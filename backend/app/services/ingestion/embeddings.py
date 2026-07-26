import logging

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

# Reuse one Gemini client for the lifetime of the process
_client = genai.Client(
    api_key=settings.GEMINI_API_KEY,
    http_options=types.HttpOptions(api_version="v1"),
)


class EmbeddingService:

    @classmethod
    def encode(cls, text: str) -> list[float] | None:
        """
        Generate a dense embedding vector for the given text.

        Returns the float list on success, or None if the API returns empty.
        Raises on hard API errors so callers can decide whether to retry.
        """
        if not text.strip():
            logger.warning("EmbeddingService.encode received blank text.")
            return None

        response = _client.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=text,
        )

        if not response.embeddings:
            logger.warning("Gemini embedding API returned empty embeddings.")
            return None

        return response.embeddings[0].values
