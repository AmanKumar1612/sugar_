import logging
from uuid import uuid4

from app.services.ingestion.chunker import PageChunk
from app.services.ingestion.embeddings import EmbeddingService
from app.services.ingestion.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class IndexingService:

    @staticmethod
    def index_chunks(
        document_id: str,
        chunks: list[str],
        title: str,
        source_type: str,
        source_url: str | None = None,
        scope: str = "public",
    ) -> int:
        """
        Embed each plain-text chunk and upsert into Qdrant.
        Legacy interface — no page number metadata.

        Returns the number of chunks successfully indexed.
        """
        page_chunks = [
            PageChunk(page_number=0, text=c) for c in chunks
        ]
        return IndexingService.index_page_chunks(
            document_id=document_id,
            page_chunks=page_chunks,
            title=title,
            source_type=source_type,
            source_url=source_url,
            scope=scope,
        )

    @staticmethod
    def index_page_chunks(
        document_id: str,
        page_chunks: list[PageChunk],
        title: str,
        source_type: str,
        source_url: str | None = None,
        scope: str = "public",
        collection_override: str | None = None,
    ) -> int:
        """
        Embed each PageChunk and upsert into Qdrant with full metadata including:
        - page_number (for citation support)
        - scope (for role-based access filtering)
        - source_file_url (for PDF jump-to-page links)

        collection_override: use a different Qdrant collection (ephemeral sessions).
        Returns the number of chunks successfully indexed.
        """
        indexed = 0
        failed = 0
        collection = collection_override or QdrantService.COLLECTION_NAME

        for index, page_chunk in enumerate(page_chunks):
            if not page_chunk.text.strip():
                continue

            try:
                vector = EmbeddingService.encode(page_chunk.text)
            except Exception:
                logger.exception(
                    "Embedding failed for document %s chunk %d", document_id, index
                )
                failed += 1
                continue

            if not vector:
                logger.warning(
                    "Empty embedding returned for document %s chunk %d",
                    document_id,
                    index,
                )
                failed += 1
                continue

            payload = {
                "document_id": document_id,
                "chunk_id": f"chunk-{index}",
                "text": page_chunk.text,
                "title": title,
                "source_type": source_type,
                "source_url": source_url,
                # Citation fields
                "page_number": page_chunk.page_number,
                "source_file_url": source_url,   # same URL for PDFs; frontend appends #page=N
                # Access control
                "scope": scope,
            }

            try:
                if collection_override:
                    # Insert into the override collection directly
                    from qdrant_client.models import PointStruct
                    QdrantService.client.upsert(
                        collection_name=collection,
                        points=[
                            PointStruct(
                                id=str(uuid4()),
                                vector=vector,
                                payload=payload,
                            )
                        ],
                    )
                else:
                    QdrantService.insert_chunk(
                        point_id=str(uuid4()),
                        vector=vector,
                        payload=payload,
                    )
                indexed += 1
            except Exception:
                logger.exception(
                    "Qdrant upsert failed for document %s chunk %d", document_id, index
                )
                failed += 1

        logger.info(
            "Indexing complete for document %s: %d indexed, %d failed.",
            document_id,
            indexed,
            failed,
        )
        return indexed
