"""
backend/app/main.py

FastAPI application factory.

Only the /health endpoint is wired in Phase 2A.
Business routes (provenance, asset, verify) will be added in later phases.
"""
import logging
import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.api.routes.watermark import router as watermark_router
from app.api.routes.verify import router as verify_router
from app.api.routes.generate import router as generate_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Content Provenance Watermarking API",
    description=(
        "Backend for the AI-Generated Media Watermarking system. "
        "Embeds and verifies content-provenance watermarks in images."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS (permissive in dev; restrict origins in production)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — Phase 2A: health | Phase 2B-2: upload/validate
# ---------------------------------------------------------------------------
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(watermark_router)
app.include_router(verify_router)
app.include_router(generate_router)

# ---------------------------------------------------------------------------
# Startup / shutdown hooks
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting Content Provenance API (env=%s)", settings.APP_ENV)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Shutting down Content Provenance API")
