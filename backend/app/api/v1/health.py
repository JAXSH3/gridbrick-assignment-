"""Health and system diagnostics endpoint."""

from fastapi import APIRouter

from app.core.config import settings
from app.db.repository import DataRepository
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return system operational status and database record statistics."""
    repo = DataRepository()
    stats = repo.get_health_stats()
    return HealthResponse(
        status="healthy" if stats["database_connected"] else "degraded",
        version=settings.VERSION,
        **stats,
    )
