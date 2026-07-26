"""
EscalatedQuery — stores queries where the bot's confidence was too low
to return a direct answer.  The grievance backend polls these records
and officers submit replies through the /grievance API.
"""
import uuid

from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class EscalatedQuery(Base):

    __tablename__ = "escalated_queries"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Who asked ───────────────────────────────────────────────────────────
    # One of session_id (anonymous) or user_id (admin/registered) will be set
    session_id = Column(
        String(36),
        ForeignKey("guest_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── The query ────────────────────────────────────────────────────────────
    query_text = Column(Text, nullable=False)

    # ── Bot's attempted answer (may be empty if generation was skipped) ──────
    bot_answer = Column(Text, nullable=True)

    # ── Confidence signals ───────────────────────────────────────────────────
    # Average cosine similarity of top-K retrieved chunks (0.0–1.0)
    retrieval_score = Column(Float, nullable=True)
    # LLM self-check label: "high" | "medium" | "low" | "no_answer"
    llm_confidence_label = Column(String(20), nullable=True)
    # Combined numeric score (0.0–1.0)
    combined_score = Column(Float, nullable=True)

    # ── Retrieved chunks snapshot (JSON array stored as text) ────────────────
    retrieved_chunks_json = Column(Text, nullable=True)

    # ── Mode used ────────────────────────────────────────────────────────────
    mode = Column(String(20), nullable=True)  # kb_only | web_only | hybrid

    # ── Status lifecycle ─────────────────────────────────────────────────────
    # pending_officer → in_progress → resolved
    status = Column(
        String(30),
        nullable=False,
        default="pending_officer",
        index=True,
    )

    # ── Officer reply ────────────────────────────────────────────────────────
    officer_reply = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    guest_session = relationship(
        "GuestSession",
        back_populates="escalated_queries",
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
    )
