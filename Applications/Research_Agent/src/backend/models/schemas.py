from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

class Chunk(BaseModel):
    paper_id: str
    section_id: str
    chunk_id: str
    text: str
    order: int
    page_from: int | None = None
    page_to: int | None = None
    year: Optional[int] = None
    venue: Optional[str] = None
    tier: str = "core"

class SearchHit(BaseModel):
    chunk_id: str
    paper_id: str
    section_id: str
    text: str
    score: float