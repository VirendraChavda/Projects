from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Iterable, Dict, Any
from tqdm import tqdm
from backend.config import settings

import time
import random
import arxiv
from arxiv import HTTPError

AI_CATEGORIES = set(settings.arxiv_categories)

def _ensure_dirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _iter_search_with_backoff(search: arxiv.Search, max_retries: int = 6):
    """Yield results from arxiv.Search.results() with retry/backoff on transient errors (429/5xx)."""
    attempt = 0
    while True:
        try:
            for r in search.results():
                yield r
            return
        except HTTPError as err:
            status = getattr(err, "status_code", None)
            # treat 429 and 5xx as retryable transient errors
            retryable = status == 429 or (status is not None and 500 <= status < 600) or "429" in str(err) or "503" in str(err)
            if not retryable:
                raise
            attempt += 1
            if attempt > max_retries:
                raise
            backoff = min(60, (2 ** attempt) + random.random())
            print(f"[warn] arXiv transient ({status}). backing off {backoff:.1f}s (attempt {attempt}/{max_retries})")
            time.sleep(backoff)
            # recreate the Search object to reset generator/internal state
            try:
                search = arxiv.Search(
                    query=getattr(search, "query", None),
                    id_list=getattr(search, "id_list", None),
                    max_results=getattr(search, "max_results", None),
                    sort_by=getattr(search, "sort_by", None),
                    sort_order=getattr(search, "sort_order", None),
                )
            except Exception:
                # if recreation fails, continue with the existing object
                pass
            continue

def search_arxiv_recent(max_results: int | None = None, days_back: int | None = None) -> list[Dict[str, Any]]:
    """
    Query arXiv for recent papers in AI-engineering categories.
    Returns a list of metadata dicts with local PDF file path filled after download().
    """
    max_results = int(max_results or settings.arxiv_max_results or 100)
    days_back = int(days_back or settings.arxiv_days_back or 30)

    date_from = (datetime.now(timezone.utc) - timedelta(days=days_back)).date().isoformat()
    cats_query = " OR ".join([f"cat:{c}" for c in AI_CATEGORIES])
    query = f"({cats_query}) AND submittedDate:[{date_from}0000 TO *]"

    results: list[Dict[str, Any]] = []

    # Create a single Search request (some arxiv versions don't accept a 'start' arg)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    try:
        for r in _iter_search_with_backoff(search):
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
            if len(results) >= max_results:
                break
    except Exception as e:
        print(f"[error] arXiv search failed after retries: {e}")

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
            # polite pause to avoid too many quick requests for PDFs
            time.sleep(0.5 + random.random() * 0.5)
        except Exception as e:
            print(f"[warn] failed to download {pdf_url}: {e}")
    return out
