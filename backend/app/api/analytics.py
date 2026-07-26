import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_admin_user
from app.models.user import User
from app.models.chat import Chat
from app.models.document import Document
from app.models.search_log import SearchLog

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


# ==========================================================
# Dashboard Overview
# ==========================================================

@router.get("/overview")
def overview(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).scalar()
    total_chats = db.query(func.count(Chat.id)).scalar()
    total_documents = db.query(func.count(Document.id)).scalar()

    search_counts = (
        db.query(
            SearchLog.success,
            func.count(SearchLog.id).label("cnt"),
        )
        .group_by(SearchLog.success)
        .all()
    )

    successful_searches = 0
    failed_searches = 0
    for row in search_counts:
        if row.success:
            successful_searches = row.cnt
        else:
            failed_searches = row.cnt

    return {
        "total_users": total_users,
        "total_chats": total_chats,
        "total_documents": total_documents,
        "total_searches": successful_searches + failed_searches,
        "successful_searches": successful_searches,
        "failed_searches": failed_searches,
    }


# ==========================================================
# Top Searches
# ==========================================================

@router.get("/top-searches")
def top_searches(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            SearchLog.query,
            func.count(SearchLog.id).label("count"),
        )
        .group_by(SearchLog.query)
        .order_by(func.count(SearchLog.id).desc())
        .limit(10)
        .all()
    )

    return [{"query": row.query, "count": row.count} for row in rows]


# ==========================================================
# Failed Searches
# ==========================================================

@router.get("/failed-searches")
def failed_searches(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(func.count(SearchLog.id))
        .filter(SearchLog.success.is_(False))
        .scalar()
    )

    return {"failed_searches": count}


# ==========================================================
# Recent Searches
# ==========================================================

@router.get("/recent-searches")
def recent_searches(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(SearchLog)
        .order_by(SearchLog.created_at.desc())
        .limit(20)
        .all()
    )

    return logs


# ==========================================================
# User Statistics
# ==========================================================

@router.get("/user-stats")
def user_stats(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            User.is_verified,
            User.is_active,
            func.count(User.id).label("cnt"),
        )
        .group_by(User.is_verified, User.is_active)
        .all()
    )

    verified = unverified = active = inactive = 0
    for row in rows:
        if row.is_verified:
            verified += row.cnt
        else:
            unverified += row.cnt
        if row.is_active:
            active += row.cnt
        else:
            inactive += row.cnt

    return {
        "verified_users": verified,
        "unverified_users": unverified,
        "active_users": active,
        "inactive_users": inactive,
    }


# ==========================================================
# Document Statistics
# ==========================================================

@router.get("/document-stats")
def document_stats(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Document.source_type,
            func.count(Document.id).label("count"),
            func.coalesce(func.sum(Document.chunk_count), 0).label("chunks"),
        )
        .group_by(Document.source_type)
        .all()
    )

    total_documents = 0
    pdf_documents = 0
    website_documents = 0
    total_chunks = 0

    for row in rows:
        total_documents += row.count
        total_chunks += row.chunks
        if row.source_type == "pdf":
            pdf_documents = row.count
        elif row.source_type == "website":
            website_documents = row.count

    return {
        "total_documents": total_documents,
        "pdf_documents": pdf_documents,
        "website_documents": website_documents,
        "total_chunks": total_chunks,
    }
