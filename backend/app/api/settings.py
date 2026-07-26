import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.dependencies import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

# In-memory store — survives the process lifetime (resets on redeploy).
# For persistence across deploys, store in DB or env var on Render.
_search_mode: str = settings.SEARCH_MODE  # "hybrid" | "kb_only" | "web_only"

VALID_MODES = {"hybrid", "kb_only", "web_only"}


class SearchModeRequest(BaseModel):
    mode: str


def get_search_mode() -> str:
    return _search_mode


@router.get("/search-mode")
def read_search_mode(current_user=Depends(get_admin_user)):
    return {"search_mode": _search_mode}


@router.post("/search-mode")
def update_search_mode(
    request: SearchModeRequest,
    current_user=Depends(get_admin_user),
):
    global _search_mode
    if request.mode not in VALID_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode. Must be one of: {', '.join(sorted(VALID_MODES))}",
        )
    _search_mode = request.mode
    logger.info("Search mode changed to '%s' by admin %s", _search_mode, current_user.id)
    return {"search_mode": _search_mode, "message": f"Search mode set to '{_search_mode}'."}
