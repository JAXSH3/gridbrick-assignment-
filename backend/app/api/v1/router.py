"""API v1 master router aggregating health, forecast, and accuracy endpoints."""

from fastapi import APIRouter

from app.api.v1.accuracy import router as accuracy_router
from app.api.v1.forecast import router as forecast_router
from app.api.v1.health import router as health_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(forecast_router)
api_v1_router.include_router(accuracy_router)
