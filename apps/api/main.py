"""
ChainRadar — FastAPI Main Application
Entry point with middleware, routers, health checks, and lifecycle events.
"""

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from interface.middleware.security_headers import SecurityHeadersMiddleware
from interface.middleware.rate_limiter import RateLimiterMiddleware, get_rate_limiter
from interface.routers import auth, wallets, alerts, webhooks, stream

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown events."""
    logger.info("ChainRadar starting", env=settings.app_env)

    if not settings.is_production:
        await init_db()
        logger.info("Database tables created (dev mode)")

    logger.info("ChainRadar ready", sim_configured=bool(settings.sim_api_key))
    yield
    logger.info("ChainRadar shutting down")


app = FastAPI(
    title="ChainRadar API",
    description="Real-time onchain monitoring and smart alert system for Solana",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# ─── Middleware (order matters — outermost first) ─────────────

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimiterMiddleware, rate_limiter=get_rate_limiter())
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id", "X-RateLimit-Policy"],
)

# ─── Routers ─────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api/v1")
app.include_router(wallets.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(stream.router, prefix="/api/v1")


# ─── Health Checks ───────────────────────────────────────────

@app.get("/health/live", tags=["Health"])
async def liveness():
    return {"status": "alive", "service": "chainradar-api"}


@app.get("/health/ready", tags=["Health"])
async def readiness():
    checks = {"database": False, "redis": False, "sim_api": False}

    try:
        from database import async_session_factory
        from sqlalchemy import text
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception as e:
        logger.error("DB health check failed", error=str(e))

    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        checks["redis"] = True
        await r.aclose()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))

    checks["sim_api"] = bool(settings.sim_api_key)
    is_ready = all(checks.values())
    return {"status": "ready" if is_ready else "degraded", "checks": checks}


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "ChainRadar API",
        "version": "1.0.0",
        "description": "Real-time onchain monitoring — PagerDuty for Solana",
        "docs": "/docs",
    }
