"""
Pydantic schemas for admin-facing chat endpoints.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    """Page-accurate citation metadata for admin responses."""
    document_name: str = ""
    page_number: Optional[int] = None
    source_file_url: Optional[str] = None
    jump_url: Optional[str] = Field(
        default=None,
        description="Direct URL compatible with PDF.js: source_file_url#page=N",
        examples=["https://storage.example.com/mukhyamantri-ganna-vikas-yojana.pdf#page=3"],
    )
    chunk_text_snippet: str = ""


class SourceResponse(BaseModel):
    title: str
    url: str


class AdminChatRequest(BaseModel):
    """
    Body for POST /admin/chat/query.
    Admins can choose mode and see citations.
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        examples=["What is the eligibility criteria for the gur license scheme?"],
    )
    history: str = Field(
        default="",
        max_length=8000,
        description="Last N conversation turns.",
    )
    mode: Literal["kb_only", "web_only", "hybrid"] = Field(
        default="hybrid",
        description="Retrieval mode: kb_only / web_only / hybrid",
    )
    chat_id: Optional[str] = Field(
        default=None,
        description="Existing admin chat session ID (optional, for history persistence).",
    )


class AdminChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse] = Field(default_factory=list)
    citations: list[CitationResponse] = Field(default_factory=list)
    retrieval_score: float = 0.0
    llm_confidence_label: str = ""
    combined_score: float = 0.0
    escalated: bool = False
    query_id: Optional[str] = Field(
        default=None,
        description="Set when escalated=True; use GET /admin/grievance/{query_id}/status to poll.",
    )


class AdHocPDFQueryRequest(BaseModel):
    """For querying an ad-hoc (session-scoped, ephemeral) PDF."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        examples=["Summarise the key findings of this document."],
    )
    history: str = Field(default="", max_length=8000)
    session_collection: str = Field(
        ...,
        description="The ephemeral Qdrant collection name returned by POST /admin/documents/adhoc-upload.",
        examples=["adhoc-abc12345"],
    )


class AdHocPDFQueryResponse(BaseModel):
    answer: str
    citations: list[CitationResponse] = Field(default_factory=list)


class AdHocPromoteRequest(BaseModel):
    """Promote an ephemeral collection to the permanent KB."""
    session_collection: str = Field(
        ...,
        description="Collection name returned by adhoc-upload.",
    )
    scope: Literal["public", "admin"] = Field(
        default="admin",
        description="Scope for the permanent KB entry.",
    )
    title: Optional[str] = Field(
        default=None,
        description="Document title override.  If omitted, the original filename is used.",
    )


class AdHocPromoteResponse(BaseModel):
    document_id: str
    message: str
    chunks: int
