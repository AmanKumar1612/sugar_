import re
import unicodedata


class QueryProcessor:
    """
    Normalise a raw user query before embedding and retrieval.
    Goals:
      - Collapse excess whitespace
      - Normalise unicode (NFC)
      - Strip leading/trailing whitespace
    Intentionally keeps the original casing so the embedding model
    can use capitalisation as a signal.
    """

    @staticmethod
    def normalize_query(question: str) -> str:
        # Unicode NFC normalisation (handles accented chars, full-width, etc.)
        question = unicodedata.normalize("NFC", question)

        # Collapse multiple spaces/tabs/newlines into a single space
        question = re.sub(r"\s+", " ", question)

        return question.strip()
