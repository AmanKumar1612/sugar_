import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class QdrantService:

    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        timeout=60,  # Qdrant Cloud free-tier clusters can cold-start; give them room to wake up
    )

    COLLECTION_NAME: str = settings.QDRANT_COLLECTION

    # Dimensionality of gemini-embedding-001 vectors
    VECTOR_SIZE: int = 3072

    @classmethod
    def create_collection(cls) -> None:
        """Create the Qdrant collection if it does not already exist."""
        collections = cls.client.get_collections()
        existing = {c.name for c in collections.collections}

        if cls.COLLECTION_NAME not in existing:
            cls.client.create_collection(
                collection_name=cls.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=cls.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Qdrant collection '%s' created.", cls.COLLECTION_NAME)
        else:
            logger.debug("Qdrant collection '%s' already exists.", cls.COLLECTION_NAME)

        # Qdrant requires an explicit payload index before you can filter on a
        # field (build_scope_filter filters on "scope"; delete_document_chunks
        # filters on "document_id"). create_payload_index is idempotent — safe
        # to call even if the index already exists.
        for field_name in ("scope", "document_id"):
            try:
                cls.client.create_payload_index(
                    collection_name=cls.COLLECTION_NAME,
                    field_name=field_name,
                    field_schema="keyword",
                )
                logger.debug("Payload index ensured for field '%s'.", field_name)
            except Exception:
                logger.exception(
                    "Failed to create payload index for field '%s' — filtering "
                    "on this field will fail until this is resolved.",
                    field_name,
                )
    @classmethod
    def insert_chunk(
        cls,
        point_id: str,
        vector: list[float],
        payload: dict,
    ) -> None:
        """Upsert one document chunk vector into Qdrant."""
        cls.client.upsert(
            collection_name=cls.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    @classmethod
    def delete_document_chunks(cls, document_id: str) -> None:
        """Delete all vectors belonging to the given document."""
        cls.client.delete(
            collection_name=cls.COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )
        logger.info(
            "Deleted all Qdrant chunks for document_id=%s.", document_id
        )

    @classmethod
    def build_scope_filter(cls, scope: str) -> Filter | None:
        """
        Build a Qdrant Filter for scope-based access control.

        scope="public"  → only chunks where payload.scope == "public"
        scope="admin"   → no filter (admin sees public + admin chunks)
        """
        if scope == "admin":
            return None  # admin sees everything
        # public → only public chunks
        return Filter(
            must=[
                FieldCondition(
                    key="scope",
                    match=MatchValue(value="public"),
                )
            ]
        )
