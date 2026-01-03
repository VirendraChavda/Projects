"""
LangGraph graph definitions for ingestion and research workflows.
Builds the complete state machine graphs.
"""
from typing import Literal
from langgraph.graph import StateGraph, END

from backend.models.states import IngestionState, IngestionStatus, ResearchState
from backend.langgraph.nodes import (
    # Ingestion nodes
    search_arxiv_node,
    check_duplicates_node,
    ingest_pdfs_node,
    finalize_ingestion_node,
    # Retrieval nodes
    retrieve_from_qdrant_node,
    rerank_results_node,
    check_coverage_node,
    # Analysis nodes
    gap_analysis_node,
    design_suggestion_node,
    pattern_detection_node,
    future_directions_node,
    aggregate_analysis_node,
    # MCP nodes
    invoke_mcp_node,
    merge_mcp_results_node,
)


# ============================================================================
# INGESTION GRAPH
# ============================================================================

def create_ingestion_graph() -> StateGraph:
    """
    Create the ingestion workflow graph.
    
    Flow:
    search_arxiv → check_duplicates → [conditional: ingest_pdfs if new docs] → finalize
    """
    graph = StateGraph(IngestionState)
    
    # Add nodes
    graph.add_node("search_arxiv", search_arxiv_node)
    graph.add_node("check_duplicates", check_duplicates_node)
    graph.add_node("ingest_pdfs", ingest_pdfs_node)
    graph.add_node("finalize", finalize_ingestion_node)
    
    # Set entry point
    graph.set_entry_point("search_arxiv")
    
    # Add edges
    graph.add_edge("search_arxiv", "check_duplicates")
    
    # Conditional edge from check_duplicates
    def should_ingest(state: IngestionState) -> str:
        if state.docs_new == 0 or state.status == IngestionStatus.COMPLETED:
            # No new docs, go directly to finalize
            return "finalize"
        else:
            # New docs found, ingest them
            return "ingest_pdfs"
    
    graph.add_conditional_edges("check_duplicates", should_ingest)
    
    # Add edges to finalize
    graph.add_edge("ingest_pdfs", "finalize")
    
    # Set exit point
    graph.add_edge("finalize", END)
    
    return graph


# ============================================================================
# RESEARCH GRAPH
# ============================================================================

def create_research_graph() -> StateGraph:
    """
    Create the research/analysis workflow graph.
    
    Flow:
    retrieve → rerank → check_coverage → 
    [conditional: invoke_mcp & merge] →
    [parallel: gap_analysis, design_suggestion, pattern_detection, future_directions] →
    aggregate → END
    """
    graph = StateGraph(ResearchState)
    
    # Add nodes
    graph.add_node("retrieve", retrieve_from_qdrant_node)
    graph.add_node("rerank", rerank_results_node)
    graph.add_node("check_coverage", check_coverage_node)
    graph.add_node("invoke_mcp", invoke_mcp_node)
    graph.add_node("merge_mcp", merge_mcp_results_node)
    graph.add_node("gap_analysis", gap_analysis_node)
    graph.add_node("design_suggestion", design_suggestion_node)
    graph.add_node("pattern_detection", pattern_detection_node)
    graph.add_node("future_directions", future_directions_node)
    graph.add_node("aggregate", aggregate_analysis_node)
    
    # Set entry point
    graph.set_entry_point("retrieve")
    
    # Add edges: linear flow
    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "check_coverage")
    
    # Conditional edge: should we use MCP?
    def should_use_mcp(state: ResearchState) -> str:
        if state.should_use_mcp:
            return "invoke_mcp"
        else:
            return "gap_analysis"
    
    graph.add_conditional_edges("check_coverage", should_use_mcp)
    
    # After MCP invocation
    graph.add_edge("invoke_mcp", "merge_mcp")
    graph.add_edge("merge_mcp", "gap_analysis")
    
    # Parallel analysis nodes (all lead to aggregate)
    graph.add_edge("gap_analysis", "aggregate")
    graph.add_edge("design_suggestion", "aggregate")
    graph.add_edge("pattern_detection", "aggregate")
    graph.add_edge("future_directions", "aggregate")
    
    # Note: We need to add all parallel analysis as edges to aggregate
    # This is done via fan-out/fan-in pattern
    # All analysis nodes should trigger, so we add them all after gap_analysis
    graph.add_edge("gap_analysis", "design_suggestion")
    graph.add_edge("design_suggestion", "pattern_detection")
    graph.add_edge("pattern_detection", "future_directions")
    graph.add_edge("future_directions", "aggregate")
    
    # Exit point
    graph.add_edge("aggregate", END)
    
    return graph


# ============================================================================
# COMPILED GRAPHS (lazy instantiation)
# ============================================================================

_ingestion_graph = None
_research_graph = None


def get_ingestion_graph():
    """Get or create the ingestion graph (singleton)"""
    global _ingestion_graph
    if _ingestion_graph is None:
        _ingestion_graph = create_ingestion_graph().compile()
    return _ingestion_graph


def get_research_graph():
    """Get or create the research graph (singleton)"""
    global _research_graph
    if _research_graph is None:
        _research_graph = create_research_graph().compile()
    return _research_graph


# For direct imports
ingestion_graph = property(lambda _: get_ingestion_graph())
research_graph = property(lambda _: get_research_graph())
