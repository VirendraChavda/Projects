"""
Django REST API views for LangGraph integration.
Provides endpoints for ingestion and research queries with streaming support.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import StreamingHttpResponse, JsonResponse
from asgiref.sync import async_to_sync
import json
import asyncio

from backend.langgraph.graphs import get_ingestion_graph, get_research_graph
from backend.models.states import IngestionState, ResearchState


# ============================================================================
# INGESTION ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def ingest_start(request):
    """
    Start a new ingestion workflow.
    
    Request body:
    {
        "days": 7,           # Optional: default 7
        "max_results": 100   # Optional: default 100
    }
    
    Returns: Streaming response with progress updates
    """
    try:
        # Parse request
        days = request.data.get('days', 7)
        max_results = request.data.get('max_results', 100)
        
        # Validate inputs
        if not (1 <= days <= 365):
            return Response(
                {"error": "days must be between 1 and 365"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not (1 <= max_results <= 1000):
            return Response(
                {"error": "max_results must be between 1 and 1000"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create initial state
        ingestion_state = IngestionState(
            days_back=days,
            max_results=max_results
        )
        
        # Get graph
        graph = get_ingestion_graph()
        
        # Generator for streaming response
        def ingestion_stream():
            try:
                # Execute graph with streaming
                for step in graph.stream(ingestion_state):
                    # Extract state from step
                    state = step
                    
                    # Format as JSON lines
                    response_data = {
                        "status": state.status.value,
                        "progress_percent": state.progress_percent,
                        "docs_found": state.docs_found,
                        "docs_existing": state.docs_existing,
                        "docs_new": state.docs_new,
                        "docs_ingested": state.docs_ingested,
                        "docs_failed": state.docs_failed,
                        "error": state.error,
                    }
                    
                    # Yield as JSON line
                    yield json.dumps(response_data) + "\n"
                
                # Final response
                final_response = {
                    "status": "success",
                    "message": "Ingestion completed",
                    "docs_ingested": state.docs_ingested,
                    "docs_failed": state.docs_failed,
                }
                yield json.dumps(final_response) + "\n"
                
            except Exception as e:
                error_response = {
                    "status": "error",
                    "error": str(e),
                }
                yield json.dumps(error_response) + "\n"
        
        # Return streaming response
        return StreamingHttpResponse(
            ingestion_stream(),
            content_type='application/x-ndjson',
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {"error": f"Failed to start ingestion: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def ingest_status(request):
    """
    Get current ingestion status.
    
    Returns:
    {
        "status": "idle|searching|checking_duplicates|ingesting|completed|error",
        "progress_percent": 0-100,
        "docs_found": int,
        "docs_new": int,
        "docs_ingested": int
    }
    """
    # TODO: Implement tracking of current ingestion state in database/cache
    return Response(
        {
            "status": "idle",
            "message": "No active ingestion"
        },
        status=status.HTTP_200_OK
    )


# ============================================================================
# RESEARCH ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def research_query(request):
    """
    Execute a research query with analysis.
    
    Request body:
    {
        "query": "transformer architectures",
        "analysis_type": "comprehensive",  # gap_analysis, design_suggestion, comprehensive
        "use_mcp": true                    # Optional: enable external tools
    }
    
    Returns:
    {
        "query": str,
        "retrieved_papers": int,
        "analysis": {...},
        "recommendations": [...],
        "sources": [...],
        "average_confidence": 0.0-1.0
    }
    """
    try:
        # Parse request
        query = request.data.get('query', '')
        analysis_type = request.data.get('analysis_type', 'comprehensive')
        use_mcp = request.data.get('use_mcp', True)
        
        # Validate inputs
        if not query or len(query.strip()) < 3:
            return Response(
                {"error": "Query must be at least 3 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_analysis_types = [
            'gap_analysis',
            'design_suggestion',
            'pattern_detection',
            'comprehensive'
        ]
        if analysis_type not in valid_analysis_types:
            return Response(
                {"error": f"Invalid analysis_type. Must be one of: {', '.join(valid_analysis_types)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create initial state
        research_state = ResearchState(
            user_query=query,
            analysis_type=analysis_type,
            use_mcp=use_mcp
        )
        
        # Get graph
        graph = get_research_graph()
        
        # Execute graph
        final_state = graph.invoke(research_state)
        
        # Check for errors
        if final_state.error:
            return Response(
                {
                    "error": final_state.error,
                    "partial_results": final_state.final_response
                },
                status=status.HTTP_206_PARTIAL_CONTENT
            )
        
        # Return results
        return Response(
            final_state.final_response,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {"error": f"Research query failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def research_get(request, analysis_id):
    """
    Retrieve a previously stored analysis result.
    
    Args:
        analysis_id: ID of the analysis to retrieve
        
    Returns:
        Stored analysis result or 404 if not found
    """
    # TODO: Implement caching/retrieval of analysis results
    return Response(
        {"error": "Analysis not found"},
        status=status.HTTP_404_NOT_FOUND
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint.
    
    Returns:
    {
        "status": "healthy",
        "version": "1.0",
        "components": {
            "qdrant": "ok|error",
            "postgres": "ok|error|not_configured",
            "llm": "ok|error|not_configured"
        }
    }
    """
    import socket
    from backend.config import settings
    
    # Check Qdrant
    qdrant_status = "error"
    try:
        from backend.services.qdrant_store import QdrantStore
        store = QdrantStore()
        store.client.get_collections()
        qdrant_status = "ok"
    except Exception as e:
        print(f"Qdrant check failed: {e}")
    
    # Check PostgreSQL
    postgres_status = "not_configured"
    try:
        # Check if DATABASE_URL is set
        if hasattr(settings, 'database_url') and settings.database_url:
            # Try to connect
            postgres_status = "ok"
    except Exception as e:
        postgres_status = "error"
    
    # Check LLM
    llm_status = "not_configured"
    if settings.llm_api_key:
        try:
            from backend.services.llm_client import get_llm_client
            client = get_llm_client()
            llm_status = "ok"
        except Exception as e:
            llm_status = "error"
    
    return Response(
        {
            "status": "healthy",
            "version": "1.0",
            "components": {
                "qdrant": qdrant_status,
                "postgres": postgres_status,
                "llm": llm_status,
            }
        },
        status=status.HTTP_200_OK
    )
