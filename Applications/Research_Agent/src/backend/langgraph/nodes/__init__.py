"""
LangGraph node implementations for ingestion and research workflows.
"""
from .ingestion_nodes import (
    search_arxiv_node,
    check_duplicates_node,
    ingest_pdfs_node,
    finalize_ingestion_node,
)

from .retrieval_nodes import (
    retrieve_from_qdrant_node,
    rerank_results_node,
    check_coverage_node,
)

from .analysis_nodes import (
    gap_analysis_node,
    design_suggestion_node,
    pattern_detection_node,
    future_directions_node,
    aggregate_analysis_node,
)

from .mcp_nodes import (
    invoke_mcp_node,
    merge_mcp_results_node,
)

__all__ = [
    # Ingestion nodes
    "search_arxiv_node",
    "check_duplicates_node",
    "ingest_pdfs_node",
    "finalize_ingestion_node",
    # Retrieval nodes
    "retrieve_from_qdrant_node",
    "rerank_results_node",
    "check_coverage_node",
    # Analysis nodes
    "gap_analysis_node",
    "design_suggestion_node",
    "pattern_detection_node",
    "future_directions_node",
    "aggregate_analysis_node",
    # MCP nodes
    "invoke_mcp_node",
    "merge_mcp_results_node",
]
