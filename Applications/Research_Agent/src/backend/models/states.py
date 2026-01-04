"""
Pydantic state models for LangGraph workflows.
Defines all state structures with validation for ingestion and research graphs.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# ENUMS
# ============================================================================

class IngestionStatus(str, Enum):
    """Status of ingestion workflow"""
    IDLE = "idle"
    SEARCHING = "searching"
    CHECKING_DUPLICATES = "checking_duplicates"
    INGESTING = "ingesting"
    COMPLETED = "completed"
    ERROR = "error"


# ============================================================================
# INGESTION STATE MODELS
# ============================================================================

class IngestionState(BaseModel):
    """
    State for the ingestion workflow.
    Tracks the entire lifecycle of downloading and processing papers.
    """
    # Input parameters
    days_back: int = Field(default=7, ge=1, le=365, description="Days back to search")
    max_results: int = Field(default=100, ge=1, le=1000, description="Max papers to retrieve")
    
    # Progress tracking
    status: IngestionStatus = Field(default=IngestionStatus.IDLE, description="Current workflow status")
    docs_found: int = Field(default=0, ge=0, description="Total docs found in arXiv")
    docs_existing: int = Field(default=0, ge=0, description="Docs already in database")
    docs_new: int = Field(default=0, ge=0, description="New docs to ingest")
    docs_ingested: int = Field(default=0, ge=0, description="Successfully ingested count")
    docs_failed: int = Field(default=0, ge=0, description="Failed ingestion count")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress 0-100%")
    
    # Results
    arxiv_results: List[Dict[str, Any]] = Field(default_factory=list, description="Raw arXiv search results")
    processed_pdfs: List[str] = Field(default_factory=list, description="Successfully processed PDF paths")
    failed_pdfs: List[tuple[str, str]] = Field(default_factory=list, description="Failed PDF paths and error messages")
    
    # Metadata
    started_at: Optional[datetime] = Field(default=None, description="When ingestion started")
    completed_at: Optional[datetime] = Field(default=None, description="When ingestion completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    class Config:
        use_enum_values = False


# ============================================================================
# RETRIEVAL & RANKING STATE MODELS
# ============================================================================

class RetrievalResult(BaseModel):
    """Single retrieved chunk with metadata"""
    chunk_id: str = Field(description="Unique chunk identifier")
    paper_id: str = Field(description="Paper/document ID")
    section_id: str = Field(description="Section identifier in paper")
    text: str = Field(description="Actual text content")
    score: float = Field(ge=0.0, le=1.0, description="Retrieval confidence score")
    source: str = Field(default="qdrant", description="Source of result (qdrant, mcp, etc)")
    page_from: Optional[int] = Field(default=None, description="Starting page number")
    page_to: Optional[int] = Field(default=None, description="Ending page number")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class RankedResult(BaseModel):
    """Result after reranking with combined scores"""
    chunk_id: str = Field(description="Unique chunk identifier")
    paper_id: str = Field(description="Paper ID")
    section_id: str = Field(description="Section ID")
    text: str = Field(description="Text content")
    primary_score: float = Field(ge=0.0, le=1.0, description="Original retrieval score")
    rerank_score: float = Field(ge=0.0, le=1.0, description="Reranking score")
    combined_score: float = Field(ge=0.0, le=1.0, description="Final combined score")
    rank: int = Field(ge=1, description="Final rank position")
    source: str = Field(default="qdrant", description="Data source")


# ============================================================================
# MCP INTEGRATION MODELS
# ============================================================================

class MCPContext(BaseModel):
    """Context for invoking MCP tools"""
    tool_name: str = Field(description="Name of MCP tool to invoke")
    query: str = Field(description="Query string for external search")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filter criteria")
    result_limit: int = Field(default=10, ge=1, le=100, description="Max external results")
    timeout: int = Field(default=30, ge=5, le=300, description="Tool timeout in seconds")


class MCPToolResult(BaseModel):
    """Result from MCP tool invocation"""
    tool_name: str = Field(description="Which MCP tool was invoked")
    success: bool = Field(description="Whether tool executed successfully")
    results: List[RetrievalResult] = Field(default_factory=list, description="Retrieved results")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: float = Field(default=0.0, description="Execution time in seconds")


# ============================================================================
# ANALYSIS RESULT MODELS
# ============================================================================

class GapAnalysis(BaseModel):
    """Results of gap analysis"""
    identified_gaps: List[str] = Field(default_factory=list, description="Research gaps found")
    research_areas: List[str] = Field(default_factory=list, description="Areas lacking coverage")
    missing_benchmarks: List[str] = Field(default_factory=list, description="Missing evaluation benchmarks")
    underexplored_topics: List[str] = Field(default_factory=list, description="Underexplored topics")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Analysis confidence")
    faithfulness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="How faithful to sources")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source references supporting analysis")


class DesignSuggestion(BaseModel):
    """Results of design suggestion analysis"""
    suggested_approaches: List[str] = Field(default_factory=list, description="Suggested approaches")
    architectural_improvements: List[str] = Field(default_factory=list, description="Architecture improvements")
    implementation_strategies: List[str] = Field(default_factory=list, description="Implementation strategies")
    trade_offs: List[str] = Field(default_factory=list, description="Design trade-offs to consider")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Suggestion confidence")
    faithfulness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="How faithful to sources")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source references supporting suggestions")


class PatternDetection(BaseModel):
    """Results of pattern detection analysis"""
    patterns_found: List[str] = Field(default_factory=list, description="Detected patterns")
    trend_analysis: List[str] = Field(default_factory=list, description="Trend observations")
    emerging_methods: List[str] = Field(default_factory=list, description="Emerging methodologies")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Pattern confidence")
    faithfulness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="How faithful to sources")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source references supporting patterns")


class FutureDirections(BaseModel):
    """Results of future directions analysis"""
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    open_questions: List[str] = Field(default_factory=list, description="Open research questions")
    future_applications: List[str] = Field(default_factory=list, description="Potential applications")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Prediction confidence")
    faithfulness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="How faithful to sources")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source references supporting predictions")


# ============================================================================
# RESEARCH STATE MODEL
# ============================================================================

class ResearchState(BaseModel):
    """
    State for the research/analysis workflow.
    Handles user queries through retrieval, ranking, and analysis.
    """
    # Input
    user_query: str = Field(description="User's research query")
    analysis_type: str = Field(
        default="comprehensive",
        description="Type of analysis: gap_analysis, design_suggestion, pattern_detection, future_directions, comprehensive"
    )
    
    # Retrieval stage
    retrieval_results: List[RetrievalResult] = Field(default_factory=list, description="Raw retrieval results")
    retrieval_limit: int = Field(default=50, ge=10, le=100, description="Max retrieval results")
    
    # Reranking stage
    ranked_results: List[RankedResult] = Field(default_factory=list, description="Reranked results")
    rerank_strategy: str = Field(
        default="ensemble",
        description="Reranking strategy: cross_encoder, semantic_diversity, ensemble"
    )
    rerank_limit: int = Field(default=20, ge=5, le=50, description="Top-k after reranking")
    
    # MCP stage
    use_mcp: bool = Field(default=True, description="Whether to use MCP tools")
    mcp_enabled: bool = Field(default=True, description="Whether MCP is available")
    mcp_context: Optional[MCPContext] = Field(default=None, description="MCP tool context")
    mcp_results: List[RetrievalResult] = Field(default_factory=list, description="Results from MCP tools")
    mcp_tool_result: Optional[MCPToolResult] = Field(default=None, description="MCP execution result")
    should_use_mcp: bool = Field(default=False, description="Decision: invoke MCP?")
    
    # Coverage check
    coverage_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence threshold for MCP invocation")
    coverage_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Coverage confidence score")
    
    # Analysis stage
    gap_analysis: Optional[GapAnalysis] = Field(default=None, description="Gap analysis results")
    design_suggestions: Optional[DesignSuggestion] = Field(default=None, description="Design suggestion results")
    pattern_detection: Optional[PatternDetection] = Field(default=None, description="Pattern detection results")
    future_directions: Optional[FutureDirections] = Field(default=None, description="Future directions results")
    
    # Output
    final_response: Optional[Dict[str, Any]] = Field(default=None, description="Final aggregated response")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="When state was created")
    completed_at: Optional[datetime] = Field(default=None, description="When analysis completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        use_enum_values = False


# ============================================================================
# FINAL RESPONSE MODEL
# ============================================================================

class FinalAnalysisResponse(BaseModel):
    """
    Final aggregated response sent to Django frontend.
    Combines all analysis results with metadata.
    """
    query: str = Field(description="Original user query")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    retrieved_papers: int = Field(ge=0, description="Number of papers retrieved")
    ranked_results_count: int = Field(ge=0, description="Number of ranked results")
    used_mcp: bool = Field(description="Whether MCP tools were invoked")
    
    # Analysis results
    analysis: Dict[str, Any] = Field(default_factory=dict, description="Analysis results by type")
    recommendations: List[str] = Field(default_factory=list, description="Key recommendations")
    sources: List[str] = Field(default_factory=list, description="Source paper IDs/URLs")
    
    # Quality metrics
    average_confidence: float = Field(ge=0.0, le=1.0, description="Average confidence score")
    execution_time: float = Field(ge=0.0, description="Total execution time in seconds")
    
    # Metadata
    model_version: str = Field(default="1.0", description="Analysis model version")
    error: Optional[str] = Field(default=None, description="Error message if any")
