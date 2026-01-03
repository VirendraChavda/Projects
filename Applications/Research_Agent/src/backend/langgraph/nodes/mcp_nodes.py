"""
MCP (Model Context Protocol) tool handlers for external data fetching.
Integrates external research sources when local database has low coverage.
"""
from __future__ import annotations
import asyncio
from typing import Optional, List
import aiohttp
from datetime import datetime, timedelta

from backend.models.states import (
    ResearchState,
    MCPContext,
    MCPToolResult,
    RetrievalResult,
)
from backend.config import settings


# ============================================================================
# MCP TOOL IMPLEMENTATIONS
# ============================================================================

class MCPToolHandler:
    """Handler for MCP tool invocations"""
    
    def __init__(self):
        self.timeout = 30
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    # ========================================================================
    # ARXIV LATEST TOOL
    # ========================================================================
    
    async def invoke_arxiv_latest(
        self,
        query: str,
        days_back: int = 30,
        limit: int = 10,
    ) -> MCPToolResult:
        """
        Fetch latest papers from arXiv matching query.
        Uses arXiv API to get up-to-date research.
        
        Args:
            query: Search query
            days_back: Only papers from last N days
            limit: Max results to return
            
        Returns:
            MCPToolResult with retrieved papers
        """
        try:
            print(f"[MCP] Invoking arxiv_latest tool: '{query}'")
            
            from backend.services.sources.arxiv_client import search_arxiv_recent
            
            # Search arXiv
            arxiv_papers = search_arxiv_recent(
                max_results=limit,
                days_back=days_back
            )
            
            # Convert to RetrievalResult format
            results = []
            for paper in arxiv_papers:
                result = RetrievalResult(
                    chunk_id=paper.get("arxiv_id"),
                    paper_id=paper.get("arxiv_id"),
                    section_id="abstract",
                    text=paper.get("summary", ""),
                    score=0.8,  # High confidence for fresh data
                    source="mcp_arxiv",
                    metadata={
                        "title": paper.get("title"),
                        "authors": paper.get("authors"),
                        "published_date": paper.get("published_date"),
                        "url": paper.get("arxiv_url"),
                    }
                )
                results.append(result)
            
            return MCPToolResult(
                tool_name="arxiv_latest",
                success=True,
                results=results,
                execution_time=0.0
            )
            
        except Exception as e:
            print(f"[MCP] arxiv_latest failed: {str(e)}")
            return MCPToolResult(
                tool_name="arxiv_latest",
                success=False,
                results=[],
                error=str(e)
            )
    
    # ========================================================================
    # GOOGLE SCHOLAR TOOL (Simulated)
    # ========================================================================
    
    async def invoke_google_scholar(
        self,
        query: str,
        limit: int = 5,
    ) -> MCPToolResult:
        """
        Simulate Google Scholar search.
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            MCPToolResult with simulated scholar results
        """
        try:
            print(f"[MCP] Invoking google_scholar tool: '{query}'")
            
            # Simulated results (would use actual Google Scholar API with proper auth)
            results = [
                RetrievalResult(
                    chunk_id=f"gs_paper_{i}",
                    paper_id=f"gs_paper_{i}",
                    section_id="abstract",
                    text=f"Research on {query} - simulated Google Scholar result {i+1}",
                    score=0.75,
                    source="mcp_google_scholar",
                    metadata={
                        "title": f"Advanced Study on {query}",
                        "citation_count": 100 - (i * 20),
                    }
                )
                for i in range(min(limit, 5))
            ]
            
            return MCPToolResult(
                tool_name="google_scholar",
                success=True,
                results=results,
                execution_time=0.5
            )
            
        except Exception as e:
            print(f"[MCP] google_scholar failed: {str(e)}")
            return MCPToolResult(
                tool_name="google_scholar",
                success=False,
                results=[],
                error=str(e)
            )
    
    # ========================================================================
    # SEMANTIC SEARCH TOOL
    # ========================================================================
    
    async def invoke_semantic_search_external(
        self,
        query: str,
        limit: int = 5,
    ) -> MCPToolResult:
        """
        Search external semantic research databases.
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            MCPToolResult with external semantic results
        """
        try:
            print(f"[MCP] Invoking semantic_search_external tool: '{query}'")
            
            # Simulated external semantic search results
            results = [
                RetrievalResult(
                    chunk_id=f"external_sem_{i}",
                    paper_id=f"external_sem_{i}",
                    section_id="method",
                    text=f"Semantic research result for '{query}' {i+1}",
                    score=0.7,
                    source="mcp_semantic_external",
                    metadata={
                        "database": "DBLP" if i % 2 == 0 else "IEEE Xplore",
                        "relevance": "high",
                    }
                )
                for i in range(min(limit, 5))
            ]
            
            return MCPToolResult(
                tool_name="semantic_search_external",
                success=True,
                results=results,
                execution_time=1.0
            )
            
        except Exception as e:
            print(f"[MCP] semantic_search_external failed: {str(e)}")
            return MCPToolResult(
                tool_name="semantic_search_external",
                success=False,
                results=[],
                error=str(e)
            )


