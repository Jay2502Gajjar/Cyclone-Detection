"""Standalone analogue query.

Split out from ``/infer/full`` so the analogue drawer can refresh independently and so
the index can be exercised on its own during Phase 2 development.
"""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.registry import registry
from app.schemas.analogue import AnalogueBlock, AnalogueOutcome

router = APIRouter(tags=["inference"])


class AnalogueRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sid: str
    k: int = 20
    excludeSeason: int | None = None


@router.post("/infer/analogues", response_model=AnalogueBlock)
def infer_analogues(request: AnalogueRequest) -> AnalogueBlock:
    stamp = registry.stamp("analogue")
    if not registry.is_usable("analogue"):
        return AnalogueBlock(
            k=0,
            outcome=AnalogueOutcome(),
            matches=[],
            exclusions=["same-storm", "same-season"],
            source=stamp,
        )

    window = np.zeros(1)
    block = registry.impl("analogue").query(
        window, k=request.k, exclude_sid=request.sid, exclude_season=request.excludeSeason
    )
    return block.model_copy(update={"source": stamp})
