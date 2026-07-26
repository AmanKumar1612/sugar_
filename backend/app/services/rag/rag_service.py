"""
RAGService — dual-mode RAG engine for the Sugarcane Industries Department,
Government of Bihar chatbot.

Key changes over v1:
  - scope-aware retrieval (public vs admin)
  - retrieval mode toggle: kb_only / web_only / hybrid
  - hybrid confidence scoring (retrieval + LLM self-check)
  - citation metadata generation (page-accurate, admin-only exposure)
  - semantic response cache
  - concise answer enforcement (system prompt + max_tokens)

The service does NOT touch the database.  Escalation persistence is handled
by the calling API layer (see app/api/public_chat.py and app/api/admin_chat.py).
"""

import logging
import re
from urllib.parse import urlparse
from app.services.ingestion.embeddings import EmbeddingService
from google import genai

from app.core.config import settings
from app.services.rag.query_processor import QueryProcessor
from app.services.rag.retriever import Retriever
from app.services.rag.web_search import WebSearch
from app.services.rag.confidence_service import (
    CONFIDENCE_INSTRUCTION,
    compute_combined_score,
    compute_retrieval_score,
    parse_confidence_from_response,
    should_escalate,
)
from app.services.rag.cache_service import get_cache

logger = logging.getLogger(__name__)

_gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

_MIN_KB_CHUNKS = 2

# ─────────────────────────────────────────────────────────────────────────────
# Common internet slang / abbreviations → expand before topic check
# ─────────────────────────────────────────────────────────────────────────────
_SLANG_MAP = {
    r"\bu\b":           "you",
    r"\bidk\b":         "I do not know",
    r"\bwdym\b":        "what do you mean",
    r"\bwdm\b":         "what do you mean",
    r"\bpls\b":         "please",
    r"\bplz\b":         "please",
    r"\binfo\b":        "information",
    r"\buni\b":         "university",
    r"\bhist\b":        "history",
    r"\bbro\b":         "friend",
    r"\btbh\b":         "to be honest",
    r"\brn\b":          "right now",
    r"\basap\b":        "as soon as possible",
    r"\bomg\b":         "oh my god",
    r"\blmk\b":         "let me know",
    r"\bbtw\b":         "by the way",
    r"\bfyi\b":         "for your information",
    r"\bngl\b":         "not going to lie",
    r"\bimo\b":         "in my opinion",
    r"\bafaik\b":       "as far as I know",
    r"\btysm\b":        "thank you so much",
    r"\bty\b":          "thank you",
    r"\bnp\b":          "no problem",
    r"\bthx\b":         "thanks",
    r"\bthnx\b":        "thanks",
    r"\bokk\b":         "okay",
    r"\bwat\b":         "what",
    r"\bwht\b":         "what",
    r"\bhw\b":          "how",
    r"\byr\b":          "year",
    r"\btelme\b":       "tell me",
    r"\btell me abt\b": "tell me about",
    r"\babt\b":         "about",
    r"\bsmth\b":        "something",
    r"\bsomewhr\b":     "somewhere",
    r"\bkno\b":         "know",
    r"\bknow abt\b":    "know about",
    r"\bgana\b":        "ganna",
    r"\bganne\b":       "ganna",
    r"\bgannaa\b":      "ganna",
    r"\bkisaan\b":      "kisan",
    r"\bkishan\b":      "kisan",
    r"\bregistr\b":     "registration",
    r"\bpanjikaran\b":  "registration",
    r"\byojna\b":       "yojana",
    r"\byojanaa\b":     "yojana",
    r"\bgud\b":         "gur",
    r"\bjaggary\b":     "jaggery",
    r"\bmil\b":         "mill",
}


def _expand_slang(text: str) -> str:
    for pattern, replacement in _SLANG_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Topic keywords — Sugarcane Industries Department, Govt. of Bihar (ccs.bihar.gov.in)
