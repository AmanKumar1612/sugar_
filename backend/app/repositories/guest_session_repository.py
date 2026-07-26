"""
GuestSessionRepository — manages anonymous session records.
"""
from sqlalchemy.orm import Session

from app.models.guest_session import GuestSession


class GuestSessionRepository:

    @staticmethod
    def get_or_create(db: Session, session_token: str) -> GuestSession:
        """
        Return the existing GuestSession for this token, or create a new one.
        """
        existing = (
            db.query(GuestSession)
            .filter(GuestSession.session_token == session_token)
            .first()
        )
        if existing:
            return existing

        session = GuestSession(session_token=session_token)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_by_token(db: Session, session_token: str) -> GuestSession | None:
        return (
            db.query(GuestSession)
            .filter(GuestSession.session_token == session_token)
            .first()
        )

    @staticmethod
    def update_contact(
        db: Session,
        session: GuestSession,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> GuestSession:
        if name is not None:
            session.contact_name = name
        if email is not None:
            session.contact_email = email
        if phone is not None:
            session.contact_phone = phone
        db.commit()
        db.refresh(session)
        return session
