"""
Pydantic schemas for the /grievance/* endpoints.
These are consumed by the separate grievance-system backend developer.
"""
import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Nested helpers
# ─────────────────────────────────────────────────────────────────────────────

class ChunkSnapshot(BaseModel):
    """One retrieved chunk stored at escalation time."""
    document_id: str = ""
    text: str = ""
    title: str = ""
    source: str = ""
    score: float = 0.0
    page_number: Optional[int] = None


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# List item (summary view for GET /grievance/pending)
# ─────────────────────────────────────────────────────────────────────────────

class GrievanceSummary(BaseModel):
    query_id: str = Field(..., examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    query_text: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    contact: Optional[ContactInfo] = None
    bot_answer: Optional[str] = None
    retrieval_score: Optional[float] = None
    llm_confidence_label: Optional[str] = None
    combined_score: Optional[float] = None
    mode: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Full detail (GET /grievance/{query_id})
# ─────────────────────────────────────────────────────────────────────────────

class GrievanceDetail(BaseModel):
    query_id: str
    query_text: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    contact: Optional[ContactInfo] = None
    bot_answer: Optional[str] = None
    retrieved_chunks: list[ChunkSnapshot] = Field(default_factory=list)
    retrieval_score: Optional[float] = None
    llm_confidence_label: Optional[str] = None
    combined_score: Optional[float] = None
    mode: Optional[str] = None
    status: str
    officer_reply: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /grievance/{query_id}/status
# ─────────────────────────────────────────────────────────────────────────────

class StatusUpdateRequest(BaseModel):
    status: str = Field(
        ...,
        description="New status.  Allowed: in_progress (claim the query to prevent duplication).",
        examples=["in_progress"],
    )


class StatusUpdateResponse(BaseModel):
    query_id: str
    status: str
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# POST /grievance/{query_id}/reply
# ─────────────────────────────────────────────────────────────────────────────

class OfficerReplyRequest(BaseModel):
    reply: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="The officer's final answer to the escalated query.",
        examples=["Registration is done online at ccs.bihar.gov.in under Kisan Panjikaran. You will need your Aadhaar number and land records. Please visit the portal for the current process."],
    )


class OfficerReplyResponse(BaseModel):
    query_id: str
    status: str
    message: str