# Includes English, Hindi (Devanagari), and Hinglish (Romanized Hindi) terms so
# the guard doesn't false-block genuine farmer queries typed in any of the three.
# ─────────────────────────────────────────────────────────────────────────────
_SUGARCANE_KEYWORDS = re.compile(
    r"ganna|sugarcane|sugar cane|cane\b|"
    r"गन्ना|"
    r"kisan|farmer|किसान|"
    r"registration|panjikaran|पंजीकरण|पंजीयन|"
    r"yojana|scheme|योजना|"
    r"mukhyamantri|मुख्यमंत्री|mgvy|"
    r"gur\b|jaggery|गुड़|khandsari|खांडसारी|"
    r"license|licence|लाइसेंस|"
    r"mechanization|mechanisation|यंत्रीकरण|यांत्रिकीकरण|equipment|यंत्र|"
    r"zdc|zonal development council|क्षेत्रीय विकास परिषद|"
    r"nursery|नर्सरी|seed|बीज|"
    r"area expansion|क्षेत्र विस्तार|क्षेत्रफल|"
    r"sugar mill|चीनी मिल|मिल\b|factory|कारखाना|"
    r"cane commissioner|गन्ना आयुक्त|"
    r"subsidy|अनुदान|सब्सिडी|"
    r"sap\b|state advised price|मूल्य|price|भाव|दर|"
    r"application|आवेदन|apply|आवेदन करें|"
    r"deadline|last date|अंतिम तिथि|"
    r"eligibility|पात्रता|documents required|दस्तावेज़|"
    r"ikh mitra|इख मित्र|app\b|"
    r"fertilizer|खाद|उर्वरक|pest|कीट|disease|रोग|"
    r"irrigation|सिंचाई|crop|फसल|"
    r"cultivation|खेती|farming|कृषि|"
    r"office|कार्यालय|contact|संपर्क|phone|फ़ोन|"
    r"complaint|शिकायत|grievance|अधिकारी|officer|"
    r"payment|भुगतान|bank|बैंक|account|खाता|"
    r"status|स्थिति|track|ट्रैक",
    re.IGNORECASE,
)

_FOLLOWUP_PATTERNS = re.compile(
    r"^("
    r"in which|which year|what year|when was|when did|who was|who did|"
    r"how many|how much|how long|how far|"
    r"tell me more|more details|more info|"
    r"and then|what about|what happened|after that|before that|"
    r"can you explain|please explain|elaborate|go on|continue|"
    r"really\??|seriously\??|wow|interesting|ok|okay|cool|got it|"
    r"yes|no|sure|please|pls|what else|anything else|"
    r"in hindi|in english|translate|repeat|again|"
    r"[\?\!\.，。\s]*"
    r")$",
    re.IGNORECASE,
)

_OFF_TOPIC_RESPONSE = (
    "मैं गन्ना उद्योग विभाग, बिहार सरकार का सहायक हूं — मैं केवल गन्ना खेती, "
    "किसान पंजीकरण, विभागीय योजनाओं, गुड़/खांडसारी, गन्ना यंत्रीकरण, "
    "चीनी मिलों और संबंधित विषयों पर आपकी मदद कर सकता हूं। कृपया इनसे जुड़ा सवाल पूछें।\n\n"
    "I'm the assistant for the Sugarcane Industries Department, Govt. of Bihar — "
    "I can only help with sugarcane cultivation, farmer registration, department "
    "schemes, gur/khandsari, cane mechanization, sugar mills, and related topics. "
    "Please ask something related to these."
)

# ─────────────────────────────────────────────────────────────────────────────
# System prompt — concise by design
# ─────────────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are the official AI assistant for the Sugarcane Industries Department
(गन्ना उद्योग विभाग), Government of Bihar (ccs.bihar.gov.in). Your primary users are
sugarcane farmers across Bihar asking about registration, government schemes, and services.