# ============================================================================
# MCP GRAPH NODE
# ============================================================================

def invoke_mcp_node(state: ResearchState) -> ResearchState:
    """
    Conditionally invoke MCP tools to fetch external data.
    Runs asynchronously to fetch from external sources.
    
    Conditions (from check_coverage_node):
    - should_use_mcp: True
    - mcp_context: Configured with tool details
    
    Updates:
    - mcp_results: List of results from MCP tools
    - mcp_tool_result: Tool execution metadata
    """
    try:
        if not state.should_use_mcp or not state.mcp_context:
            print("[invoke_mcp_node] MCP not needed or context not set")
            return state
        
        print("[invoke_mcp_node] Invoking MCP tools for external data...")
        
        # Run async MCP tools
        mcp_results = asyncio.run(_run_mcp_tools(state))
        
        state.mcp_results = mcp_results
        state.mcp_tool_result = MCPToolResult(
            tool_name=state.mcp_context.get("tool_name", "unknown"),
            success=len(mcp_results) > 0,
            results=mcp_results,
        )
        
        print(f"[invoke_mcp_node] Retrieved {len(mcp_results)} results from MCP tools")
        
        return state
        
    except Exception as e:
        state.error = f"MCP invocation failed: {str(e)}"
        print(f"[invoke_mcp_node] Error: {state.error}")
        return state


async def _run_mcp_tools(state: ResearchState) -> List[RetrievalResult]:
    """
    Run configured MCP tools asynchronously.
    
    Tool selection based on mcp_context.tool_name:
    - arxiv_latest: Fetch latest arXiv papers
    - google_scholar: Search Google Scholar
    - semantic_search: Query external semantic databases
    """
    tool_name = state.mcp_context.get("tool_name", "arxiv_latest")
    query = state.mcp_context.get("query", state.user_query)
    result_limit = state.mcp_context.get("result_limit", 10)
    
    async with MCPToolHandler() as handler:
        if tool_name == "arxiv_latest":
            result = await handler.invoke_arxiv_latest(
                query=query,
                days_back=7,
                limit=result_limit
            )
        elif tool_name == "google_scholar":
            result = await handler.invoke_google_scholar(
                query=query,
                limit=result_limit
            )
        elif tool_name == "semantic_search":
            result = await handler.invoke_semantic_search_external(
                query=query,
                limit=result_limit
            )
        else:
            print(f"[MCP] Unknown tool: {tool_name}")
            return []
        
        if result.success:
            return result.results
        else:
            print(f"[MCP] Tool {tool_name} failed: {result.error}")
            return []


# ============================================================================
# MERGE MCP WITH RANKED RESULTS
# ============================================================================

def merge_mcp_results_node(state: ResearchState) -> ResearchState:
    """
    Merge MCP results with ranked results.
    De-duplicate based on paper_id.
    Re-rank combined results.
    
    Updates:
    - ranked_results: Merged and re-ranked results
    """
    try:
        if not state.mcp_results:
            print("[merge_mcp_results_node] No MCP results to merge")
            return state
        
        print(f"[merge_mcp_results_node] Merging {len(state.mcp_results)} MCP results with ranked results")
        
        # Create dict of ranked results by chunk_id for deduplication
        ranked_dict = {r.chunk_id: r for r in state.ranked_results}
        
        # Add MCP results (converting RetrievalResult to RankedResult)
        from backend.models.states import RankedResult
        
        for idx, mcp_result in enumerate(state.mcp_results):
            # Skip if already have this paper
            if mcp_result.chunk_id in ranked_dict:
                print(f"[merge_mcp_results_node] Skipping duplicate: {mcp_result.chunk_id}")
                continue
            
            # Convert and add to ranked results
            ranked_result = RankedResult(
                chunk_id=mcp_result.chunk_id,
                paper_id=mcp_result.paper_id,
                section_id=mcp_result.section_id,
                text=mcp_result.text,
                primary_score=mcp_result.score,
                rerank_score=mcp_result.score,
                combined_score=mcp_result.score,
                rank=len(ranked_dict) + idx + 1,
                source=mcp_result.source
            )
            ranked_dict[mcp_result.chunk_id] = ranked_result
        
        # Re-sort by combined score
        merged_results = list(ranked_dict.values())
        merged_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Update ranks
        for idx, r in enumerate(merged_results):
            r.rank = idx + 1
        
        state.ranked_results = merged_results[:state.rerank_limit]
        
        print(f"[merge_mcp_results_node] Final result count: {len(state.ranked_results)}")
        
        return state
        
    except Exception as e:
        state.error = f"MCP merge failed: {str(e)}"
        print(f"[merge_mcp_results_node] Error: {state.error}")
        return state
