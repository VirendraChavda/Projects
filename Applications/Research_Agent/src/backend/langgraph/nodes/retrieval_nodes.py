"""
Research graph nodes for retrieval, reranking, and coverage analysis.
Handles: retrieve → rerank → check coverage → [conditionally invoke MCP]
"""
from __future__ import annotations
import numpy as np
from typing import Any

from backend.models.states import ResearchState, RetrievalResult, RankedResult
from backend.services.embeddings import Embedder
from backend.services.retriever import Retriever
from backend.services.qdrant_store import QdrantStore
from backend.services.rerank import get_ranker
from backend.config import settings


# ============================================================================
# NODE 1: RETRIEVE FROM QDRANT
# ============================================================================

def retrieve_from_qdrant_node(state: ResearchState) -> ResearchState:
    """
    Retrieve candidate results from Qdrant vector database.
    Uses semantic search with embeddings.
    
    Updates:
    - retrieval_results: List of RetrievalResult from Qdrant
    """
    try:
        print(f"[retrieve_from_qdrant_node] Retrieving papers for query: '{state.user_query}'")
        
        # Initialize embedder and retriever
        embedder = Embedder()
        store = QdrantStore(dim=embedder.model.get_sentence_embedding_dimension())
        retriever = Retriever(embedder, store)
        
        # Perform semantic search
        search_results = retriever.search(state.user_query, k=state.retrieval_limit)
        
        # Convert to RetrievalResult objects
        retrieval_results = []
        for result in search_results:
            retrieval_results.append(
                RetrievalResult(
                    chunk_id=result.get("chunk_id"),
                    paper_id=result.get("paper_id"),
                    section_id=result.get("section_id"),
                    text=result.get("text"),
                    score=result.get("score", 0.0),
                    source="qdrant",
                    metadata={"retrieval_method": "semantic_search"}
                )
            )
        
        state.retrieval_results = retrieval_results
        
        # Calculate coverage score as average of top results
        if retrieval_results:
            state.coverage_score = float(np.mean([r.score for r in retrieval_results[:5]]))
        else:
            state.coverage_score = 0.0
        
        print(f"[retrieve_from_qdrant_node] Retrieved {len(retrieval_results)} results, coverage score: {state.coverage_score:.3f}")
        
        return state
        
    except Exception as e:
        state.error = f"Retrieval failed: {str(e)}"
        print(f"[retrieve_from_qdrant_node] Error: {state.error}")
        return state


# ============================================================================
# NODE 2: RERANK RESULTS
# ============================================================================

def rerank_results_node(state: ResearchState) -> ResearchState:
    """
    Rerank retrieved results using configured strategy.
    Produces ranked_results (top-k after reranking).
    
    Strategies (configurable via settings):
    - cross_encoder: Cross-encoder neural ranking (best accuracy)
    - semantic_diversity: Penalize similar results (diverse results)
    - ensemble: Combine multiple strategies (balanced approach)
    
    Updates:
    - ranked_results: Reranked top-k results
    """
    try:
        if not state.retrieval_results:
            print("[rerank_results_node] No retrieval results to rerank")
            return state
        
        rerank_strategy = settings.rerank_strategy or state.rerank_strategy
        top_k = settings.rerank_top_k or state.rerank_limit
        
        print(f"[rerank_results_node] Reranking {len(state.retrieval_results)} results using {rerank_strategy}")
        
        ranker = get_ranker()
        
        # Apply selected reranking strategy
        if rerank_strategy == "cross_encoder":
            ranked = ranker.cross_encoder_rerank(
                query=state.user_query,
                results=state.retrieval_results,
                top_k=top_k
            )
        elif rerank_strategy == "semantic_diversity":
            ranked = ranker.semantic_diversity_rerank(
                results=state.retrieval_results,
                top_k=top_k,
                diversity_weight=0.3
            )
        elif rerank_strategy == "ensemble":
            ranked = ranker.ensemble_rerank(
                query=state.user_query,
                results=state.retrieval_results,
                top_k=top_k,
                strategies=["cross_encoder", "semantic_diversity"],
                weights=[0.6, 0.4]
            )
        else:
            print(f"[rerank_results_node] Unknown strategy: {rerank_strategy}, using fallback")
            ranked = ranker._fallback_rerank(state.retrieval_results, top_k)
        
        state.ranked_results = ranked
        
        print(f"[rerank_results_node] Reranked to {len(ranked)} results")
        
        return state
        
    except Exception as e:
        state.error = f"Reranking failed: {str(e)}"
        print(f"[rerank_results_node] Error: {state.error}")
        return state


# ============================================================================
# NODE 3: CHECK COVERAGE & DECIDE ON MCP
# ============================================================================

def check_coverage_node(state: ResearchState) -> ResearchState:
    """
    Analyze coverage of ranked results and decide whether to invoke MCP.
    
    Decision logic:
    - If coverage_score >= threshold → Skip MCP
    - If coverage_score < threshold AND use_mcp → Invoke MCP
    - If MCP disabled → Skip regardless
    
    Updates:
    - should_use_mcp: Boolean decision flag
    - mcp_context: Context for MCP invocation (if needed)
    """
    try:
        print(f"[check_coverage_node] Analyzing coverage (score: {state.coverage_score:.3f}, threshold: {state.coverage_threshold:.3f})")
        
        # Default: don't use MCP
        state.should_use_mcp = False
        
        # Check conditions
        if not state.mcp_enabled:
            print("[check_coverage_node] MCP disabled, skipping")
            return state
        
        if not state.use_mcp:
            print("[check_coverage_node] MCP not requested, skipping")
            return state
        
        # Check coverage threshold
        if state.coverage_score < state.coverage_threshold:
            print(f"[check_coverage_node] Low coverage detected, enabling MCP")
            state.should_use_mcp = True
            
            # Prepare MCP context
            state.mcp_context = {
                "tool_name": "arxiv_latest",  # Default to arXiv for research queries
                "query": state.user_query,
                "result_limit": 10,
                "timeout": 30
            }
        else:
            print("[check_coverage_node] Sufficient coverage from local database")
        
        return state
        
    except Exception as e:
        state.error = f"Coverage check failed: {str(e)}"
        print(f"[check_coverage_node] Error: {state.error}")
        return state
