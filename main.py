"""
INCOIS Ocean Hazard Crowdsourcing Platform — Python/FastAPI Backend
"""

import os
import sys

# Ensure project root is on path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger

from config.settings import settings
from config.database import connect_db, disconnect_db
from config.redis import connect_redis, disconnect_redis
from app.utils.logger import setup_logger
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.services.scheduler import start_scheduler, stop_scheduler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Routes
from app.routes import auth, reports, hotspots, social, admin, analytics, ws


# ──────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    logger.info("🌊 INCOIS Platform starting up…")

    await connect_db()
    await connect_redis()
    start_scheduler()

    yield  # ← application runs here

    stop_scheduler()
    await disconnect_redis()
    await disconnect_db()
    logger.info("🌊 INCOIS Platform shut down cleanly.")


# ──────────────────────────────────────────────
# App factory
# ──────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="INCOIS Ocean Hazard Crowdsourcing Platform",
        description=(
            "Real-time citizen reporting of ocean hazards with NLP-powered "
            "social media monitoring and dynamic hotspot generation."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # ── Global exception handler ────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc} | {request.method} {request.url}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"},
        )

    # ── Health check ────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "service": "INCOIS Hazard Platform", "version": "1.0.0"}

    # ── API Routes ──────────────────────────────
    PREFIX = "/api/v1"
    app.include_router(auth.router,      prefix=PREFIX)
    app.include_router(reports.router,   prefix=PREFIX)
    app.include_router(hotspots.router,  prefix=PREFIX)
    app.include_router(social.router,    prefix=PREFIX)
    app.include_router(admin.router,     prefix=PREFIX)
    app.include_router(analytics.router, prefix=PREFIX)
    app.include_router(ws.router)        # WebSocket has no prefix

    return app


app = create_app()


# ──────────────────────────────────────────────
# Dev entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level="debug" if settings.APP_DEBUG else "info",
    )
