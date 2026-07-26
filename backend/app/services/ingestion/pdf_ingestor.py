import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    """Text extracted from a single PDF page."""
    page_number: int          # 1-based
    text: str


class PDFIngestor:

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract all text from a PDF file as a single string.
        Used by the legacy pipeline.
        Returns an empty string if the file cannot be read.
        """
        try:
            with fitz.open(file_path) as doc:
                text = "\n".join(page.get_text() for page in doc)
            return text
        except Exception:
            logger.exception("Failed to extract text from PDF: %s", file_path)
            return ""

    @staticmethod
    def extract_pages(file_path: str) -> list[PageText]:
        """
        Extract text per page, preserving 1-based page numbers.
        Returns a list of PageText objects (one per non-empty page).
        Used by the page-aware ingestion pipeline (section 5 citation support).
        """
        pages: list[PageText] = []
        try:
            with fitz.open(file_path) as doc:
                for i, page in enumerate(doc, start=1):
                    text = page.get_text().strip()
                    if text:
                        pages.append(PageText(page_number=i, text=text))
        except Exception:
            logger.exception("Failed to extract pages from PDF: %s", file_path)
        return pages
