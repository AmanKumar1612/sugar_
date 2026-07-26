"""
Public anonymous chat endpoint.

POST /chat/query   — main chat endpoint for anonymous users
GET  /chat/{query_id}/status — poll for officer reply

Rate-limited with slowapi.
Public users can only use kb_only mode (no web search, controls cost).
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.guest_session import GuestSession
from app.repositories.grievance_repository import GrievanceRepository
from app.repositories.guest_session_repository import GuestSessionRepository
from app.schemas.public_chat import (
    ContactInfo,
    EscalationResponse,
    PublicChatRequest,
    PublicChatResponse,
    QueryStatusResponse,
    SourceResponse,
)
from app.services.rag.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Public Chat"],
)

# Module-level limiter (key shared with app.state.limiter in main.py)
_limiter = Limiter(key_func=get_remote_address)


# =============================================================================
# POST /chat/query
# =============================================================================

@router.post(
    "/query",
    response_model=None,  # returns either PublicChatResponse or EscalationResponse
    summary="Public anonymous chat query",
    description=(
        "Send a question to the Sugarcane Dept assistant. Answers use only the knowledge base (kb_only). "
        "If confidence is too low the query is escalated to an officer and a query_id "
        "is returned for polling via GET /chat/{query_id}/status."
    ),
)
@_limiter.limit(settings.PUBLIC_CHAT_RATE_LIMIT)
def public_chat_query(
    request_body: PublicChatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    question = request_body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be blank.",
        )

    # ── Session management ────────────────────────────────────────────────────
    # Accept client-supplied session_id or generate a new one.
    session_token = request_body.session_id or str(uuid.uuid4())
    guest_session = GuestSessionRepository.get_or_create(db, session_token)

    # ── RAG pipeline ──────────────────────────────────────────────────────────
    # Public users are always kb_only + public scope.
    try:
        result = RAGService.answer(
            question=question,
            history=request_body.history,
            mode="kb_only",
            scope="public",
            include_citations=False,  # no citations for public
        )
    except Exception:
        logger.exception("RAGService failed for public query: %s", question[:80])
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again.",
        )

    sources = [
        SourceResponse(title=s["title"], url=s["url"])
        for s in result.get("sources", [])
    ]

    # ── Confidence check → escalation ────────────────────────────────────────
    if result["escalate"]:
        escalation_record = GrievanceRepository.create(
            db=db,
            query_text=question,
            bot_answer=result["answer"] if result["answer"] else None,
            retrieval_score=result["retrieval_score"],
            llm_confidence_label=result["llm_confidence_label"],
            combined_score=result["combined_score"],
            retrieved_chunks=result["retrieved_chunks"],
            mode="kb_only",
            session_id=str(guest_session.id),
            user_id=None,
        )
        return EscalationResponse(
            session_id=session_token,
            query_id=str(escalation_record.id),
            escalated=True,
            contact_required=True,
        )

    # ── High-confidence direct answer ─────────────────────────────────────────
    return PublicChatResponse(
        session_id=session_token,
        answer=result["answer"],
        sources=sources,
        escalated=False,
    )


# =============================================================================
# POST /chat/{query_id}/contact
# Capture contact info after escalation
# =============================================================================

@router.post(
    "/{query_id}/contact",
    status_code=status.HTTP_200_OK,
    summary="Submit contact info for an escalated query",
    description=(
        "After receiving an escalation response, call this endpoint to submit "
        "the user's contact details so the officer can reply directly."
    ),
)
def submit_contact(
    query_id: str,
    contact: ContactInfo,
    db: Session = Depends(get_db),
):
    record = GrievanceRepository.get_by_id(db, query_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found.")

    if not record.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This query is not associated with a guest session.",
        )

    session = db.query(GuestSession).filter_by(id=record.session_id).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    GuestSessionRepository.update_contact(
        db=db,
        session=session,
        name=contact.name,
        email=str(contact.email) if contact.email else None,
        phone=contact.phone,
    )

    return {"message": "Contact information saved. An officer will respond shortly."}


# =============================================================================
# GET /chat/{query_id}/status
# =============================================================================

@router.get(
    "/{query_id}/status",
    response_model=QueryStatusResponse,
    summary="Poll for officer reply status",
    description=(
        "Poll this endpoint after receiving an escalation response. "
        "Returns the current status and officer reply (when resolved)."
    ),
)
def get_query_status(
    query_id: str,
    db: Session = Depends(get_db),
):
    record = GrievanceRepository.get_by_id(db, query_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found.")

    return QueryStatusResponse(
        query_id=str(record.id),
        status=record.status,
        officer_reply=record.officer_reply,
    )
