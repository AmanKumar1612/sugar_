"""
Pydantic schemas for the public anonymous chat endpoint (/chat/query)
and the query-status polling endpoint (/chat/{query_id}/status).
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# ─────────────────────────────────────────────────────────────────────────────
# Request
# ─────────────────────────────────────────────────────────────────────────────

class PublicChatRequest(BaseModel):
    """
    Body for POST /chat/query (public, anonymous).

    session_id is a client-generated UUID that the browser stores
    (e.g. in a cookie or localStorage).  If omitted the server creates one
    and returns it in the response.
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["Ganna kisan registration kaise kare?"],
    )
    history: str = Field(
        default="",
        max_length=8000,
        description="Last N conversation turns formatted as 'User: ...\\nAssistant: ...'",
    )
    session_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Opaque session token.  Pass the value returned by the previous call.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Source / citation schemas
# ─────────────────────────────────────────────────────────────────────────────

class SourceResponse(BaseModel):
    title: str
    url: str


# ─────────────────────────────────────────────────────────────────────────────
# Normal (high-confidence) answer response
# ─────────────────────────────────────────────────────────────────────────────

class PublicChatResponse(BaseModel):
    """Returned when confidence is high enough to give a direct answer."""
    session_id: str
    answer: str
    sources: list[SourceResponse] = Field(default_factory=list)
    escalated: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Escalation contact capture (attached to an escalation request)
# ─────────────────────────────────────────────────────────────────────────────

class ContactInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, examples=["Arjun Sharma"])
    email: Optional[EmailStr] = Field(default=None, examples=["arjun@example.com"])
    phone: Optional[str] = Field(default=None, max_length=50, examples=["+91-9876543210"])


# ─────────────────────────────────────────────────────────────────────────────
# Escalation response (low-confidence)
# ─────────────────────────────────────────────────────────────────────────────

class EscalationResponse(BaseModel):
    """Returned when confidence is too low and the query is forwarded to an officer."""
    session_id: str
    query_id: str = Field(
        ...,
        description="Use this ID to poll GET /chat/{query_id}/status for an officer reply.",
    )
    message: str = Field(
        default=(
            "Your question has been forwarded to an officer. "
            "Please provide your contact details so we can reply to you."
        )
    )
    escalated: bool = True
    contact_required: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Status polling
# ─────────────────────────────────────────────────────────────────────────────

class QueryStatusResponse(BaseModel):
    query_id: str
    status: str = Field(
        ...,
        description="pending_officer | in_progress | resolved",
        examples=["pending_officer"],
    )
    officer_reply: Optional[str] = Field(
        default=None,
        description="Populated once status == 'resolved'.",
    )
