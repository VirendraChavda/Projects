from __future__ import annotations
import argparse
import hashlib
import os
import re
from typing import List, Dict
from tqdm import tqdm

from backend.config import settings
from backend.services.sources.arxiv_client import search_arxiv_recent, download_pdfs
from backend.services.pdf_parse import pdf_to_sections
from backend.services.chunker import chunk_section
from backend.services.embeddings import Embedder
from backend.services.qdrant_store import QdrantStore
from backend.services.retriever import Retriever

def _title_fingerprint(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # very light stopword removal
    stops = {"the", "a", "an", "of", "and", "for", "on", "in", "to", "with"}
    toks = [w for w in t.split() if w not in stops]
    return " ".join(toks)

def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def cmd_download(args):
    print(f"[info] searching arXiv ({settings.arxiv_categories}), last {settings.arxiv_days_back} days …")
    items = search_arxiv_recent(settings.arxiv_max_results, settings.arxiv_days_back)
    items = download_pdfs(items, settings.data_raw)
    print(f"[ok] downloaded {len(items)} PDFs into {settings.data_raw}")
    return 0

def _ingest_pdf(embedder: Embedder, store: QdrantStore, pdf_path: str, meta: dict | None = None) -> int:
    meta = meta or {}
    paper_id = meta.get("arxiv_id") or os.path.splitext(os.path.basename(pdf_path))[0]
    sections = pdf_to_sections(pdf_path)
    all_chunks: list[dict] = []
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
        print(f"[warn] no chunks produced for {pdf_path}")
        return 0

    vecs = embedder.encode([c["text"] for c in all_chunks])
    n = store.upsert(all_chunks, vecs)
    return n

def cmd_ingest_folder(args):
    embedder = Embedder()
    store = QdrantStore(dim=embedder.model.get_sentence_embedding_dimension())
    folder = args.folder
    pdfs = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    total = 0
    for path in tqdm(pdfs, desc="Indexing PDFs"):
        try:
            total += _ingest_pdf(embedder, store, path)
        except Exception as e:
            print(f"[warn] failed to ingest {path}: {e}")
    print(f"[ok] upserted {total} chunks to collection '{store.collection}'")
    return 0

def cmd_download_and_ingest(args):
    # 1) download recent arXiv PDFs
    items = search_arxiv_recent(settings.arxiv_max_results, settings.arxiv_days_back)
    items = download_pdfs(items, settings.data_raw)
    # 2) ingest them
    embedder = Embedder()
    store = QdrantStore(dim=embedder.model.get_sentence_embedding_dimension())
    total = 0
    for md in tqdm(items, desc="Indexing downloaded PDFs"):
        path = md.get("pdf_path")
        if not path:
            continue
        try:
            total += _ingest_pdf(embedder, store, path, md)
        except Exception as e:
            print(f"[warn] failed to ingest {path}: {e}")
    print(f"[ok] upserted {total} chunks to collection '{store.collection}'")
    return 0

def cmd_search(args):
    embedder = Embedder()
    store = QdrantStore(dim=embedder.model.get_sentence_embedding_dimension())
    retr = Retriever(embedder, store)
    hits = retr.search(args.query, k=args.k)
    for i, h in enumerate(hits, 1):
        print(f"\n[{i}] score={h['score']:.3f}  {h['paper_id']}  {h['section_id']}")
        snippet = (h["text"] or "").replace("\n", " ")
        print("    " + (snippet[:180] + ("…" if len(snippet) > 180 else "")))
    return 0

def main():
    ap = argparse.ArgumentParser(prog="ai-research-agent (task1)", description="Download -> Ingest -> Search")
    sub = ap.add_subparsers(required=True)

    p = sub.add_parser("download-arxiv", help="Download recent AI papers from arXiv to data/raw")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("ingest-folder", help="Ingest PDFs from a folder (default: data/raw)")
    p.add_argument("folder", nargs="?", default=settings.data_raw)
    p.set_defaults(func=cmd_ingest_folder)

    p = sub.add_parser("download-and-ingest", help="Download recent arXiv papers and ingest them")
    p.set_defaults(func=cmd_download_and_ingest)

    p = sub.add_parser("search", help="Semantic search over Qdrant collection")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=10)
    p.set_defaults(func=cmd_search)

    args = ap.parse_args()
    raise SystemExit(args.func(args))

if __name__ == "__main__":
    main()
