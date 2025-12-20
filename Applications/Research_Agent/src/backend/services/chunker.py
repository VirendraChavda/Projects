from __future__ import annotations
from typing import List, Dict
import re

_WS = re.compile(r"\s+")

def _simple_tokenize(text: str) -> list[str]:
    return _WS.split(text.strip())

def chunk_section(paper_id: str, section_id: str, text: str, target_tokens: int, overlap_tokens: int,
                  page_from: int | None, page_to: int | None) -> list[dict]:
    toks = _simple_tokenize(text)
    chunks: list[dict] = []
    if not toks:
        return chunks
    start = 0
    order = 0
    while start < len(toks):
        end = min(start + target_tokens, len(toks))
        piece = " ".join(toks[start:end]).strip()
        chunk_id = f"{paper_id}:{section_id}:{order}"
        chunks.append({
            "paper_id": paper_id,
            "section_id": section_id,
            "chunk_id": chunk_id,
            "text": piece,
            "order": order,
            "page_from": page_from,
            "page_to": page_to,
        })
        if end == len(toks):
            break
        start = max(0, end - overlap_tokens)
        order += 1
    return chunks
