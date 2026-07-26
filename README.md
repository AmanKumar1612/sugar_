# Ganna Sahayak — Sugarcane Dept Chatbot (Sugarcane Industries Department, Govt. of Bihar)

Two folders: `backend/` (FastAPI + RAG + grievance API) and `frontend/` (Next.js UI).
Run the backend first, then the frontend.

---

## 1. Backend — setup & run

### Requirements
- Python 3.11+
- PostgreSQL running locally (or a connection string to one)
- A Qdrant instance (cloud free tier or `docker run -p 6333:6333 qdrant/qdrant`)
- A Gemini API key, a Tavily API key (for web-search fallback mode)

### Steps
```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# now open .env and fill in real values:
#   DATABASE_URL, QDRANT_URL, QDRANT_API_KEY, GEMINI_API_KEY, TAVILY_API_KEY,
#   JWT_SECRET, JWT_REFRESH_SECRET (generate with: python -c "import secrets; print(secrets.token_hex(32))")

# create the DB tables + bootstrap an admin account
python scripts/init_roles.py
python scripts/create_admin.py       # follow the prompts for admin email/password

# (optional but recommended) seed the knowledge base with a starter document
python scripts/seed_kb.py

# run the API
uvicorn app.main:app --reload --port 8000
```

Once running:
- Swagger UI (test every endpoint without a frontend): **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

### Rotate your secrets first
Your original `.env` (shared earlier in this chat) is **not** included in this
folder — it's been stripped for safety since those keys were exposed in this
conversation. Rotate every one of them (Gemini, Tavily, Qdrant, Postgres
password, JWT secrets, Google OAuth secret) before using this in anything
beyond local testing.

---

## 2. Frontend — setup & run

### Requirements
- Node.js 20+

### Steps
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** — this is the public farmer-facing chat (no
login). Admin/officer sign-in is a separate, unlinked route at
**http://localhost:3000/login**, using the admin account you created above.

The frontend expects the backend at `http://localhost:8000` by default —
check `frontend/src/services/api.js` if you need to point it elsewhere.

---

## 3. What to hand your backend developer (grievance system)

He does **not** need the frontend or your `.env`. Give him:
1. The `backend/` folder (or just have it running somewhere he can reach)
2. The Swagger docs URL: `http://localhost:8000/docs` (or your deployed URL + `/docs`)
3. The grievance endpoints he'll integrate against:
   - `GET  /grievance/pending` — list of escalated queries awaiting an officer
   - `GET  /grievance/{query_id}` — full detail of one escalated query
   - `PATCH /grievance/{query_id}/status` — mark `in_progress`
   - `POST /grievance/{query_id}/reply` — submit the officer's final answer
4. An admin bearer token (from `/auth/login`) so he can authenticate his test calls.

He can test every one of these directly from `/docs` without you building anything extra.

---

## 4. What changed from the original NalandaGPT code

- Removed the old authenticated `/chat` + `/guest` routes (this was the source
  of the "login won't go away" issue) — public chat is now fully anonymous via
  `/chat/query`.
- The RAG answer engine no longer filters for "Nalanda" topics — it now
  recognizes sugarcane/farmer/scheme topics in **English, Hindi, and Hinglish**.
- Removed unused Neo4j/MinIO/Redis config that was never wired to anything.
- Removed the public self-registration flow — only admins/officers have
  accounts (created via `scripts/create_admin.py`), farmers need none.
- Rebranded all user-facing text, email templates, and API examples.

## 5. Known follow-ups (not done in this pass)
- **Verify Hindi embedding quality**: run a handful of real Hindi/Hinglish
  queries through `/chat/query` and check the retrieved chunks make sense —
  Gemini's embedding model is multilingual, but retrieval quality should still
  be spot-checked against real scheme documents, not just the one seed page.
- **Load real content**: replace the single seeded homepage crawl with the
  actual scheme PDFs/pages from ccs.bihar.gov.in via the admin document-upload
  endpoints, for both `public` and `admin` scope as appropriate.
- **No dedicated admin chat UI** exists yet in the frontend for the
  mode-toggle/citations/ad-hoc-PDF-summary features — those backend endpoints
  work today and are testable via `/docs`, but need a frontend admin chat page
  built when you're ready for that.
