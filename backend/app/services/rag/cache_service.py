"""
SemanticCache — in-memory semantic similarity-based response cache.

Design decisions:
  - In-memory (no Redis dependency for v1).  Survives the process lifetime;
    resets on redeploy.  A Redis backend can be swapped in later if needed.
  - Lookup: embed the incoming query and compute cosine similarity against all
    cached query vectors.  If the best match exceeds CACHE_SIMILARITY_THRESHOLD
    the cached response is returned without hitting the LLM.
  - Invalidation strategy chosen: TTL + explicit invalidation on officer reply.
    When /grievance/{query_id}/reply is called the cache entry for that query
    is deleted so the next identical question re-runs through the full pipeline
    (and may now get a high-confidence answer or find the officer reply).
  - Thread safety: a simple threading.Lock guards reads/writes (FastAPI runs
    in a single process with async handlers + background threads).
  - Cache key: (query_text, mode, scope) — different modes or scopes must not
    share entries.
"""

import logging
import math
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    query_text: str
    query_vector: list[float]
    response: dict          # the full RAGService response dict
    mode: str
    scope: str
    created_at: float = field(default_factory=time.time)
    query_id: str | None = None  # linked escalated_query.id if this was escalated


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class SemanticCache:
    """
    Thread-safe, in-memory semantic cache.
    Instantiate once (module-level singleton below).
    """

    def __init__(
        self,
        similarity_threshold: float = 0.92,
        ttl_seconds: int = 3600,
        max_size: int = 500,
        enabled: bool = True,
    ) -> None:
        self._threshold = similarity_threshold
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._enabled = enabled
        self._entries: list[CacheEntry] = []
        self._lock = threading.Lock()

    def _is_expired(self, entry: CacheEntry) -> bool:
        return (time.time() - entry.created_at) > self._ttl

    def _evict_expired(self) -> None:
        """Remove all expired entries (must be called with lock held)."""
        self._entries = [e for e in self._entries if not self._is_expired(e)]

    def lookup(
        self,
        query_vector: list[float],
        mode: str,
        scope: str,
    ) -> dict | None:
        """
        Return a cached response dict if a sufficiently similar query exists,
        otherwise return None.
        """
        if not self._enabled:
            return None

        with self._lock:
            self._evict_expired()
            best_score = -1.0
            best_entry: CacheEntry | None = None

            for entry in self._entries:
                if entry.mode != mode or entry.scope != scope:
                    continue
                score = _cosine_similarity(query_vector, entry.query_vector)
                if score > best_score:
                    best_score = score
                    best_entry = entry

            if best_entry is not None and best_score >= self._threshold:
                logger.debug(
                    "Cache HIT (similarity=%.4f, mode=%s, scope=%s)",
                    best_score,
                    mode,
                    scope,
                )
                return best_entry.response

        logger.debug("Cache MISS (best_similarity=%.4f)", best_score)
        return None

    def store(
        self,
        query_text: str,
        query_vector: list[float],
        response: dict,
        mode: str,
        scope: str,
        query_id: str | None = None,
    ) -> None:
        """Store a new cache entry."""
        if not self._enabled:
            return

        with self._lock:
            self._evict_expired()
            # Enforce max size — drop oldest entries first
            while len(self._entries) >= self._max_size:
                self._entries.pop(0)

            self._entries.append(
                CacheEntry(
                    query_text=query_text,
                    query_vector=query_vector,
                    response=response,
                    mode=mode,
                    scope=scope,
                    query_id=query_id,
                )
            )
            logger.debug("Cache STORE (mode=%s, scope=%s, size=%d)", mode, scope, len(self._entries))

    def invalidate_by_query_id(self, query_id: str) -> int:
        """
        Remove cache entries associated with an escalated query ID.
        Called when an officer submits a reply so the next identical question
        bypasses the cache and re-runs the full pipeline.
        Returns number of entries removed.
        """
        with self._lock:
            before = len(self._entries)
            self._entries = [e for e in self._entries if e.query_id != query_id]
            removed = before - len(self._entries)
        if removed:
            logger.info("Cache invalidated %d entries for query_id=%s", removed, query_id)
        return removed

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


# ── Module-level singleton (initialised lazily from settings) ────────────────

_cache: SemanticCache | None = None


def get_cache() -> SemanticCache:
    """Return the module-level SemanticCache singleton, creating it if needed."""
    global _cache
    if _cache is None:
        from app.core.config import settings
        _cache = SemanticCache(
            similarity_threshold=settings.CACHE_SIMILARITY_THRESHOLD,
            ttl_seconds=settings.CACHE_TTL_SECONDS,
            max_size=settings.CACHE_MAX_SIZE,
            enabled=settings.CACHE_ENABLED,
        )
    return _cache
