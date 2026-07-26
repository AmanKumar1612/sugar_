"""
Grievance system integration API — consumed by the separate grievance backend.

Pull-based design (no webhooks for v1): the grievance backend polls these endpoints.

GET  /grievance/pending              — list unresolved escalated queries
GET  /grievance/{query_id}           — full detail of one query
PATCH /grievance/{query_id}/status   — mark in_progress (claim)
POST  /grievance/{query_id}/reply    — officer submits final answer → resolved
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_admin_user
from app.models.guest_session import GuestSession
from app.repositories.grievance_repository import GrievanceRepository, VALID_STATUSES
from app.schemas.grievance import (
    ChunkSnapshot,
    ContactInfo,
    GrievanceDetail,
    GrievanceSummary,
    OfficerReplyRequest,
    OfficerReplyResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
)
from app.services.rag.cache_service import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/grievance",
    tags=["Grievance System"],
)


def _get_contact(db: Session, record) -> ContactInfo | None:
    """Fetch contact info from the linked GuestSession (if any)."""
    if not record.session_id:
        return None
    session: GuestSession | None = (
        db.query(GuestSession).filter(GuestSession.id == record.session_id).first()
    )
    if not session:
        return None
    if not any([session.contact_name, session.contact_email, session.contact_phone]):
        return None
    return ContactInfo(
        name=session.contact_name,
        email=session.contact_email,
        phone=session.contact_phone,
    )


def _parse_chunks(record) -> list[ChunkSnapshot]:
    if not record.retrieved_chunks_json:
        return []
    try:
        raw = json.loads(record.retrieved_chunks_json)
        return [ChunkSnapshot(**c) for c in raw]
    except Exception:
        return []


# =============================================================================
# GET /grievance/pending
# =============================================================================

@router.get(
    "/pending",
    response_model=list[GrievanceSummary],
    summary="List pending / in-progress escalated queries",
    description=(
        "Returns all escalated queries not yet resolved. "
        "Optionally filter by status: pending_officer | in_progress."
    ),
)
def list_pending(
    filter_status: str | None = Query(
        default=None,
        alias="status",
        description="Filter by status: pending_officer | in_progress.  Omit for both.",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if filter_status and filter_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status filter.  Allowed: {', '.join(sorted(VALID_STATUSES))}",
        )

    records = GrievanceRepository.list_pending(db, status=filter_status, limit=limit, offset=offset)

    result = []
    for rec in records:
        result.append(
            GrievanceSummary(
                query_id=str(rec.id),
                query_text=rec.query_text,
                session_id=rec.session_id,
                user_id=rec.user_id,
                contact=_get_contact(db, rec),
                bot_answer=rec.bot_answer,
                retrieval_score=rec.retrieval_score,
                llm_confidence_label=rec.llm_confidence_label,
                combined_score=rec.combined_score,
                mode=rec.mode,
                status=rec.status,
                created_at=rec.created_at,
            )
        )
    return result


# =============================================================================
# GET /grievance/{query_id}
# =============================================================================

@router.get(
    "/{query_id}",
    response_model=GrievanceDetail,
    summary="Get full detail of an escalated query",
)
def get_grievance(
    query_id: str,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    rec = GrievanceRepository.get_by_id(db, query_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found.")

    return GrievanceDetail(
        query_id=str(rec.id),
        query_text=rec.query_text,
        session_id=rec.session_id,
        user_id=rec.user_id,
        contact=_get_contact(db, rec),
        bot_answer=rec.bot_answer,
        retrieved_chunks=_parse_chunks(rec),
        retrieval_score=rec.retrieval_score,
        llm_confidence_label=rec.llm_confidence_label,
        combined_score=rec.combined_score,
        mode=rec.mode,
        status=rec.status,
        officer_reply=rec.officer_reply,
        resolved_at=rec.resolved_at,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
    )


# =============================================================================
# PATCH /grievance/{query_id}/status
# =============================================================================

@router.patch(
    "/{query_id}/status",
    response_model=StatusUpdateResponse,
    summary="Claim a query (mark in_progress) to prevent duplicate officer work",
)
def update_status(
    query_id: str,
    request_body: StatusUpdateRequest,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    rec = GrievanceRepository.get_by_id(db, query_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found.")

    if request_body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status.  Allowed: {', '.join(sorted(VALID_STATUSES))}",
        )

    # Prevent re-opening a resolved query via this endpoint
    if rec.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This query is already resolved and cannot be reopened via this endpoint.",
        )

    updated = GrievanceRepository.update_status(db, rec, request_body.status)
    logger.info(
        "Grievance %s status updated to '%s' by admin %s",
        query_id,
        updated.status,
        current_user.id,
    )
    return StatusUpdateResponse(
        query_id=str(updated.id),
        status=updated.status,
        message=f"Query status updated to '{updated.status}'.",
    )


# =============================================================================
# POST /grievance/{query_id}/reply
# =============================================================================

@router.post(
    "/{query_id}/reply",
    response_model=OfficerReplyResponse,
    summary="Submit officer reply — marks query as resolved",
    description=(
        "Submit the final officer answer for an escalated query. "
        "Status is set to 'resolved' and the cache entry for this query is invalidated "
        "so the next identical question re-runs through the full pipeline."
    ),
)
def submit_reply(
    query_id: str,
    request_body: OfficerReplyRequest,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    rec = GrievanceRepository.get_by_id(db, query_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found.")

    if rec.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This query has already been resolved.",
        )

    updated = GrievanceRepository.set_reply(db, rec, request_body.reply)

    # Invalidate cache so next identical question re-runs the pipeline
    get_cache().invalidate_by_query_id(query_id)

    logger.info(
        "Grievance %s resolved by admin %s",
        query_id,
        current_user.id,
    )

    return OfficerReplyResponse(
        query_id=str(updated.id),
        status=updated.status,
        message="Reply submitted successfully. Query is now resolved.",
    )
