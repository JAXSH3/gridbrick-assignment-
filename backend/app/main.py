"""FastAPI application entrypoint for UK Wind Day-Ahead Decision Support Desk."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import RequestIdMiddleware, setup_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context initializing database and logging on startup."""
    setup_logging()
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production API for UK energy utility day-ahead power buyers. "
        "Reconstructs exact wind forecasts available at gate closure, evaluates accuracy, "
        "and calculates statistical procurement safety buffers using official Elexon BMRS data."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Correlation ID and access logging middleware
app.add_middleware(RequestIdMiddleware)

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Register v1 master router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", include_in_schema=False)
def root_health() -> dict[str, str]:
    """Simple root health check endpoint for container probes."""
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/", include_in_schema=False)
def root_redirect() -> RedirectResponse:
    """Redirect root path to interactive OpenAPI documentation."""
    return RedirectResponse(url=f"{settings.API_V1_STR}/docs")
