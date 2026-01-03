"""
Ingestion graph nodes for downloading and processing papers.
Handles: search arXiv → check duplicates → ingest PDFs → finalize
"""
from __future__ import annotations
import os
import hashlib
import re
from datetime import datetime
from typing import Any
from tqdm import tqdm

from backend.config import settings
from backend.models.states import IngestionState, IngestionStatus
from backend.services.sources.arxiv_client import search_arxiv_recent, download_pdfs
from backend.services.pdf_parse import pdf_to_sections
from backend.services.chunker import chunk_section
from backend.services.embeddings import Embedder
from backend.services.qdrant_store import QdrantStore
from backend.stores.postgres_repo import PostgresRepository


# ============================================================================
# NODE 1: SEARCH ARXIV
# ============================================================================

def search_arxiv_node(state: IngestionState) -> IngestionState:
    """
    Search arXiv for recent papers based on days_back and max_results.
    
    Updates:
    - status: SEARCHING
    - arxiv_results: List of search results
    - docs_found: Count of papers found
    """
    try:
        state.status = IngestionStatus.SEARCHING
        state.started_at = datetime.now()
        
        print(f"[search_arxiv_node] Searching arXiv for papers from last {state.days_back} days...")
        
        # Call arxiv service
        arxiv_results = search_arxiv_recent(
            max_results=state.max_results,
            days_back=state.days_back
        )
        
        state.arxiv_results = arxiv_results
        state.docs_found = len(arxiv_results)
        state.progress_percent = 25.0
        
        print(f"[search_arxiv_node] Found {state.docs_found} papers")
        
        return state
        
    except Exception as e:
        state.status = IngestionStatus.ERROR
        state.error = f"ArXiv search failed: {str(e)}"
        print(f"[search_arxiv_node] Error: {state.error}")
        return state


# ============================================================================
# NODE 2: CHECK DUPLICATES
# ============================================================================

def _title_fingerprint(title: str) -> str:
    """Create normalized title fingerprint for duplicate detection"""
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    stops = {"the", "a", "an", "of", "and", "for", "on", "in", "to", "with"}
    toks = [w for w in t.split() if w not in stops]
    return " ".join(toks)


def check_duplicates_node(state: IngestionState) -> IngestionState:
    """
    Check which papers are already in the database.
    Separate into: docs_existing (skip) and docs_new (process).
    
    Updates:
    - status: CHECKING_DUPLICATES
    - docs_existing: Count of papers already in DB
    - docs_new: Count of new papers to ingest
    - arxiv_results: Filtered to only new papers
    """
    try:
        state.status = IngestionStatus.CHECKING_DUPLICATES
        state.progress_percent = 40.0
        
        print("[check_duplicates_node] Checking for duplicate papers...")
        
        # Initialize repo to check existing papers
        repo = PostgresRepository()
        
        # Fingerprint existing papers for comparison
        existing_fingerprints = set(repo.get_all_paper_fingerprints())
        existing_arxiv_ids = set(repo.get_all_arxiv_ids())
        
        new_results = []
        existing_count = 0
        
        for result in state.arxiv_results:
            arxiv_id = result.get("arxiv_id")
            title = result.get("title", "")
            
            # Check both arxiv_id and title fingerprint
            if arxiv_id in existing_arxiv_ids:
                existing_count += 1
                print(f"[check_duplicates_node] Skipping existing paper: {arxiv_id}")
                continue
                
            fingerprint = _title_fingerprint(title)
            if fingerprint in existing_fingerprints:
                existing_count += 1
                print(f"[check_duplicates_node] Skipping duplicate: {title}")
                continue
            
            new_results.append(result)
        
        state.docs_existing = existing_count
        state.docs_new = len(new_results)
        state.arxiv_results = new_results
        
        print(f"[check_duplicates_node] Found {state.docs_existing} existing, {state.docs_new} new papers")
        
        # If no new papers, skip ingestion
        if state.docs_new == 0:
            state.status = IngestionStatus.COMPLETED
            state.completed_at = datetime.now()
            state.progress_percent = 100.0
            print("[check_duplicates_node] No new papers to ingest")
        
        return state
        
    except Exception as e:
        state.status = IngestionStatus.ERROR
        state.error = f"Duplicate check failed: {str(e)}"
        print(f"[check_duplicates_node] Error: {state.error}")
        return state


# ============================================================================
# NODE 3: INGEST PDFS
# ============================================================================

