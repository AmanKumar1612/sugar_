import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

_REMOVE_TAGS = {"script", "style", "noscript", "header", "footer", "nav", "aside"}


class WebsiteIngestor:

    @staticmethod
    def extract_text(url: str) -> str:
        """
        Fetch a URL and extract clean body text.
        Raises requests.HTTPError on non-2xx responses.
        Returns empty string if parsing fails.
        """
        response = requests.get(url, headers=_HEADERS, timeout=30)
        response.raise_for_status()

        # Honour the content-type charset; fall back to apparent encoding
        response.encoding = response.apparent_encoding or "utf-8"

        try:
            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(_REMOVE_TAGS):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            logger.debug("Extracted %d chars from %s", len(text), url)
            return text
        except Exception:
            logger.exception("Failed to parse HTML from %s", url)
            return ""
