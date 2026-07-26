"""
GrievanceRepository — database access layer for EscalatedQuery records.
"""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.escalated_query import EscalatedQuery

logger = logging.getLogger(__name__)

VALID_STATUSES = {"pending_officer", "in_progress", "resolved"}


class GrievanceRepository:

    @staticmethod
    def create(
        db: Session,
        query_text: str,
        bot_answer: str | None,
        retrieval_score: float,
        llm_confidence_label: str,
        combined_score: float,
        retrieved_chunks: list[dict],
        mode: str,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> EscalatedQuery:
        record = EscalatedQuery(
            query_text=query_text,
            bot_answer=bot_answer,
            retrieval_score=retrieval_score,
            llm_confidence_label=llm_confidence_label,
            combined_score=combined_score,
            retrieved_chunks_json=json.dumps(retrieved_chunks),
            mode=mode,
            session_id=session_id,
            user_id=user_id,
            status="pending_officer",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(
            "Escalated query created: id=%s session=%s user=%s",
            record.id,
            session_id,
            user_id,
        )
        return record

    @staticmethod
    def get_by_id(db: Session, query_id: str) -> EscalatedQuery | None:
        return (
            db.query(EscalatedQuery)
            .filter(EscalatedQuery.id == query_id)
            .first()
        )

    @staticmethod
    def list_pending(
        db: Session,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EscalatedQuery]:
        q = db.query(EscalatedQuery)
        if status:
            q = q.filter(EscalatedQuery.status == status)
        else:
            q = q.filter(EscalatedQuery.status != "resolved")
        return (
            q.order_by(EscalatedQuery.created_at.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_status(
        db: Session,
        record: EscalatedQuery,
        new_status: str,
    ) -> EscalatedQuery:
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        record.status = new_status
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def set_reply(
        db: Session,
        record: EscalatedQuery,
        officer_reply: str,
    ) -> EscalatedQuery:
        record.officer_reply = officer_reply
        record.status = "resolved"
        record.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_for_session(
        db: Session,
        session_id: str,
    ) -> list[EscalatedQuery]:
        return (
            db.query(EscalatedQuery)
            .filter(EscalatedQuery.session_id == session_id)
            .order_by(EscalatedQuery.created_at.desc())
            .all()
        )