def _ingest_single_pdf(
    embedder: Embedder,
    store: QdrantStore,
    repo: PostgresRepository,
    pdf_path: str,
    metadata: dict | None = None
) -> tuple[int, str | None]:
    """
    Ingest a single PDF: parse → chunk → embed → store.
    Returns (chunks_ingested, error_if_any)
    """
    try:
        metadata = metadata or {}
        paper_id = metadata.get("arxiv_id") or os.path.splitext(os.path.basename(pdf_path))[0]
        
        # Parse PDF into sections
        sections = pdf_to_sections(pdf_path)
        if not sections:
            return 0, f"No sections extracted from {pdf_path}"
        
        all_chunks = []
        
        # Chunk each section
        for idx, sec in enumerate(sections):
            section_id = f"{paper_id}:sec{idx}"
            chunks = chunk_section(
                paper_id=paper_id,
                section_id=section_id,
                text=sec["text"],
                target_tokens=settings.chunk_tokens,
                overlap_tokens=settings.chunk_overlap,
                page_from=sec.get("page_from"),
                page_to=sec.get("page_to"),
            )
            all_chunks.extend(chunks)
        
        if not all_chunks:
            return 0, f"No chunks produced for {pdf_path}"
        
        # Generate embeddings
        texts = [c["text"] for c in all_chunks]
        vecs = embedder.encode(texts)
        
        # Upsert to Qdrant
        n_upserted = store.upsert(all_chunks, vecs)
        
        # Store metadata in PostgreSQL
        repo.insert_paper(
            arxiv_id=paper_id,
            title=metadata.get("title", ""),
            authors=",".join(metadata.get("authors", [])),
            published_date=metadata.get("published_date"),
            pdf_path=pdf_path,
            fingerprint=_title_fingerprint(metadata.get("title", "")),
            chunks_count=n_upserted
        )
        
        return n_upserted, None
        
    except Exception as e:
        return 0, f"Failed to ingest {pdf_path}: {str(e)}"


def ingest_pdfs_node(state: IngestionState) -> IngestionState:
    """
    Download and ingest new papers.
    - Download PDFs from arxiv_results
    - Parse, chunk, embed
    - Upsert to Qdrant
    - Store metadata in PostgreSQL
    
    Updates:
    - status: INGESTING
    - docs_ingested: Successfully ingested count
    - docs_failed: Failed count
    - processed_pdfs: List of processed paths
    - failed_pdfs: List of (path, error) tuples
    - progress_percent: 40-90%
    """
    try:
        # Skip if no new docs
        if state.docs_new == 0:
            state.status = IngestionStatus.COMPLETED
            state.completed_at = datetime.now()
            state.progress_percent = 100.0
            return state
        
        state.status = IngestionStatus.INGESTING
        
        print(f"[ingest_pdfs_node] Downloading {state.docs_new} PDFs...")
        
        # Download PDFs
        items = download_pdfs(state.arxiv_results, settings.data_raw)
        
        print(f"[ingest_pdfs_node] Downloaded {len(items)} PDFs, starting ingestion...")
        
        # Initialize embedder and store
        embedder = Embedder()
        store = QdrantStore(dim=embedder.model.get_sentence_embedding_dimension())
        repo = PostgresRepository()
        
        ingested = 0
        failed = 0
        
        # Ingest each PDF with progress
        for idx, item in enumerate(tqdm(items, desc="Ingesting PDFs")):
            pdf_path = item.get("pdf_path")
            if not pdf_path or not os.path.exists(pdf_path):
                failed += 1
                state.failed_pdfs.append((pdf_path or "unknown", "File not found"))
                continue
            
            # Ingest single PDF
            chunks_count, error = _ingest_single_pdf(embedder, store, repo, pdf_path, item)
            
            if error:
                failed += 1
                state.failed_pdfs.append((pdf_path, error))
                print(f"[ingest_pdfs_node] {error}")
            else:
                ingested += chunks_count
                state.processed_pdfs.append(pdf_path)
            
            # Update progress
            progress = 40 + (50 * (idx + 1) / len(items))
            state.progress_percent = min(90.0, progress)
        
        state.docs_ingested = ingested
        state.docs_failed = failed
        
        print(f"[ingest_pdfs_node] Ingestion complete: {ingested} chunks, {failed} failed")
        
        return state
        
    except Exception as e:
        state.status = IngestionStatus.ERROR
        state.error = f"Ingestion failed: {str(e)}"
        print(f"[ingest_pdfs_node] Error: {state.error}")
        return state


# ============================================================================
# NODE 4: FINALIZE INGESTION
# ============================================================================

def finalize_ingestion_node(state: IngestionState) -> IngestionState:
    """
    Finalize ingestion: set status, timestamps, final metrics.
    
    Updates:
    - status: COMPLETED
    - completed_at: Timestamp
    - progress_percent: 100%
    """
    try:
        if state.status != IngestionStatus.ERROR:
            state.status = IngestionStatus.COMPLETED
        
        if not state.completed_at:
            state.completed_at = datetime.now()
        
        state.progress_percent = 100.0
        
        print(f"\n[finalize_ingestion_node] Ingestion complete!")
        print(f"  - Total found: {state.docs_found}")
        print(f"  - Existing: {state.docs_existing}")
        print(f"  - New: {state.docs_new}")
        print(f"  - Ingested: {state.docs_ingested}")
        print(f"  - Failed: {state.docs_failed}")
        
        return state
        
    except Exception as e:
        state.status = IngestionStatus.ERROR
        state.error = f"Finalization failed: {str(e)}"
        print(f"[finalize_ingestion_node] Error: {state.error}")
        return state
