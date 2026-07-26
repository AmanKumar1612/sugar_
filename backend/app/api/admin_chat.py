"""
Admin chat endpoints — authenticated admins only.

POST /admin/chat/query          — RAG query with mode selection and citations
POST /admin/documents/adhoc-upload  — ephemeral PDF upload (chat-scoped)
POST /admin/documents/adhoc-query   — query an ephemeral PDF
POST /admin/documents/adhoc-promote — promote ephemeral PDF to permanent KB
"""
import logging
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.dependencies import get_admin_user
from app.core.config import settings
from app.models.user import User
from app.repositories.grievance_repository import GrievanceRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.admin_chat import (
    AdHocPDFQueryRequest,
    AdHocPDFQueryResponse,
    AdHocPromoteRequest,
    AdHocPromoteResponse,
    AdminChatRequest,
    AdminChatResponse,
    CitationResponse,
    SourceResponse,
)
from app.services.ingestion.chunker import Chunker
from app.services.ingestion.indexing_service import IndexingService
from app.services.ingestion.pdf_ingestor import PDFIngestor
from app.services.ingestion.qdrant_service import QdrantService
from app.services.rag.rag_service import RAGService
from app.services.rag.retriever import Retriever

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin Chat"],
)

ADHOC_UPLOAD_DIR = "uploads/adhoc"
os.makedirs(ADHOC_UPLOAD_DIR, exist_ok=True)


# =============================================================================
# POST /admin/chat/query
# =============================================================================

@router.post(
    "/chat/query",
    response_model=AdminChatResponse,
    summary="Admin RAG chat query with mode selection and citations",
)
def admin_chat_query(
    request_body: AdminChatRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    question = request_body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be blank.",
        )

    try:
        result = RAGService.answer(
            question=question,
            history=request_body.history,
            mode=request_body.mode,
            scope="admin",
            include_citations=True,
        )
    except Exception:
        logger.exception("RAGService failed for admin query: %s", question[:80])
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again.",
        )

    sources = [
        SourceResponse(title=s["title"], url=s["url"])
        for s in result.get("sources", [])
    ]
    citations = [
        CitationResponse(**c)
        for c in result.get("citations", [])
    ]

    query_id: str | None = None
    if result["escalate"]:
        escalation = GrievanceRepository.create(
            db=db,
            query_text=question,
            bot_answer=result["answer"],
            retrieval_score=result["retrieval_score"],
            llm_confidence_label=result["llm_confidence_label"],
            combined_score=result["combined_score"],
            retrieved_chunks=result["retrieved_chunks"],
            mode=request_body.mode,
            session_id=None,
            user_id=str(current_user.id),
        )
        query_id = str(escalation.id)

    return AdminChatResponse(
        answer=result["answer"],
        sources=sources,
        citations=citations,
        retrieval_score=result["retrieval_score"],
        llm_confidence_label=result["llm_confidence_label"],
        combined_score=result["combined_score"],
        escalated=result["escalate"],
        query_id=query_id,
    )


# =============================================================================
# POST /admin/documents/adhoc-upload
# Upload a PDF for ephemeral (session-scoped) use — NOT added to permanent KB
# =============================================================================

