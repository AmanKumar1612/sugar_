import logging

from sqlalchemy.orm import Session

from app.models.search_log import SearchLog

logger = logging.getLogger(__name__)


class SearchLogRepository:

    @staticmethod
    def create(
        db: Session,
        query: str,
        user_id: str | None = None,
        success: bool = True,
    ) -> SearchLog:
        """
        Persist a search log entry.
        user_id may be None for unauthenticated (guest) queries.
        """
        log = SearchLog(
            query=query,
            user_id=user_id,
            success=success,
        )
        try:
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(
                "Failed to create SearchLog for user_id=%s query='%s'",
                user_id,
                query,
            )
            return log  # Return unsaved instance so callers don't crash

        return log
