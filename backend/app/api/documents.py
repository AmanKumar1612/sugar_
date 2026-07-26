"""
Document management endpoints — admin only.

Adds scope support (public/admin) to all ingestion flows.
Page-aware chunking is used for PDFs so citations carry accurate page numbers.
"""
import logging
import os
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, Query, UploadFile, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.dependencies import get_admin_user
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.ingestion.chunker import Chunker
from app.services.ingestion.indexing_service import IndexingService
from app.services.ingestion.pdf_ingestor import PDFIngestor
from app.services.ingestion.qdrant_service import QdrantService
from app.services.ingestion.website_ingestor import WebsiteIngestor
from app.schemas.document import DocumentResponse, DocumentScopeRequest, KBStatsResponse
from app.schemas.website import WebsiteRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

_CONTENT_PREVIEW_LIMIT = 5000
VALID_SCOPES = {"public", "admin"}


# ─────────────────────────────────────────────────────────────────────────────
# Background indexing tasks
# ─────────────────────────────────────────────────────────────────────────────

def _index_pdf_background(
    document_id: str,
    file_path: str,
    title: str,
    scope: str,
    source_url: str | None = None,
) -> None:
    """
    Page-aware PDF indexing running in background after the HTTP response is sent.
    Opens its own DB session to update chunk_count when done.
    """
    try:
        pages = PDFIngestor.extract_pages(file_path)
        page_chunks = Chunker.split_pages(pages)

        indexed = IndexingService.index_page_chunks(
            document_id=document_id,
            page_chunks=page_chunks,
            title=title,
            source_type="pdf",
            source_url=source_url,
            scope=scope,
        )

        db = SessionLocal()
        try:
            doc = DocumentRepository.get_by_id(db, document_id)
            if doc:
                doc.chunk_count = indexed
                doc.status = "INDEXED"
                db.commit()
        finally:
            db.close()

        logger.info(
            "Background PDF indexing complete: %s (%d chunks, scope=%s)",
            document_id, indexed, scope,
        )
    except Exception:
        logger.exception("Background PDF indexing failed: %s", document_id)
        db2 = SessionLocal()
        try:
            doc = DocumentRepository.get_by_id(db2, document_id)
            if doc:
                doc.status = "FAILED"
                db2.commit()
        finally:
            db2.close()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def _index_website_background(
    document_id: str,
    chunks: list[str],
    title: str,
    source_url: str,
    scope: str,
) -> None:
    try:
        indexed = IndexingService.index_chunks(
            document_id=document_id,
            chunks=chunks,
            title=title,
            source_type="website",
            source_url=source_url,
            scope=scope,
        )
        db = SessionLocal()
        try:
            doc = DocumentRepository.get_by_id(db, document_id)
            if doc:
                doc.chunk_count = indexed
                doc.status = "INDEXED"
                db.commit()
        finally:
            db.close()
        logger.info(
            "Background website indexing complete: %s (%d chunks, scope=%s)",
            document_id, indexed, scope,
        )
    except Exception:
        logger.exception("Background website indexing failed: %s", document_id)


# ===========================================================
# Upload PDF
# ===========================================================

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    scope: str = Form(default="public"),
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF to the permanent knowledge base.

    - scope: "public" (visible to all) or "admin" (admin-only queries).
    - Page-aware chunking preserves page numbers for accurate citations.
    - Returns 202 immediately; indexing runs in background.
    """
    if scope not in VALID_SCOPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope '{scope}'. Must be one of: {', '.join(sorted(VALID_SCOPES))}",
        )
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file selected.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed.")

    existing = DocumentRepository.get_by_title(db, file.filename)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A document with this filename has already been uploaded.",
        )

    tmp_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, tmp_filename)

    try:
        raw = await file.read()
        with open(file_path, "wb") as buf:
            buf.write(raw)

        # Quick page count for the response (no full extraction here)
        import fitz
        with fitz.open(file_path) as doc:
            page_count = len(doc)

        if page_count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No pages could be read from this PDF.",
            )

        # Save document record immediately (status = INDEXING)
        document = DocumentRepository.create(
            db=db,
            title=file.filename,
            source_type="pdf",
            file_name=file.filename,
            content="",  # filled by background task
        )
        document.scope = scope
        document.status = "INDEXING"
        db.commit()

        logger.info(
            "PDF accepted: %s (%d pages, scope=%s) by admin %s — indexing in background",
            file.filename, page_count, scope, current_user.id,
        )

        # Schedule indexing AFTER the response is sent
        # NOTE: tmp file is cleaned up inside the background task
        background_tasks.add_task(
            _index_pdf_background,
            document_id=str(document.id),
            file_path=file_path,
            title=document.title,
            scope=scope,
            source_url=None,
        )

        return {
            "message": "PDF received. Indexing is running in the background.",
            "document_id": str(document.id),
            "pages": page_count,
            "scope": scope,
            "status": "INDEXING",
        }

    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        db.rollback()
        logger.exception("PDF upload failed: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process PDF. Please try again.",
        )


# ===========================================================
# Add Website
# ===========================================================

@router.post("/add-website", status_code=status.HTTP_202_ACCEPTED)
def add_website(
    background_tasks: BackgroundTasks,
    request: WebsiteRequest,
    scope: str = Query(default="public"),
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    Crawl a website and add it to the knowledge base.

    - scope: "public" or "admin".
    """
    if scope not in VALID_SCOPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope '{scope}'. Must be one of: {', '.join(sorted(VALID_SCOPES))}",
        )

    url_str = str(request.url)

    existing = DocumentRepository.get_by_source_url(db, url_str)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This website URL has already been indexed.",
        )

    try:
        text = WebsiteIngestor.extract_text(url_str)

        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unable to extract text from the website.",
            )

        chunks = Chunker.split(text)

        document = DocumentRepository.create(
            db=db,
            title=url_str,
            source_type="website",
            source_url=url_str,
            content=text[:_CONTENT_PREVIEW_LIMIT],
        )
        document.scope = scope
        document.chunk_count = len(chunks)
        document.status = "INDEXING"
        db.commit()

        logger.info(
            "Website accepted: %s (%d chunks, scope=%s) by admin %s",
            url_str, len(chunks), scope, current_user.id,
        )

        background_tasks.add_task(
            _index_website_background,
            document_id=str(document.id),
            chunks=chunks,
            title=document.title,
            source_url=url_str,
            scope=scope,
        )

        return {
            "message": "Website received. Indexing is running in the background.",
            "document_id": str(document.id),
            "chunks": len(chunks),
            "scope": scope,
            "status": "INDEXING",
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Website indexing failed: %s", url_str)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to index website. Please try again.",
        )


