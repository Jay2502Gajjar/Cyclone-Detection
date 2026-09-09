"""Health endpoint.

Reports what is actually loaded, including whether anything is trained. Phase 0 answers
``DEGRADED`` with every component untrained, which is the truthful answer rather than a
failure.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.registry import registry
from app.schemas.health import HealthResponse, ModelInfo

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    models = [ModelInfo(**m) for m in registry.health()]
    any_trained = any(m.isTrained for m in models)
    return HealthResponse(status="UP" if any_trained else "DEGRADED", models=models)
