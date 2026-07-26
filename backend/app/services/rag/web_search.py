import logging
from dataclasses import dataclass, field

from tavily import TavilyClient

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


@dataclass
class WebSearchResult:
    context: str = ""
    sources: list[dict] = field(default_factory=list)


class WebSearch:

    @staticmethod
    def search(question: str) -> WebSearchResult:
        """
        Perform a web search.
        Returns a WebSearchResult with context string and structured sources list.
        Both are empty on failure so callers degrade gracefully.
        """
        try:
            response = _client.search(
                query=question,
                search_depth="advanced",
                max_results=5,
            )

            results = response.get("results", [])
            parts: list[str] = []
            sources: list[dict] = []

            for result in results:
                title   = result.get("title", "")
                content = result.get("content", "")
                url     = result.get("url", "")

                parts.append(f"Title: {title}")
                parts.append(f"Content: {content}")
                parts.append(f"URL: {url}")
                parts.append("")

                if url:
                    sources.append({"title": title or url, "url": url})

            context = "\n".join(parts).strip()
            logger.debug("WebSearch returned %d results for: %s", len(results), question)
            return WebSearchResult(context=context, sources=sources)

        except Exception:
            logger.exception("Tavily web search failed for query: %s", question)
            return WebSearchResult()
