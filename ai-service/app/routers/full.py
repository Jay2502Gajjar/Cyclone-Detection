"""The composite inference endpoint.

This is the only route Spring Boot calls in normal operation. Everything the Command
Center needs comes back in one response, so the frontend never has to chase follow-up
calls while a judge is watching.

The temporal mask (invariant I1) is enforced by ``InferFullRequest``'s validator before
this function body runs, so a request carrying future observations is rejected with 422
rather than quietly repaired.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.pipeline.full_analysis import run_full_analysis
from app.registry import registry
from app.schemas.forecast import InferFullRequest, InferFullResponse

router = APIRouter(tags=["inference"])


@router.post("/infer/full", response_model=InferFullResponse)
def infer_full(
    request: InferFullRequest, settings: Settings = Depends(get_settings)
) -> InferFullResponse:
    return run_full_analysis(
        request, registry, settings.frames_dir, settings.bundle_version
    )
