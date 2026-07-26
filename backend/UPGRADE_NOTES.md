# Sugarcane Dept Chatbot — Upgrade Notes

## Changelog — Sugarcane Department rebrand & cleanup pass

The codebase originated as "NalandaGPT" (a Nalanda University chatbot) and was adapted for the
**Sugarcane Industries Department, Government of Bihar** (ccs.bihar.gov.in). This pass fixed:

- **Critical bug**: the production `RAGService.answer()` method still had a hardcoded Nalanda-only
  topic guard and system prompt — every real farmer question would have been blocked as off-topic.
  Replaced with sugarcane-domain keywords (English/Hindi/Hinglish) and a bilingual system prompt.
- **Removed dead legacy auth-gated chat**: `app/api/chat.py` and `app/api/guest.py` (and their
  repositories/schemas) were leftover from the original single-tier NalandaGPT and required login
  for chat — not compatible with the anonymous-public / authenticated-admin model this project needs.
  Deleted; `app/api/public_chat.py` is the only public chat entrypoint now, and it requires no login.
- **Frontend was not wired to the new backend**: `chat/page.jsx` and the homepage were still calling
  the old dead `/guest` and `/chat/{id}/message` endpoints instead of the real `/chat/query` +
  escalation flow. Rewired both pages, `Message.jsx`, and `MessageBubble.jsx` to use
  `services/publicChat.js`, including a contact-info form and officer-reply polling UI for escalated
  queries. Removed the public-facing Sign in/Sign up buttons and the self-serve `/register` page —
  there's no "regular user" tier in this architecture, only anonymous public + authenticated admin.
- **Removed dead config**: unused `REDIS_URL` / `NEO4J_*` / `MINIO_*` settings were defined but never
  referenced anywhere in the code — removed from `config.py` and `.env.example`.
- **Removed a hardcoded real Google OAuth Client ID** that had been left in `config.py` as a fallback
  default, and in the frontend's `.env.local` / `.env.development.local` — replaced with placeholders.
- **Removed dead files**: duplicate `sample.pdf`s, an unrelated internal SRS PDF, stray `__pycache__`
  directories with `.pyc` files for scripts that no longer exist, an irrelevant `VITE_API_URL` env var
  left over from a different frontend bootstrap.
- Rebranded strings across prompts, email templates, schema examples, and UI copy.

**Still worth doing before wider rollout**: replace the single seed URL in `scripts/seed_kb.py` with
the real scheme pages/PDFs from ccs.bihar.gov.in (Kisan Panjikaran, Mukhyamantri Ganna Vikas Yojana,
gur license rules, ZDC notifications, etc.) via the admin document-upload endpoints, and test Hindi/
Hinglish retrieval quality specifically — don't assume English-tuned defaults carry over.

---

## How Scope Filtering Works

Every document chunk stored in Qdrant carries a `scope` metadata field: `"public"` or `"admin"`.

- **Public queries** (`POST /chat/query`) always filter Qdrant with `scope == "public"`.
- **Admin queries** (`POST /admin/chat/query`) apply no filter — admins see all chunks.
- **At ingestion time** the admin chooses scope via a `scope` form field (PDF upload) or `?scope=` query param (websites). Default is `"public"`.
- **No duplication** of documents: the same Qdrant collection is used for both roles; access control is purely via metadata filtering at query time.

## How Confidence Thresholds Are Configured

Three env vars (with defaults) control escalation sensitivity:

| Variable | Default | Description |
|---|---|---|
| `CONFIDENCE_RETRIEVAL_LOW` | `0.55` | Average cosine similarity of top-K retrieved chunks below which retrieval is considered weak. |
| `CONFIDENCE_COMBINED_LOW` | `0.45` | Weighted combined score (0.6×retrieval + 0.4×LLM) below which the query is escalated. |
| `CONFIDENCE_LLM_LOW_LABELS` | `"low,no_answer"` | Comma-separated LLM self-check labels that immediately trigger escalation regardless of retrieval score. |

**LLM self-check** is embedded in the same generation prompt (no extra LLM call). The model outputs a `{"confidence": "high"|"medium"|"low"|"no_answer"}` JSON line that is parsed and stripped before the answer is shown to the user.

**Tuning**: raise `CONFIDENCE_COMBINED_LOW` (e.g. to `0.6`) to escalate more aggressively; lower it (e.g. to `0.3`) to escalate less.

## How to Run the Seed Script

```bash
cd backend

# 1. Make sure .env is set up (copy from .env.example and fill in credentials)
cp .env.example .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the seed script
python scripts/seed_kb.py
```

The script will:
1. Create all database tables (safe to re-run — idempotent).
2. Index two Wikipedia pages about Nalanda (public scope).
3. Index `data/pdfs/sample.pdf` (public scope) if the file exists — uses page-aware chunking for accurate citations.
4. Run a retrieval smoke test to confirm Qdrant connectivity and embedding pipeline are working.

After seeding, `POST /chat/query` with `{"question": "What is Nalanda?"}` should return a real answer.

## New API Endpoints Summary

### Public (anonymous, no auth)
| Method | Path | Description |
|---|---|---|
| `POST` | `/chat/query` | Main chat endpoint. `kb_only` mode, public scope. Rate-limited. |
| `POST` | `/chat/{query_id}/contact` | Submit contact info after escalation. |
| `GET` | `/chat/{query_id}/status` | Poll for officer reply. |

### Admin (Bearer token required)
| Method | Path | Description |
|---|---|---|
| `POST` | `/admin/chat/query` | Admin chat with mode selection and citations. |
| `POST` | `/admin/documents/adhoc-upload` | Upload ephemeral PDF (not added to KB). |
| `POST` | `/admin/documents/adhoc-query` | Query an ephemeral PDF. |
| `POST` | `/admin/documents/adhoc-promote` | Promote ephemeral PDF to permanent KB. |
| `PATCH` | `/documents/{id}/scope` | Update document scope. |

### Grievance (Bearer token, consumed by grievance backend)
| Method | Path | Description |
|---|---|---|
| `GET` | `/grievance/pending` | List unresolved escalated queries. |
| `GET` | `/grievance/{query_id}` | Full detail of one query. |
| `PATCH` | `/grievance/{query_id}/status` | Claim query (set `in_progress`). |
| `POST` | `/grievance/{query_id}/reply` | Submit officer reply → resolves query. |

## Cache Invalidation Strategy

**Choice: TTL + explicit invalidation on officer reply.**

- Cache entries expire after `CACHE_TTL_SECONDS` (default: 1 hour).
- When `POST /grievance/{query_id}/reply` is called, the cache entry linked to that `query_id` is immediately invalidated.
- Next identical query re-runs the full pipeline, which may now return a high-confidence answer (since the KB may have been updated by the officer's knowledge).

**Why TTL over Redis**: Simpler dependency footprint for v1. A Redis backend can replace the in-memory store by implementing the same `SemanticCache` interface.

## New Environment Variables

Add these to your `.env` file (all have defaults — no breaking change to existing deployments):

```env
# Confidence thresholds
CONFIDENCE_RETRIEVAL_LOW=0.55
CONFIDENCE_COMBINED_LOW=0.45
CONFIDENCE_LLM_LOW_LABELS=low,no_answer

# Semantic cache
CACHE_ENABLED=true
CACHE_SIMILARITY_THRESHOLD=0.92
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=500

# Rate limiting
PUBLIC_CHAT_RATE_LIMIT=10/minute
ADMIN_RATE_LIMIT=60/minute

# Ad-hoc PDF max size (bytes)
ADHOC_PDF_MAX_BYTES=20971520
```
