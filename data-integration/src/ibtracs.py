"""
IBTrACS data loading and querying.

Provides functions to load processed IBTrACS data and query it by
cyclone ID, basin, season, or spatial/temporal criteria. This module
does NOT download or process raw data — see scripts/download_ibtracs.py
and scripts/process_ibtracs.py for that.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from .models import Cyclone, Observation, DataMode, SourceInfo
from .normalizers import classify_intensity

logger = logging.getLogger(__name__)

# Default path to processed IBTrACS data
_DEFAULT_PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed" / "ibtracs"


class IBTrACSStore:
    """
    In-memory store for processed IBTrACS cyclone records.

    Loads from the processed JSON files produced by process_ibtracs.py.
    """

    def __init__(self, processed_dir: Optional[Path] = None):
        self._dir = processed_dir or _DEFAULT_PROCESSED_DIR
        self._cyclones: Dict[str, Cyclone] = {}
        self._observations: Dict[str, List[Observation]] = {}
        self._loaded = False

    # ── Loading ───────────────────────────────────────────────────────

    def load(self) -> bool:
        """
        Load processed IBTrACS data from disk.

        Returns True if data was loaded successfully, False otherwise.
        """
        cyclones_file = self._dir / "cyclones.json"
        observations_file = self._dir / "observations.json"

        if not cyclones_file.exists():
            logger.warning("Processed cyclones file not found: %s", cyclones_file)
            return False

        try:
            with open(cyclones_file, "r", encoding="utf-8") as f:
                raw_cyclones = json.load(f)

            for entry in raw_cyclones:
                cyc = Cyclone(**entry)
                self._cyclones[cyc.id] = cyc

            if observations_file.exists():
                with open(observations_file, "r", encoding="utf-8") as f:
                    raw_obs = json.load(f)

                for entry in raw_obs:
                    obs = Observation(**entry)
                    cid = entry.get("cyclone_id", "")
                    if cid not in self._observations:
                        self._observations[cid] = []
                    self._observations[cid].append(obs)

                # Sort observations chronologically
                for cid in self._observations:
                    self._observations[cid].sort(key=lambda o: o.observed_at)

            self._loaded = True
            logger.info(
                "Loaded %d cyclones, %d total observations",
                len(self._cyclones),
                sum(len(v) for v in self._observations.values()),
            )
            return True

        except Exception as exc:
            logger.error("Failed to load IBTrACS data: %s", exc)
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── Queries ───────────────────────────────────────────────────────

    def get_cyclone(self, cyclone_id: str) -> Optional[Cyclone]:
        """Get cyclone metadata by ID."""
        return self._cyclones.get(cyclone_id)

    def get_observations(self, cyclone_id: str) -> List[Observation]:
        """Get all observations for a cyclone, chronologically ordered."""
        return self._observations.get(cyclone_id, [])

    def get_latest_observation(self, cyclone_id: str) -> Optional[Observation]:
        """Get the most recent observation for a cyclone."""
        obs = self.get_observations(cyclone_id)
        return obs[-1] if obs else None

    def list_cyclones(
        self,
        basin: Optional[str] = None,
        season_year: Optional[int] = None,
        limit: int = 100,
    ) -> List[Cyclone]:
        """
        List cyclones with optional filtering.

        Args:
            basin: Filter by basin code (e.g. "NI").
            season_year: Filter by season year.
            limit: Maximum number of results.
        """
        results = sorted(
            self._cyclones.values(),
            key=lambda c: (1 if c.name != "UNNAMED" else 0, c.season_year, c.id),
            reverse=True,
        )

        if basin:
            results = [c for c in results if c.basin == basin]
        if season_year:
            results = [c for c in results if c.season_year == season_year]

        return results[:limit]

    def search_by_name(self, name: str) -> List[Cyclone]:
        """Search cyclones by name (case-insensitive substring match)."""
        name_upper = name.upper()
        return [
            c for c in self._cyclones.values()
            if name_upper in c.name.upper()
        ]

    def get_track(self, cyclone_id: str) -> List[dict]:
        """
        Get the full track of a cyclone as a list of coordinate dicts.

        Returns a GeoJSON-friendly list of points.
        """
        observations = self.get_observations(cyclone_id)
        return [
            {
                "lat": obs.latitude,
                "lon": obs.longitude,
                "time": obs.observed_at.isoformat() if obs.observed_at else None,
                "wind_kmh": obs.wind_speed_kmh,
                "pressure_hpa": obs.pressure_hpa,
                "category": obs.intensity_category.value,
            }
            for obs in observations
        ]

    def get_source_info(self) -> SourceInfo:
        """Return provenance information for IBTrACS data."""
        return SourceInfo(
            mode=DataMode.REAL,
            provider="NOAA IBTrACS",
            source_url="https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/",
            processing_script="scripts/process_ibtracs.py",
            processing_version="0.1.0",
        )
