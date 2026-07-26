"""
ConfidenceService — hybrid confidence scoring for RAG answers.

Two signals are combined:
  1. Retrieval score  — average cosine similarity of the top-K chunks returned
                        by Qdrant.  If no chunks were retrieved the score is 0.
  2. LLM self-check   — a structured sub-instruction appended to the generation
                        prompt that asks the model to rate its own confidence.
                        The model returns a JSON fragment:
                        {"confidence": "high"|"medium"|"low"|"no_answer"}
                        This is extracted from the response before it is shown
                        to the user.

Combined score  =  0.6 * retrieval_score  +  0.4 * llm_numeric_score
  where llm_numeric_score maps:
    "high"      → 1.0
    "medium"    → 0.6
    "low"       → 0.2
    "no_answer" → 0.0

If combined_score < settings.CONFIDENCE_COMBINED_LOW   → escalate
If llm_label in settings.CONFIDENCE_LLM_LOW_LABELS     → escalate
Both thresholds are checked; either failing triggers escalation.
"""

import json
import logging
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

_LLM_SCORE_MAP = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.2,
    "no_answer": 0.0,
}

# Instruction appended to the generation prompt so the model returns a
# machine-readable confidence tag in the SAME response (no extra LLM call).
CONFIDENCE_INSTRUCTION = """
--- Confidence Self-Check ---
After writing your answer above, output EXACTLY one line with this JSON and nothing else:
{"confidence": "<label>"}
where <label> is ONE of: high, medium, low, no_answer
  high      = you are confident the answer is well-supported by the retrieved context
  medium    = the answer is partially supported; some uncertainty remains
  low       = the retrieved context is weak or tangential; answer may be inaccurate
  no_answer = the context does not support an answer at all
Do NOT include any other text after this JSON line.
"""

# Regex to find the JSON confidence tag anywhere in the response
_CONFIDENCE_RE = re.compile(
    r'\{["\s]*confidence["\s]*:["\s]*(high|medium|low|no_answer)["\s]*\}',
    re.IGNORECASE,
)


def parse_confidence_from_response(raw_response: str) -> tuple[str, str]:
    """
    Split the LLM response into (clean_answer, confidence_label).

    Strips the JSON confidence line from the answer the user sees.
    Falls back to "low" if no confidence tag is found.
    """
    match = _CONFIDENCE_RE.search(raw_response)
    if match:
        label = match.group(1).lower()
        # Remove the confidence JSON line from the visible answer
        clean = _CONFIDENCE_RE.sub("", raw_response).strip()
        # Also strip any trailing "--- Confidence Self-Check ---" header that
        # might have leaked into the answer portion.
        clean = re.sub(r"---\s*Confidence Self-Check\s*---.*", "", clean, flags=re.DOTALL).strip()
        return clean, label

    logger.debug("No confidence tag found in LLM response; defaulting to 'low'.")
    return raw_response.strip(), "low"


def compute_retrieval_score(chunks: list[dict]) -> float:
    """Average similarity score of retrieved chunks (0.0 if no chunks)."""
    if not chunks:
        return 0.0
    scores = [c.get("score", 0.0) for c in chunks]
    return round(sum(scores) / len(scores), 4)


def compute_combined_score(retrieval_score: float, llm_label: str) -> float:
    """Weighted combination of retrieval and LLM confidence signals."""
    llm_numeric = _LLM_SCORE_MAP.get(llm_label, 0.0)
    combined = 0.6 * retrieval_score + 0.4 * llm_numeric
    return round(combined, 4)


def should_escalate(retrieval_score: float, llm_label: str, combined_score: float) -> bool:
    """
    Return True if the query should be escalated to an officer.

    Either the combined numeric score is too low OR the LLM explicitly
    rated the answer as insufficient.
    """
    low_labels = {
        lbl.strip().lower()
        for lbl in settings.CONFIDENCE_LLM_LOW_LABELS.split(",")
        if lbl.strip()
    }
    if llm_label.lower() in low_labels:
        return True
    if combined_score < settings.CONFIDENCE_COMBINED_LOW:
        return True
    return False
