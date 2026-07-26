"""
seed_kb.py — Populate the Sugarcane Dept Chatbot knowledge base with sample documents.

Usage:
    cd backend
    python scripts/seed_kb.py

What this does:
  1. Creates the database tables (idempotent).
  2. Crawls the Sugarcane Industries Department, Govt. of Bihar website (public scope).
  3. Uploads the sample.pdf from data/pdfs/ (public scope) if it exists — replace this
     with real scheme PDFs/circulars from ccs.bihar.gov.in for production use.
  4. Verifies that /chat/query returns a real answer.

Set the DATABASE_URL, QDRANT_URL, QDRANT_API_KEY, GEMINI_API_KEY env vars
(or have a backend/.env file) before running.

IMPORTANT: The single URL below is only a starting point. For real farmer queries to
work well, add the actual scheme pages/PDFs (Kisan Panjikaran, Mukhyamantri Ganna
Vikas Yojana, gur license rules, ZDC notifications, etc.) via the admin document
upload endpoints — see UPGRADE_NOTES.md.
"""

import logging
import os
import sys
import uuid

# ── Make sure the project root is on sys.path ─────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models import *  # noqa: F401,F403 — registers all ORM models
from app.repositories.document_repository import DocumentRepository
from app.services.ingestion.chunker import Chunker
from app.services.ingestion.indexing_service import IndexingService
from app.services.ingestion.pdf_ingestor import PDFIngestor
from app.services.ingestion.qdrant_service import QdrantService
from app.services.ingestion.website_ingestor import WebsiteIngestor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("seed_kb")

# ── Sample documents (all public scope) ──────────────────────────────────────
# Replace/extend this list with the real scheme pages from ccs.bihar.gov.in.

SEED_WEBSITES = [
    {
        "url": "https://ccs.bihar.gov.in/",
        "title": "Sugarcane Industries Department, Govt. of Bihar — Home",
        "scope": "public",
    },
]

SAMPLE_PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs", "sample.pdf")


def ensure_qdrant_collection() -> None:
    logger.info("Ensuring Qdrant collection '%s' exists ...", settings.QDRANT_COLLECTION)
    QdrantService.create_collection()


def seed_websites(db) -> None:
    for item in SEED_WEBSITES:
        existing = DocumentRepository.get_by_source_url(db, item["url"])
        if existing and (existing.chunk_count or 0) > 0:
            logger.info("Website already indexed — skipping: %s", item["url"])
            continue
        if existing:
            logger.info(
                "Website row exists but has 0 indexed chunks (a previous run "
                "likely failed) — retrying: %s", item["url"]
            )

        logger.info("Crawling: %s", item["url"])
        try:
            text = WebsiteIngestor.extract_text(item["url"])
        except Exception as exc:
            logger.warning("Failed to crawl %s: %s", item["url"], exc)
            continue

        if not text.strip():
            logger.warning("No text extracted from %s — skipping.", item["url"])
            continue

        chunks = Chunker.split(text)
        if existing:
            doc = existing
        else:
            doc = DocumentRepository.create(
                db=db,
                title=item["title"],
                source_type="website",
                source_url=item["url"],
                content=text[:5000],
            )
        doc.scope = item["scope"]
        doc.status = "INDEXING"
        db.commit()

        logger.info("Indexing %d chunks for: %s", len(chunks), item["title"])
        indexed = IndexingService.index_chunks(
            document_id=str(doc.id),
            chunks=chunks,
            title=item["title"],
            source_type="website",
            source_url=item["url"],
            scope=item["scope"],
        )
        doc.chunk_count = indexed
        doc.status = "INDEXED"
        db.commit()
        logger.info("  ✓ %d chunks indexed.", indexed)


def seed_pdf(db) -> None:
    pdf_path = os.path.abspath(SAMPLE_PDF_PATH)
    if not os.path.exists(pdf_path):
        logger.info("Sample PDF not found at %s — skipping PDF seed.", pdf_path)
        return

    filename = os.path.basename(pdf_path)
    existing = DocumentRepository.get_by_title(db, filename)
    if existing and (existing.chunk_count or 0) > 0:
        logger.info("Sample PDF already indexed — skipping.")
        return
    if existing:
        logger.info(
            "Sample PDF row exists but has 0 indexed chunks (a previous run "
            "likely failed) — retrying."
        )

    logger.info("Indexing sample PDF: %s", pdf_path)
    pages = PDFIngestor.extract_pages(pdf_path)
    if not pages:
        logger.warning("No pages extracted from sample PDF — skipping.")
        return

    page_chunks = Chunker.split_pages(pages)

    if existing:
        doc = existing
    else:
        doc = DocumentRepository.create(
            db=db,
            title=filename,
            source_type="pdf",
            file_name=filename,
            content="",
        )
    doc.scope = "public"
    doc.status = "INDEXING"
    db.commit()

    logger.info("Indexing %d page-chunks for sample PDF ...", len(page_chunks))
    indexed = IndexingService.index_page_chunks(
        document_id=str(doc.id),
        page_chunks=page_chunks,
        title=filename,
        source_type="pdf",
        source_url=None,
        scope="public",
    )
    doc.chunk_count = indexed
    doc.status = "INDEXED"
    db.commit()
    logger.info("  ✓ %d chunks indexed.", indexed)


def smoke_test() -> None:
    """Quick retrieval smoke test — no LLM call, just checks Qdrant returns something."""
    from app.services.rag.retriever import Retriever
    logger.info("Running retrieval smoke test ...")
    chunks = Retriever.search("गन्ना किसान पंजीकरण कैसे करें", limit=3, scope="public")
    if chunks:
        logger.info("  ✓ Retrieval returned %d chunk(s).", len(chunks))
        logger.info("  Sample: %s", chunks[0]["text"][:120])
    else:
        logger.warning("  ✗ No chunks returned — check Qdrant connectivity and embeddings.")


def main() -> None:
    logger.info("=== Sugarcane Dept Chatbot KB Seed Script ===")
    logger.info("Database: %s", settings.DATABASE_URL[:40] + "...")
    logger.info("Qdrant:   %s / %s", settings.QDRANT_URL, settings.QDRANT_COLLECTION)

    # Create tables
    logger.info("Creating database tables (if not exist) ...")
    Base.metadata.create_all(bind=engine)

    ensure_qdrant_collection()

    db = SessionLocal()
    try:
        seed_websites(db)
        seed_pdf(db)
    finally:
        db.close()

    smoke_test()
    logger.info("=== Seed complete ===")


if __name__ == "__main__":
    main()
