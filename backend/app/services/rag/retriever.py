import logging

from app.core.config import settings
from app.services.ingestion.embeddings import EmbeddingService
from app.services.ingestion.qdrant_service import QdrantService
from app.services.rag.query_processor import QueryProcessor

logger = logging.getLogger(__name__)

# Minimum cosine similarity score to include a chunk (0.0 – 1.0)
_SCORE_THRESHOLD = 0.5


class Retriever:

    @staticmethod
    def search(
        question: str,
        limit: int = 5,
        scope: str = "public",
        collection_override: str | None = None,
    ) -> list[dict]:
        """
        Embed the question and retrieve the most relevant chunks from Qdrant.

        Args:
            question: the user's query (already slang-expanded).
            limit: max number of chunks to return.
            scope: "public" (only public chunks) or "admin" (all chunks).
            collection_override: query a temporary/session collection instead.

        Returns a list of chunk dicts:
            {
                "document_id": str,
                "text": str,
                "title": str,
                "source": str,        # URL or filename
                "score": float,
                "page_number": int,   # 1-based; 0 if not page-aware
                "source_file_url": str | None,
                "scope": str,
            }
        """
        # Embed the query
        try:
            normalised = QueryProcessor.normalize_query(question)
            vector = EmbeddingService.encode(normalised)
            if vector is None:
                logger.warning("Query embedding returned empty for: %s", question)
                return []
        except Exception:
            logger.exception("Embedding failed for query: %s", question)
            return []

        # Build scope filter (None means no filter = admin sees everything)
        query_filter = QdrantService.build_scope_filter(scope)
        collection = collection_override or QdrantService.COLLECTION_NAME

        # Query Qdrant
        try:
            results = QdrantService.client.query_points(
                collection_name=collection,
                query=vector,
                limit=limit,
                with_payload=True,
                score_threshold=_SCORE_THRESHOLD,
                query_filter=query_filter,
            )
        except Exception:
            logger.exception("Qdrant query failed for query: %s", question)
            return []

        if not results.points:
            logger.debug("No Qdrant results above threshold for: %s", question)
            return []

        chunks: list[dict] = []
        for point in results.points:
            payload = point.payload or {}

            source = (
                payload.get("source_url")
                or payload.get("source_file_url")
                or payload.get("file_name")
                or payload.get("title")
                or ""
            )

            chunks.append(
                {
                    "document_id": payload.get("document_id", ""),
                    "text": payload.get("text", ""),
                    "title": payload.get("title", ""),
                    "source": source,
                    "score": round(point.score, 4),
                    "page_number": payload.get("page_number", 0),
                    "source_file_url": payload.get("source_file_url"),
                    "scope": payload.get("scope", "public"),
                }
            )

        logger.debug(
            "Retriever found %d chunks (scope=%s) for query: %s",
            len(chunks),
            scope,
            question,
        )
        return chunks