YOU CAN ANSWER QUESTIONS ABOUT:
- गन्ना किसान पंजीकरण (farmer/Kisan registration) — process, eligibility, documents required
- मुख्यमंत्री गन्ना विकास योजना (Mukhyamantri Ganna Vikas Yojana) and other cane development schemes
- गुड़ लाइसेंस / गुड़ इकाई योजना (jaggery/gur license and unit schemes)
- गन्ना यंत्रीकरण योजना (cane mechanization scheme) — equipment, subsidies
- क्षेत्रीय विकास परिषद / ZDC — regulation of cane supply and purchase
- गन्ना फसल क्षेत्र विस्तार कार्यक्रम and गन्ना नर्सरी योजना (cane area expansion & nursery schemes)
- Sugar mills in Bihar — locations, contact details
- Cultivation guidance: seeds, fertilizers, irrigation, common pests/diseases (general awareness only —
  do not give specific pesticide dosages; direct farmers to a Kisan Salahkar / agriculture officer for that)
- Application deadlines, scheme status, and how/where to apply or register
- Department contact details and how to reach an officer for unresolved issues

STRICT RULES:
1. ONLY answer questions about sugarcane farming, department schemes, and the topics listed above.
2. LANGUAGE RULE: Reply in the SAME language/script the farmer used — Hindi (Devanagari), Hinglish
   (Romanized Hindi), or English. If mixed, mirror the dominant language. Never force English on a
   Hindi query or vice versa.
3. FOLLOW-UP RULE: If conversation history is about a scheme or topic above, treat natural follow-ups
   ("iske liye kya document chahiye", "last date kya hai") as related to that same topic.
4. Never fabricate scheme names, deadlines, amounts, phone numbers, or eligibility criteria — if the
   knowledge base and web context don't have it, say so plainly rather than guessing.
5. SLANG/SPELLING RULE: Handle common typos, abbreviations, and Hinglish spelling variants gracefully.
6. OFF-TOPIC RULE: Politely decline clearly unrelated questions (politics, entertainment, other
   departments/states, general trivia) and redirect the farmer to ask about sugarcane/department topics.
7. Be CONCISE — direct, factual answers in 3–5 sentences unless the farmer needs a step list (e.g.
   registration steps), in which case use a short numbered list. Avoid padding and filler.
8. Use retrieved knowledge-base context as the primary source; web search as fallback; your own general
   knowledge only when both are insufficient — and say so if you're relying on general knowledge."""


def _source_label(url: str) -> str:
    if not url:
        return "Source"
    host = urlparse(url).netloc.replace("www.", "").lower()
    if "ccs.bihar.gov.in" in host:
        return "Sugarcane Industries Dept, Bihar"
    if "bihar.gov.in" in host or "bihar" in host:
        return "Bihar Government"
    if "sugarcanemech" in host:
        return "Cane Mechanization Portal"
    if "wikipedia" in host:
        return "Wikipedia"
    return host or "Source"