@router.post(
    "/documents/adhoc-upload",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a PDF for ad-hoc chat (ephemeral, not added to KB)",
    description=(
        "Upload a PDF to ask questions about it in this session only. "
        "The document is indexed into a temporary Qdrant collection scoped to this upload. "
        "Use the returned session_collection to query it via POST /admin/documents/adhoc-query. "
        "To promote it to the permanent KB call POST /admin/documents/adhoc-promote."
    ),
)
async def adhoc_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file selected.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed.")

    raw = await file.read()
    if len(raw) > settings.ADHOC_PDF_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.ADHOC_PDF_MAX_BYTES // 1_048_576} MB.",
        )

    # Save temporarily for PyMuPDF processing
    tmp_name = f"{uuid.uuid4().hex}_{file.filename}"
    tmp_path = os.path.join(ADHOC_UPLOAD_DIR, tmp_name)

    try:
        with open(tmp_path, "wb") as buf:
            buf.write(raw)

        pages = PDFIngestor.extract_pages(tmp_path)
        if not pages:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No text could be extracted from this PDF.",
            )

        page_chunks = Chunker.split_pages(pages)

        # Use an ephemeral Qdrant collection named by a short random ID
        session_id = uuid.uuid4().hex[:12]
        session_collection = f"adhoc-{session_id}"

        # Create the ephemeral collection in Qdrant
        from qdrant_client.models import Distance, VectorParams
        QdrantService.client.create_collection(
            collection_name=session_collection,
            vectors_config=VectorParams(
                size=QdrantService.VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )

        # Index in background
        doc_id = f"adhoc-{session_id}"
        background_tasks.add_task(
            _index_adhoc_background,
            doc_id=doc_id,
            page_chunks=page_chunks,
            title=file.filename,
            collection=session_collection,
            tmp_path=tmp_path,
        )

        logger.info(
            "Ad-hoc PDF accepted: %s (%d page-chunks) by admin %s → collection %s",
            file.filename,
            len(page_chunks),
            current_user.id,
            session_collection,
        )

        return {
            "message": "PDF received. Indexing in background.",
            "session_collection": session_collection,
            "filename": file.filename,
            "page_count": len(pages),
            "estimated_chunks": len(page_chunks),
        }

    except HTTPException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        logger.exception("Ad-hoc PDF upload failed: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process PDF. Please try again.",
        )


def _index_adhoc_background(
    doc_id: str,
    page_chunks: list,
    title: str,
    collection: str,
    tmp_path: str,
) -> None:
    try:
        IndexingService.index_page_chunks(
            document_id=doc_id,
            page_chunks=page_chunks,
            title=title,
            source_type="pdf",
            source_url=None,
            scope="admin",
            collection_override=collection,
        )
        logger.info("Ad-hoc indexing complete for collection %s", collection)
    except Exception:
        logger.exception("Ad-hoc background indexing failed for collection %s", collection)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# =============================================================================
# POST /admin/documents/adhoc-query
# =============================================================================

@router.post(
    "/documents/adhoc-query",
    response_model=AdHocPDFQueryResponse,
    summary="Query an ad-hoc (ephemeral) PDF",
)
def adhoc_query(
    request_body: AdHocPDFQueryRequest,
    current_user: User = Depends(get_admin_user),
):
    question = request_body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be blank.",
        )

    # Verify the ephemeral collection exists
    try:
        collections = {c.name for c in QdrantService.client.get_collections().collections}
        if request_body.session_collection not in collections:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Session collection '{request_body.session_collection}' not found. "
                    "It may still be indexing — please wait a moment and retry."
                ),
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to check collections")

    try:
        result = RAGService.answer(
            question=question,
            history=request_body.history,
            mode="kb_only",
            scope="admin",
            include_citations=True,
            collection_override=request_body.session_collection,
        )
    except Exception:
        logger.exception("RAGService failed for adhoc query")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service error. Please try again.",
        )

    citations = [CitationResponse(**c) for c in result.get("citations", [])]
    return AdHocPDFQueryResponse(
        answer=result["answer"],
        citations=citations,
    )


# =============================================================================
# POST /admin/documents/adhoc-promote
# Promote an ephemeral collection to the permanent KB
# =============================================================================

@router.post(
    "/documents/adhoc-promote",
    response_model=AdHocPromoteResponse,
    summary="Promote an ad-hoc PDF to the permanent knowledge base",
    description=(
        "Re-indexes the ephemeral collection into the permanent Qdrant collection "
        "with the given scope tag, creates a Document record, then drops the "
        "ephemeral collection."
    ),
)
def adhoc_promote(
    request_body: AdHocPromoteRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    collection = request_body.session_collection
    if not collection.startswith("adhoc-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_collection. Must start with 'adhoc-'.",
        )

    # Scroll all points from the ephemeral collection
    try:
        scroll_result = QdrantService.client.scroll(
            collection_name=collection,
            limit=10_000,
            with_payload=True,
            with_vectors=True,
        )
        points = scroll_result[0]
    except Exception:
        logger.exception("Failed to scroll ephemeral collection %s", collection)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection}' not found or could not be read.",
        )

    if not points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No indexed chunks found in this collection.  It may still be indexing.",
        )

    # Determine title
    sample_payload = points[0].payload or {}
    title = request_body.title or sample_payload.get("title", collection)

    # Create permanent DB document record
    doc = DocumentRepository.create(
        db=db,
        title=title,
        source_type="pdf",
        file_name=title,
        source_url=None,
        content="",
    )
    doc.scope = request_body.scope
    doc.status = "INDEXING"
    doc.chunk_count = len(points)
    db.commit()

    # Re-upsert each point into the permanent collection with updated metadata
    from qdrant_client.models import PointStruct
    permanent_points = []
    for pt in points:
        payload = dict(pt.payload or {})
        payload["document_id"] = str(doc.id)
        payload["scope"] = request_body.scope
        permanent_points.append(
            PointStruct(id=str(uuid.uuid4()), vector=pt.vector, payload=payload)
        )

    try:
        # Batch upsert in chunks of 100
        batch_size = 100
        for i in range(0, len(permanent_points), batch_size):
            QdrantService.client.upsert(
                collection_name=QdrantService.COLLECTION_NAME,
                points=permanent_points[i:i + batch_size],
            )
        doc.status = "INDEXED"
        db.commit()
    except Exception:
        doc.status = "FAILED"
        db.commit()
        logger.exception("Failed to promote collection %s to permanent KB", collection)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote document to permanent KB.",
        )

    # Drop the ephemeral collection
    try:
        QdrantService.client.delete_collection(collection)
        logger.info("Ephemeral collection %s dropped after promotion.", collection)
    except Exception:
        logger.warning("Could not drop ephemeral collection %s (non-fatal).", collection)

    return AdHocPromoteResponse(
        document_id=str(doc.id),
        message=f"Document '{title}' promoted to permanent KB with scope='{request_body.scope}'.",
        chunks=len(permanent_points),
    )
