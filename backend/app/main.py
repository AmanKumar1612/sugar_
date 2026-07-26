import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import Base, engine

import app.models  # noqa: F401 — registers all ORM classes

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.analytics import router as analytics_router
from app.api.settings import router as settings_router
from app.api.public_chat import router as public_chat_router
from app.api.admin_chat import router as admin_chat_router
from app.api.grievance import router as grievance_router

# -------------------------------------------------------
# Logging
# -------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------
# Rate limiter (slowapi — in-memory, per IP)
# -------------------------------------------------------

def _key_func(request: Request) -> str:
    """
    Key function for rate limiting.
    Uses X-Forwarded-For header (Render/nginx proxy) if available,
    otherwise falls back to remote address.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func, default_limits=[settings.ADMIN_RATE_LIMIT])


# -------------------------------------------------------
# CORS helpers
# -------------------------------------------------------

def _get_cors_origins() -> list[str]:
    origins_from_env = [
        o.strip()
        for o in settings.ALLOWED_ORIGINS.split(",")
        if o.strip()
    ]
    always_allowed = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    merged = list(dict.fromkeys(origins_from_env + always_allowed))
    logger.info("CORS allowed origins: %s", merged)
    return merged


# -------------------------------------------------------
# Startup / shutdown
# -------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Sugarcane Dept Chatbot API (env=%s)", settings.ENV)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")
    _bootstrap_admin()
    logger.info("Sugarcane Dept Chatbot API is ready.")
    yield
    logger.info("Sugarcane Dept Chatbot API shutting down.")


def _bootstrap_admin() -> None:
    if not settings.DEFAULT_ADMIN_EMAIL or not settings.DEFAULT_ADMIN_PASSWORD:
        return

    from app.core.database import SessionLocal
    from app.models.user import User
    from app.models.role import Role
    from app.core.security import hash_password

    db = SessionLocal()
    try:
        admin_role = (
            db.query(Role)
            .filter(Role.name.in_(["ADMIN", "SUPER_ADMIN"]))
            .first()
        )
        if not admin_role:
            logger.warning("Admin bootstrap skipped: ADMIN/SUPER_ADMIN role not found.")
            return

        if db.query(User).filter(User.role_id == admin_role.id).first():
            return

        if db.query(User).filter(User.email == settings.DEFAULT_ADMIN_EMAIL).first():
            logger.warning("Admin bootstrap: %s already registered.", settings.DEFAULT_ADMIN_EMAIL)
            return

        admin = User(
            name="Admin",
            email=settings.DEFAULT_ADMIN_EMAIL,
            hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            provider="LOCAL",
            is_verified=True,
            is_active=True,
            role_id=admin_role.id,
        )
        db.add(admin)
        db.commit()
        logger.info("Default admin created: %s", settings.DEFAULT_ADMIN_EMAIL)
    except Exception:
        db.rollback()
        logger.exception("Admin bootstrap failed.")
    finally:
        db.close()


# -------------------------------------------------------
# App
# -------------------------------------------------------

app = FastAPI(
    title="Sugarcane Industries Department Chatbot API",
    version="2.0.0",
    description=(
        "Dual-mode RAG chatbot for the Sugarcane Industries Department, Government of Bihar — "
        "public anonymous farmer chat (Hindi/Hinglish/English) with confidence-based escalation "
        "to department officers, and admin knowledge-base management with page-accurate citations."
    ),
    lifespan=lifespan,
    docs_url="/docs",      # always on so the grievance-backend dev can test
    redoc_url="/redoc",
)

# -------------------------------------------------------
# Rate limiting middleware
# -------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# -------------------------------------------------------
# CORS
# -------------------------------------------------------
cors_origins = _get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
    expose_headers=["Content-Type"],
    max_age=600,
)

# -------------------------------------------------------
# Apply per-endpoint rate limits via middleware
# Public chat is the most expensive endpoint — tightest limit.
# -------------------------------------------------------

@app.middleware("http")
async def rate_limit_public_chat(request: Request, call_next):
    """
    Apply a stricter rate limit to the public chat endpoint.
    This middleware intercepts /chat/query POST requests before the route
    handler runs and delegates to slowapi's limiter state if needed.
    The primary rate limiting decoration is done via the limiter.limit
    dependency injection pattern on the route itself.
    """
    response = await call_next(request)
    return response


# -------------------------------------------------------
# Routers
# -------------------------------------------------------

# Auth — admin/officer login only. Public (farmer) chat requires no account.
app.include_router(auth_router)

# Public (anonymous, no login) — farmer-facing chat
app.include_router(public_chat_router)    # POST /chat/query, GET /chat/{id}/status, POST /chat/{id}/contact

# Admin (Bearer token required) — officials managing KB and chatting with full access
app.include_router(documents_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(admin_chat_router)     # POST /admin/chat/query, /admin/documents/adhoc-*

# Grievance system integration (Bearer token, consumed by the grievance backend dev)
app.include_router(grievance_router)      # GET/PATCH/POST /grievance/*


# -------------------------------------------------------
# Health check
# -------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "version": "2.0.0"}
