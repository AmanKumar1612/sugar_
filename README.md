# Sugarcane AI – Smart Farmer Assistant

A production-ready full-stack web application for sugarcane farmers with:
- React + Vite frontend
- FastAPI backend
- JWT auth and role-based access
- AI-powered chatbot with RAG using ChromaDB + sentence transformers
- Admin knowledge management
- SQLite database and Docker-ready setup

## Features
- Landing page with animated experience
- Farmer/Admin authentication
- Secure chat interface after login
- Admin knowledge management CRUD
- Dummy knowledge base seeding with embeddings
- Swagger/OpenAPI docs via FastAPI

## Backend setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Frontend setup
```bash
cd frontend/vite-project
npm install
npm run dev
```

## Docker
```bash
docker compose up --build
```

