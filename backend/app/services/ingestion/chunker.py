from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.ingestion.pdf_ingestor import PageText

# Single shared instance — RecursiveCharacterTextSplitter is stateless
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
)


@dataclass
class PageChunk:
    """A text chunk with its originating page number."""
    page_number: int   # 1-based
    text: str


class Chunker:

    @staticmethod
    def split(text: str) -> list[str]:
        """Split plain text into chunks (legacy interface)."""
        return _splitter.split_text(text)

    @staticmethod
    def split_pages(pages: list[PageText]) -> list[PageChunk]:
        """
        Split a list of per-page texts into chunks while preserving
        the source page number for each chunk.
        Each page's text is split independently so chunks never span
        page boundaries, which makes page-accurate citations reliable.
        """
        result: list[PageChunk] = []
        for page in pages:
            if not page.text.strip():
                continue
            sub_chunks = _splitter.split_text(page.text)
            for chunk_text in sub_chunks:
                if chunk_text.strip():
                    result.append(PageChunk(page_number=page.page_number, text=chunk_text))
        return result
