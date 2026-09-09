"""Health contract types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Provenance


class ModelInfo(BaseModel):
    """One registered component and what it is actually allowed to claim."""

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    key: str
    version: str
    provenance: Provenance
    isTrained: bool


class HealthResponse(BaseModel):
    """Reports the truth about the bundle, including that nothing is trained yet."""

    model_config = ConfigDict(populate_by_name=True)

    status: str
    models: list[ModelInfo] = []
