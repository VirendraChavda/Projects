from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Iterable, Dict, Any
import arxiv
from tqdm import tqdm
from backend.config import settings

AI_CATEGORIES = set(settings.arxiv_categories)

def _ensure_dirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def search_arxiv_recent(max_results: int | None = None, days_back: int | None = None) -> list[Dict[str, Any]]:
    """
    Query arXiv for recent papers in AI-engineering categories.
    Returns a list of metadata dicts with local PDF file path filled after download().
    """
    max_results = max_results or settings.arxiv_max_results
    days_back = days_back or settings.arxiv_days_back

    date_from = (datetime.now(timezone.utc) - timedelta(days=days_back)).date().isoformat()
    cats_query = " OR ".join([f"cat:{c}" for c in AI_CATEGORIES])
    query = f"({cats_query}) AND submittedDate:[{date_from}0000 TO *]"

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    results = []
    for r in search.results():
        # basic metadata
        md = {
            "source": "arxiv",
            "arxiv_id": r.entry_id.split("/")[-1],
            "title": r.title,
            "authors": [a.name for a in r.authors],
            "summary": r.summary,
            "published": r.published,
            "updated": r.updated,
            "primary_category": r.primary_category,
            "categories": list(r.categories),
            "pdf_url": r.pdf_url,
            "year": r.published.year if r.published else None,
            "venue": "arXiv",
            "license": "arXiv",
        }
        results.append(md)
    return results

def download_pdfs(items: Iterable[Dict[str, Any]], out_dir: str) -> list[Dict[str, Any]]:
    _ensure_dirs(out_dir)
    out = []
    for it in tqdm(list(items), desc="Downloading PDFs"):
        pdf_url = it.get("pdf_url")
        if not pdf_url:
            continue
        fname = f"{it['arxiv_id'].replace('/', '_')}.pdf"
        local_path = os.path.join(out_dir, fname)
        try:
            # arxiv library can download directly
            paper = next(arxiv.Search(id_list=[it["arxiv_id"]]).results())
            paper.download_pdf(filename=local_path)
            it["pdf_path"] = local_path
            out.append(it)
        except Exception as e:
            print(f"[warn] failed to download {pdf_url}: {e}")
    return out
