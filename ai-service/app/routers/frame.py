"""Single-frame analysis.

Used by the offline precompute job, which runs this over every frame of every demo storm
so the timeline scrubber reads finished rows instead of triggering inference. Also backs
the "upload an unseen image" demo in Phase 3.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.io.bt_loader import FrameNotAvailable, load_bt
from app.pipeline.full_analysis import _analyse_structure, _estimate_intensity
from app.registry import registry
from app.schemas.common import ObservedBlock, Provenance, Source
from app.schemas.frame import FrameAnalysis, InferFrameRequest

router = APIRouter(tags=["inference"])


@router.post("/infer/frame", response_model=FrameAnalysis)
def infer_frame(
    request: InferFrameRequest, settings: Settings = Depends(get_settings)
) -> FrameAnalysis:
    bt = None
    if request.frameRef is not None:
        try:
            bt = load_bt(settings.frames_dir, request.frameRef.btPath)
        except FrameNotAvailable:
            bt = None

    return FrameAnalysis(
        sid=request.sid,
        t=request.t,
        observed=ObservedBlock(
            lat=0.0, lon=0.0, source=Source(provenance=Provenance.OBSERVED)
        ),
        imageUrl=request.frameRef.imageUrl if request.frameRef else None,
        imageTime=request.frameRef.imageTime if request.frameRef else None,
        imageSource=request.frameRef.imageSource if request.frameRef else None,
        structure=_analyse_structure(bt, registry),
        vision=_estimate_intensity(bt, registry),
        analysisVersion=settings.bundle_version,
    )
