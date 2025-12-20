from __future__ import annotations
import re
import fitz  # PyMuPDF
from typing import List, Dict, Any

REFS_PAT = re.compile(r"^\s*references\s*$", re.IGNORECASE)

def pdf_to_sections(pdf_path: str) -> list[dict]:
    """
    Very simple PDF -> sections:
    - Extract page text blocks
    - Split into paragraphs (double newlines)
    - Stop at 'References'
    - Group paragraphs into coarse sections by naive headings
    """
    doc = fitz.open(pdf_path)
    paras: list[tuple[int, str]] = []  # (page, text)
    for p in range(len(doc)):
        txt = doc[p].get_text("text")
        if not txt:
            continue
        # normalize hard breaks; keep paragraph blocks
        chunks = [b.strip() for b in txt.split("\n\n") if b.strip()]
        for c in chunks:
            paras.append((p + 1, c))

    # truncate at References
    cut_idx = None
    for i, (_, t) in enumerate(paras):
        if REFS_PAT.match(t.strip()):
            cut_idx = i
            break
    if cut_idx is not None:
        paras = paras[:cut_idx]

    # naive heading heuristic: lines with few words and Title Case/ALL CAPS
    sections: list[dict] = []
    current = {"title": "Main", "paras": [], "page_from": 1, "page_to": 1}
    for page, para in paras:
        line0 = para.splitlines()[0]
        words = len(line0.split())
        is_heading = words <= 8 and (line0.isupper() or line0.istitle())
        if is_heading and current["paras"]:
            # flush old
            sec_text = "\n\n".join(current["paras"]).strip()
            sections.append({
                "title": current["title"],
                "text": sec_text,
                "page_from": current["page_from"],
                "page_to": current["page_to"],
            })
            # start new
            current = {"title": line0.strip(), "paras": [], "page_from": page, "page_to": page}
        else:
            current["paras"].append(para)
            current["page_to"] = page

    # flush last
    if current["paras"]:
        sections.append({
            "title": current["title"],
            "text": "\n\n".join(current["paras"]).strip(),
            "page_from": current["page_from"],
            "page_to": current["page_to"],
        })
    return sections
