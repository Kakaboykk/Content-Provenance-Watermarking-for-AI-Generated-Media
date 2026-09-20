"""
backend/app/api/routes/health.py

GET /health — liveness probe.

Returns {"status": "ok"} when the application is running.
Optionally checks the database connection and reflects its status.
"""
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.database import check_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    database: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness / health check",
    description=(
        "Returns `{\"status\": \"ok\"}` when the application is running. "
        "Also reports the database connectivity status."
    ),
)
def health_check() -> HealthResponse:
    db_ok = check_db_connection()
    db_status = "ok" if db_ok else "unreachable"

    if not db_ok:
        logger.warning("Health check: database is unreachable")

    return HealthResponse(status="ok", database=db_status)
