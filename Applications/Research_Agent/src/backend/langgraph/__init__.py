"""
LangGraph state schema definitions.
"""
from typing import Annotated
from langgraph.graph.message import MessagesState
from backend.models.states import IngestionState, ResearchState


class IngestionWorkflowState(MessagesState):
    """State for ingestion workflow"""
    ingestion_state: IngestionState


class ResearchWorkflowState(MessagesState):
    """State for research/analysis workflow"""
    research_state: ResearchState
