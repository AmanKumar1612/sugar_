import logging
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):

    # =====================================================
    # APP
    # =====================================================

    APP_NAME: str = "Sugarcane Dept Chatbot"

    ENV: str = "development"

    DEBUG: bool = True


    # =====================================================
    # DATABASE
    # =====================================================

    DATABASE_URL: str


    # =====================================================
    # JWT
    # =====================================================

    JWT_SECRET: str

    JWT_REFRESH_SECRET: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REFRESH_TOKEN_EXPIRE_DAYS: int = 30


    # =====================================================
    # GEMINI
    # =====================================================

    GEMINI_API_KEY: str

    GEMINI_MODEL: str = "gemini-2.5-flash"


    # =====================================================
    # EMBEDDING MODEL
    # =====================================================

    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"


    # =====================================================
    # TAVILY
    # =====================================================

    TAVILY_API_KEY: str


    # =====================================================
    # QDRANT
    # =====================================================

    QDRANT_URL: str

    QDRANT_API_KEY: str

    QDRANT_COLLECTION: str = "sugarcane_documents"


    # =====================================================
    # EMAIL
    # =====================================================

    RESEND_API_KEY: str = ""

    EMAIL_FROM: str = ""


    # =====================================================
    # GOOGLE LOGIN (admin sign-in, optional)
    # =====================================================

    GOOGLE_CLIENT_ID: str = ""

    GOOGLE_CLIENT_SECRET: str = ""


    # =====================================================
    # FRONTEND
    # =====================================================

    FRONTEND_URL: str = "http://localhost:3000"

    # Comma-separated list of allowed CORS origins.
    # e.g. "http://localhost:3000,https://app.example.com"
    ALLOWED_ORIGINS: str = "http://localhost:3000"


    # =====================================================
    # ADMIN BOOTSTRAP
    # =====================================================

    DEFAULT_ADMIN_EMAIL: str = ""

    DEFAULT_ADMIN_PASSWORD: str = ""

    # =====================================================
    # SEARCH MODE
    # kb_only     — use only Qdrant knowledge base
    # web_only    — use only Tavily web search
    # hybrid      — KB first, fall back to web (default)
    # =====================================================

    SEARCH_MODE: str = "hybrid"

    # =====================================================
    # CONFIDENCE THRESHOLDS
    # Tune these to adjust escalation sensitivity.
    # retrieval_score: avg cosine similarity (0–1) below
    #   which retrieval is considered insufficient.
    # llm_low_labels: comma-separated LLM self-check
    #   labels treated as low confidence.
    # combined_low_threshold: combined score (0–1) below
    #   which the query is escalated to an officer.
    # =====================================================

    CONFIDENCE_RETRIEVAL_LOW: float = 0.55
    CONFIDENCE_COMBINED_LOW: float = 0.45
    CONFIDENCE_LLM_LOW_LABELS: str = "low,no_answer"

    # =====================================================
    # SEMANTIC CACHE
    # similarity_threshold: cosine sim (0–1) above which
    #   a cached answer is considered a match.
    # ttl_seconds: how long a cache entry lives.
    # max_size: max number of entries in memory cache.
    # =====================================================

    CACHE_ENABLED: bool = True
    CACHE_SIMILARITY_THRESHOLD: float = 0.92
    CACHE_TTL_SECONDS: int = 3600
    CACHE_MAX_SIZE: int = 500

    # =====================================================
    # RATE LIMITING (slowapi / in-memory)
    # public_chat_rate: e.g. "10/minute"
    # admin_rate: e.g. "60/minute"
    # =====================================================

    PUBLIC_CHAT_RATE_LIMIT: str = "10/minute"
    ADMIN_RATE_LIMIT: str = "60/minute"

    # =====================================================
    # AD-HOC PDF (ephemeral, session-scoped)
    # max file size in bytes for ad-hoc uploads
    # =====================================================

    ADHOC_PDF_MAX_BYTES: int = 20_971_520  # 20 MB

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string to list."""
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
