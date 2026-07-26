from typing import Optional, Literal
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    title: str
    source_type: str
    source_url: Optional[str] = None
    file_name: Optional[str] = None
    chunk_count: Optional[int] = None
    status: str = "INDEXED"
    scope: str = "public"

    model_config = {"from_attributes": True}


class DocumentScopeRequest(BaseModel):
    """Used to update the scope of an existing document."""
    scope: Literal["public", "admin"]


class KBStatsResponse(BaseModel):
    total_documents: int
    total_pdfs: int
    total_websites: int
    total_chunks: int
    public_documents: int
    admin_documents: int
    public_chunks: int
    admin_chunks: int