# ===========================================================
# List Documents
# ===========================================================

@router.get("/")
def list_documents(
    scope: Optional[str] = Query(default=None, description="Filter by scope: public | admin"),
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List all documents, optionally filtered by scope."""
    if scope and scope not in VALID_SCOPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope.  Must be one of: {', '.join(sorted(VALID_SCOPES))}",
        )

    q = db.query(Document)
    if scope:
        q = q.filter(Document.scope == scope)
    documents = q.order_by(Document.created_at.desc()).all()
    return documents


# ===========================================================
# Document Statistics — scope breakdown
# NOTE: Must be before /{document_id}
# ===========================================================

@router.get("/stats/overview", response_model=KBStatsResponse)
def document_stats(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """KB statistics broken down by source_type and scope."""
    rows = (
        db.query(
            Document.source_type,
            Document.scope,
            func.count(Document.id).label("count"),
            func.coalesce(func.sum(Document.chunk_count), 0).label("chunks"),
        )
        .group_by(Document.source_type, Document.scope)
        .all()
    )

    total_documents = total_pdfs = total_websites = total_chunks = 0
    public_docs = admin_docs = public_chunks = admin_chunks = 0

    for row in rows:
        total_documents += row.count
        total_chunks += row.chunks
        if row.source_type == "pdf":
            total_pdfs += row.count
        elif row.source_type == "website":
            total_websites += row.count
        if row.scope == "public":
            public_docs += row.count
            public_chunks += row.chunks
        elif row.scope == "admin":
            admin_docs += row.count
            admin_chunks += row.chunks

    return KBStatsResponse(
        total_documents=total_documents,
        total_pdfs=total_pdfs,
        total_websites=total_websites,
        total_chunks=total_chunks,
        public_documents=public_docs,
        admin_documents=admin_docs,
        public_chunks=public_chunks,
        admin_chunks=admin_chunks,
    )


# ===========================================================
# Get Document by ID
# ===========================================================

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    document = DocumentRepository.get_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return document


# ===========================================================
# Update Document Scope
# ===========================================================

@router.patch("/{document_id}/scope", response_model=DocumentResponse)
def update_document_scope(
    document_id: str,
    request_body: DocumentScopeRequest,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    Change the scope of an existing document.

    NOTE: This updates the DB record only.  To update existing Qdrant vectors
    the document should be re-indexed (delete + re-upload), as Qdrant does not
    support bulk payload updates without re-ingestion in this pipeline.
    """
    document = DocumentRepository.get_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    document.scope = request_body.scope
    db.commit()
    db.refresh(document)
    logger.info(
        "Document %s scope updated to '%s' by admin %s",
        document_id, request_body.scope, current_user.id,
    )
    return document


# ===========================================================
# Delete Document
# ===========================================================

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    document = DocumentRepository.get_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    try:
        QdrantService.delete_document_chunks(document_id=document_id)
        DocumentRepository.delete(db, document)
        logger.info("Document deleted: %s by admin %s", document_id, current_user.id)
    except Exception:
        db.rollback()
        logger.exception("Failed to delete document %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document. Please try again.",
        )

    return {"message": "Document deleted successfully."}
