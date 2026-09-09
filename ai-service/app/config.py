"""Service configuration.

The AI service is stateless: it loads model weights and reads brightness-temperature
arrays, and that is all. It holds no database connection and downloads nothing, so its
configuration is three paths and a version string.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore",
        protected_namespaces=(),
    )

    #: Where trained weights live. Empty in Phase 0.
    models_dir: Path = Path("../models")

    #: Root for brightness-temperature arrays. Nothing outside it can be read.
    frames_dir: Path = Path("../data/frames")

    #: Stamped onto every response so a result can be traced to the bundle that made it.
    bundle_version: str = "phase0"

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