def _normalise_url(raw: str) -> str | None:
    if not raw:
        return None
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def _deduplicate_sources(raw_sources: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for src in raw_sources:
        url = _normalise_url(src.get("url", ""))
        if not url or url in seen:
            continue
        seen.add(url)
        title = src.get("title") or _source_label(url)
        result.append({"title": title, "url": url})
    return result


def _is_domain_related(question: str, kb_hits: int, history: str = "") -> bool:
    expanded = _expand_slang(question)
    if kb_hits >= 1:
        return True
    if _SUGARCANE_KEYWORDS.search(expanded):
        return True
    if history and _SUGARCANE_KEYWORDS.search(history):
        return True
    if _FOLLOWUP_PATTERNS.match(expanded.strip()):
        return True
    return False


def _build_citations(chunks: list[dict]) -> list[dict]:
    """
    Build structured citation objects from retrieved chunks.
    Includes page_number and source_file_url for PDF jump-to-page links.
    The source_file_url#page=N convention is compatible with PDF.js viewers.
    """
    citations: list[dict] = []
    seen: set[tuple] = set()
    for chunk in chunks:
        doc_id = chunk.get("document_id", "")
        page = chunk.get("page_number", 0)
        title = chunk.get("title", "")
        source_url = chunk.get("source_file_url") or chunk.get("source", "")
        snippet = chunk.get("text", "")[:200]

        key = (doc_id, page)
        if key in seen:
            continue
        seen.add(key)

        # Build a direct-link URL for PDF.js viewers
        jump_url: str | None = None
        if source_url and page and page > 0:
            normalised = _normalise_url(source_url) or ""
            jump_url = f"{normalised}#page={page}" if normalised else None

        citations.append(
            {
                "document_name": title,
                "page_number": page if page > 0 else None,
                "source_file_url": _normalise_url(source_url),
                "jump_url": jump_url,
                "chunk_text_snippet": snippet,
            }
        )
    return citations


class RAGService:

    @staticmethod
    def answer(
        question: str,
        history: str = "",
        mode: str = "kb_only",
        scope: str = "public",
        include_citations: bool = False,
        collection_override: str | None = None,
    ) -> dict:
        """
        Core RAG answer method.

        Args:
            question:           The user's current message.
            history:            Last N turns formatted as "User: ...\nAssistant: ..."
            mode:               "kb_only" | "web_only" | "hybrid"
            scope:              "public" | "admin"  — controls Qdrant filter
            include_citations:  If True, include citation metadata in response.
            collection_override: Query a different Qdrant collection (ephemeral PDFs).

        Returns a dict:
            {
              "answer": str,
              "sources": [...],
              "citations": [...],       # empty list if include_citations=False
              "retrieval_score": float,
              "llm_confidence_label": str,
              "combined_score": float,
              "escalate": bool,
              "retrieved_chunks": [...], # raw chunks for escalation storage
            }
        """
        # ── 1. Slang expansion ────────────────────────────────────────────────
        expanded_question = _expand_slang(question)

# ── 2. Embed the query (needed for cache lookup + retrieval) ──────────
        try:
            normalised = QueryProcessor.normalize_query(expanded_question)
            query_vector = EmbeddingService.encode(normalised) or []
        except Exception:
            logger.exception("Query embedding failed for: %s", question)
            query_vector = []

        # ── 3. Semantic cache lookup ──────────────────────────────────────────
        cache = get_cache()
        if query_vector:
            cached = cache.lookup(query_vector=query_vector, mode=mode, scope=scope)
            if cached is not None:
                return cached

        # ── 4. KB retrieval ───────────────────────────────────────────────────
        retrieved_chunks: list[dict] = []
        if mode in ("hybrid", "kb_only"):
            try:
                retrieved_chunks = Retriever.search(
                    question=expanded_question,
                    limit=5,
                    scope=scope,
                    collection_override=collection_override,
                )
            except Exception:
                logger.exception("Retriever failed for: %s", question)

        # ── 5. Topic guard ────────────────────────────────────────────────────
        # Skip topic guard for ephemeral (session-scoped) collections
        if not collection_override and not _is_domain_related(
            question, len(retrieved_chunks), history
        ):
            logger.info("Off-topic blocked: %s", question[:80])
            off_topic_result = {
                "answer": _OFF_TOPIC_RESPONSE,
                "sources": [],
                "citations": [],
                "retrieval_score": 0.0,
                "llm_confidence_label": "no_answer",
                "combined_score": 0.0,
                "escalate": False,
                "retrieved_chunks": [],
            }
            return off_topic_result

        context_parts: list[str] = []
        kb_sources: list[dict] = []

        for chunk in retrieved_chunks:
            text = chunk.get("text", "").strip()
            if text:
                context_parts.append(text)
            source_url = chunk.get("source", "")
            title      = chunk.get("title", "")
            if source_url:
                kb_sources.append({
                    "title": title or _source_label(source_url),
                    "url":   source_url,
                })

        # ── 6. Web search ─────────────────────────────────────────────────────
        web_result_sources: list[dict] = []
        web_context = ""

        use_web = (
            mode == "web_only"
            or (mode == "hybrid" and len(retrieved_chunks) < _MIN_KB_CHUNKS)
        )

        if use_web:
            logger.debug("Web search triggered (mode=%s, kb_chunks=%d).", mode, len(retrieved_chunks))
            try:
                web_result         = WebSearch.search(expanded_question)
                web_context        = web_result.context
                web_result_sources = web_result.sources
            except Exception:
                logger.exception("WebSearch failed for: %s", question)

        # ── 7. Build generation prompt ────────────────────────────────────────
        context_block = (
            "\n\n".join(context_parts)
            if context_parts
            else "No knowledge base results found."
        )

        # Confidence self-check instruction appended so we get label in same call
        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            + (f"--- Conversation History ---\n{history.strip()}\n\n" if history.strip() else "")
            + f"--- Knowledge Base Context ---\n{context_block}\n\n"
            + (f"--- Web Search Context ---\n{web_context}\n\n" if web_context else "")
            + f"--- Current Question ---\n{question}\n\n"
            "--- Answer (be concise, 3–5 sentences) ---\n"
            + CONFIDENCE_INSTRUCTION
        )

        # ── 8. Call Gemini ────────────────────────────────────────────────────
        try:
            gemini_response = _gemini_client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config={
                    "max_output_tokens": 512,
                    "temperature": 0.2,
                },
            )
            raw_answer = (gemini_response.text or "").strip()
            if not raw_answer:
                raw_answer = "no_answer_placeholder"
        except Exception:
            logger.exception("Gemini generation failed for: %s", question)
            return {
                "answer": "Sorry, the AI service encountered an error. Please try again.",
                "sources": [],
                "citations": [],
                "retrieval_score": 0.0,
                "llm_confidence_label": "low",
                "combined_score": 0.0,
                "escalate": False,
                "retrieved_chunks": retrieved_chunks,
            }

        # ── 9. Parse confidence tag from the answer ───────────────────────────
        clean_answer, llm_label = parse_confidence_from_response(raw_answer)
        if not clean_answer or clean_answer == "no_answer_placeholder":
            clean_answer = "I wasn't able to generate an answer. Please try rephrasing your question."

        # ── 10. Compute confidence scores ─────────────────────────────────────
        retrieval_score = compute_retrieval_score(retrieved_chunks)
        combined_score  = compute_combined_score(retrieval_score, llm_label)
        escalate        = should_escalate(retrieval_score, llm_label, combined_score)

        # ── 11. Build citations ───────────────────────────────────────────────
        citations = _build_citations(retrieved_chunks) if include_citations else []

        # ── 12. Merge and deduplicate sources ─────────────────────────────────
        all_sources = _deduplicate_sources(kb_sources + web_result_sources)

        result = {
            "answer": clean_answer,
            "sources": all_sources,
            "citations": citations,
            "retrieval_score": retrieval_score,
            "llm_confidence_label": llm_label,
            "combined_score": combined_score,
            "escalate": escalate,
            "retrieved_chunks": retrieved_chunks,
        }

        # ── 13. Cache (only non-escalated answers) ────────────────────────────
        if not escalate and query_vector:
            cache.store(
                query_text=question,
                query_vector=query_vector,
                response=result,
                mode=mode,
                scope=scope,
            )

        logger.debug(
            "Answer generated. KB=%d, web=%d, retrieval_score=%.3f, "
            "llm_label=%s, combined=%.3f, escalate=%s",
            len(retrieved_chunks),
            len(web_result_sources),
            retrieval_score,
            llm_label,
            combined_score,
            escalate,
        )

        return result
