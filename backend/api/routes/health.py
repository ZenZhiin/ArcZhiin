# =============================================================================
# ArcZhiin — Health Check Route
# =============================================================================

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": "ok", "service": "arczhiin"}
