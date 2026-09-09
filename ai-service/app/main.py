"""CycloVision AI service.

Stateless inference. No database connection, no downloads, no training code — it loads a
model bundle once at startup and answers requests about frames and forecasts.

The startup log deliberately shouts about how many components are trained. In Phase 0
that number is zero, and a service that quietly pretended otherwise would undermine the
one thing this project is trying to be careful about.
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import get_settings
from app.registry import load_all
from app.routers import analogues, frame, full, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)

    # Models load once, here. Loading per request would put multi-second latency on the
    # most-used path in the demo.
    load_all(settings)
    logger.info(
        "CycloVision AI service ready · bundle={} · frames={} · models={}",
        settings.bundle_version,
        settings.frames_dir,
        settings.models_dir,
    )
    yield
    logger.info("CycloVision AI service shutting down")


app = FastAPI(
    title="CycloVision AI Service",
    version="phase0",
    description=(
        "Stateless inference for tropical cyclone evolution intelligence. "
        "Never receives observations later than the requested as-of time, and never "
        "produces verification against ground truth — both belong to the backend."
    ),
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(full.router)
app.include_router(frame.router)
app.include_router(analogues.router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Surface contract violations as 422 with the reason intact."""
    return JSONResponse(
        status_code=422,
        content={"code": "INVALID_REQUEST", "message": str(exc)},
    )


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "service": "cyclovision-ai",
        "docs": "/docs",
        "health": "/health",
    }
