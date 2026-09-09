"""
Create demo scenarios for CycloVision offline operation.

Generates 5 complete, self-contained demo scenarios based on real
North Indian Ocean cyclones. All values are curated from publicly
available data and are explicitly marked as demo data.

Usage:
    python scripts/create_demo_scenarios.py

Output:
    data/demo/scenarios/scenario_01/ through scenario_05/
    Each contains a scenario.json file.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent
_SCENARIOS_DIR = _PROJECT_ROOT / "data" / "demo" / "scenarios"


def _build_scenarios() -> list:
    """
    Build 5 demo scenarios covering different cyclone states.

    Data is curated from publicly available IBTrACS and IMD records.
    All values are explicitly marked as demo data.
    """
    return [
        # ── Scenario 01: Developing Cyclone (MAHA 2019, Arabian Sea) ──
        {
            "scenario_id": "scenario_01",
            "title": "Developing Cyclone — MAHA (2019)",
            "description": (
                "Cyclone MAHA in the Arabian Sea during early formation stage. "
                "Demonstrates a developing system with moderate winds and gradual "
                "pressure drop. Data curated from public IBTrACS/IMD records, "
                "marked as demo."
            ),
            "cyclone": {
                "id": "DEMO_MAHA_2019",
                "name": "MAHA",
                "basin": "NI",
                "season_year": 2019,
                "status": "demo",
            },
            "latest_observation": {
                "observed_at": "2019-10-31T12:00:00+00:00",
                "latitude": 10.5,
                "longitude": 73.2,
                "wind_speed_kmh": 75.0,
                "pressure_hpa": 994.0,
                "movement_direction_deg": 310.0,
                "movement_speed_kmh": 12.0,
                "intensity_category": "Cyclonic Storm",
            },
            "historical_observations": [
                {
                    "observed_at": "2019-10-30T00:00:00+00:00",
                    "latitude": 9.8,
                    "longitude": 74.5,
                    "wind_speed_kmh": 45.0,
                    "pressure_hpa": 1002.0,
                    "movement_direction_deg": 300.0,
                    "movement_speed_kmh": 10.0,
                    "intensity_category": "Depression",
                },
                {
                    "observed_at": "2019-10-30T12:00:00+00:00",
                    "latitude": 10.0,
                    "longitude": 74.0,
                    "wind_speed_kmh": 55.0,
                    "pressure_hpa": 998.0,
                    "movement_direction_deg": 305.0,
                    "movement_speed_kmh": 11.0,
                    "intensity_category": "Deep Depression",
                },
                {
                    "observed_at": "2019-10-31T00:00:00+00:00",
                    "latitude": 10.3,
                    "longitude": 73.6,
                    "wind_speed_kmh": 65.0,
                    "pressure_hpa": 996.0,
                    "movement_direction_deg": 308.0,
                    "movement_speed_kmh": 11.5,
                    "intensity_category": "Cyclonic Storm",
                },
            ],
            "weather": {
                "latitude": 10.5,
                "longitude": 73.2,
                "wind_speed_kmh": 75.0,
                "pressure_hpa": 994.0,
                "temperature_c": 28.2,
                "sea_surface_temp_c": None,
                "observed_at": "2019-10-31T12:00:00+00:00",
                "source": "demo",
            },
            "satellite": {
                "image_id": "demo_ir_cyclone_01",
                "cyclone_id": "DEMO_MAHA_2019",
                "captured_at": "2019-10-31T06:00:00+00:00",
                "image_type": "infrared",
                "source": "demo",
                "storage_path": "data/demo/images/cyclone/demo_ir_cyclone_01.png",
                "is_cyclone": True,
            },
            "source": {
                "mode": "demo",
                "provider": "demo",
                "processing_script": "scripts/create_demo_scenarios.py",
                "processing_version": "0.1.0",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        },

        # ── Scenario 02: Intensifying Super Cyclone (AMPHAN 2020, Bay of Bengal) ──
        {
            "scenario_id": "scenario_02",
            "title": "Intensifying Super Cyclone — AMPHAN (2020)",
            "description": (
                "Super Cyclonic Storm AMPHAN in the Bay of Bengal during rapid "
                "intensification. One of the strongest cyclones recorded in the "
                "North Indian Ocean. Data curated from public records, marked as demo."
            ),
            "cyclone": {
                "id": "DEMO_AMPHAN_2020",
                "name": "AMPHAN",
                "basin": "NI",
                "season_year": 2020,
                "status": "demo",
            },
            "latest_observation": {
                "observed_at": "2020-05-18T06:00:00+00:00",
                "latitude": 14.8,
                "longitude": 86.3,
                "wind_speed_kmh": 240.0,
                "pressure_hpa": 920.0,
                "movement_direction_deg": 350.0,
                "movement_speed_kmh": 14.0,
                "intensity_category": "Super Cyclonic Storm",
            },
            "historical_observations": [
                {
                    "observed_at": "2020-05-16T00:00:00+00:00",
                    "latitude": 11.5,
                    "longitude": 87.0,
                    "wind_speed_kmh": 85.0,
                    "pressure_hpa": 990.0,
                    "movement_direction_deg": 340.0,
                    "movement_speed_kmh": 10.0,
                    "intensity_category": "Cyclonic Storm",
                },
                {
                    "observed_at": "2020-05-17T00:00:00+00:00",
                    "latitude": 12.8,
                    "longitude": 86.8,
                    "wind_speed_kmh": 140.0,
                    "pressure_hpa": 965.0,
                    "movement_direction_deg": 345.0,
                    "movement_speed_kmh": 12.0,
                    "intensity_category": "Very Severe Cyclonic Storm",
                },
                {
                    "observed_at": "2020-05-17T12:00:00+00:00",
                    "latitude": 13.5,
                    "longitude": 86.5,
                    "wind_speed_kmh": 185.0,
                    "pressure_hpa": 940.0,
                    "movement_direction_deg": 348.0,
                    "movement_speed_kmh": 13.0,
                    "intensity_category": "Extremely Severe Cyclonic Storm",
                },
            ],
            "weather": {
                "latitude": 14.8,
                "longitude": 86.3,
                "wind_speed_kmh": 240.0,
                "pressure_hpa": 920.0,
                "temperature_c": 27.5,
                "sea_surface_temp_c": None,
                "observed_at": "2020-05-18T06:00:00+00:00",
                "source": "demo",
            },
            "satellite": {
                "image_id": "demo_ir_cyclone_01",
                "cyclone_id": "DEMO_AMPHAN_2020",
                "captured_at": "2020-05-18T06:00:00+00:00",
                "image_type": "infrared",
                "source": "demo",
                "storage_path": "data/demo/images/cyclone/demo_ir_cyclone_01.png",
                "is_cyclone": True,
            },
            "source": {
                "mode": "demo",
                "provider": "demo",
                "processing_script": "scripts/create_demo_scenarios.py",
                "processing_version": "0.1.0",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        },

        # ── Scenario 03: Mature Extremely Severe (BIPARJOY 2023, Arabian Sea) ──
        {
            "scenario_id": "scenario_03",
            "title": "Mature Extremely Severe — BIPARJOY (2023)",
            "description": (
                "Extremely Severe Cyclonic Storm BIPARJOY in the Arabian Sea at "
                "peak intensity. Long-lived cyclone that threatened the Gujarat coast. "
                "Data curated from public records, marked as demo."
            ),
            "cyclone": {
                "id": "DEMO_BIPARJOY_2023",
                "name": "BIPARJOY",
                "basin": "NI",
                "season_year": 2023,
                "status": "demo",
            },
            "latest_observation": {
                "observed_at": "2023-06-12T12:00:00+00:00",
                "latitude": 17.2,
                "longitude": 64.8,
                "wind_speed_kmh": 185.0,
                "pressure_hpa": 944.0,
                "movement_direction_deg": 330.0,
                "movement_speed_kmh": 8.0,
                "intensity_category": "Extremely Severe Cyclonic Storm",
            },
            "historical_observations": [
                {
                    "observed_at": "2023-06-08T00:00:00+00:00",
                    "latitude": 14.0,
                    "longitude": 67.0,
                    "wind_speed_kmh": 65.0,
                    "pressure_hpa": 996.0,
                    "movement_direction_deg": 320.0,
                    "movement_speed_kmh": 6.0,
                    "intensity_category": "Cyclonic Storm",
                },
                {
                    "observed_at": "2023-06-10T00:00:00+00:00",
                    "latitude": 15.5,
                    "longitude": 66.0,
                    "wind_speed_kmh": 120.0,
                    "pressure_hpa": 972.0,
                    "movement_direction_deg": 325.0,
                    "movement_speed_kmh": 7.0,
                    "intensity_category": "Very Severe Cyclonic Storm",
                },
                {
                    "observed_at": "2023-06-11T12:00:00+00:00",
                    "latitude": 16.5,
                    "longitude": 65.2,
                    "wind_speed_kmh": 170.0,
                    "pressure_hpa": 950.0,
                    "movement_direction_deg": 328.0,
                    "movement_speed_kmh": 7.5,
                    "intensity_category": "Extremely Severe Cyclonic Storm",
                },
            ],
            "weather": {
                "latitude": 17.2,
                "longitude": 64.8,
                "wind_speed_kmh": 185.0,
                "pressure_hpa": 944.0,
                "temperature_c": 28.8,
                "sea_surface_temp_c": None,
                "observed_at": "2023-06-12T12:00:00+00:00",
                "source": "demo",
            },
            "satellite": {
                "image_id": "demo_vis_cyclone_02",
                "cyclone_id": "DEMO_BIPARJOY_2023",
                "captured_at": "2023-06-12T09:00:00+00:00",
                "image_type": "visible",
                "source": "demo",
                "storage_path": "data/demo/images/cyclone/demo_vis_cyclone_02.png",
                "is_cyclone": True,
            },
            "source": {
                "mode": "demo",
                "provider": "demo",
                "processing_script": "scripts/create_demo_scenarios.py",
                "processing_version": "0.1.0",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        },

        # ── Scenario 04: Weakening (MOCHA 2023, Bay of Bengal) ──
        {
            "scenario_id": "scenario_04",
            "title": "Weakening Post-Landfall — MOCHA (2023)",
            "description": (
                "Cyclone MOCHA weakening after making landfall in Myanmar. "
                "Demonstrates a storm transitioning from Extremely Severe to "
                "Depression. Data curated from public records, marked as demo."
            ),
            "cyclone": {
                "id": "DEMO_MOCHA_2023",
                "name": "MOCHA",
                "basin": "NI",
                "season_year": 2023,
                "status": "demo",
            },
            "latest_observation": {
                "observed_at": "2023-05-14T18:00:00+00:00",
                "latitude": 21.5,
                "longitude": 93.5,
                "wind_speed_kmh": 45.0,
                "pressure_hpa": 998.0,
                "movement_direction_deg": 30.0,
                "movement_speed_kmh": 18.0,
                "intensity_category": "Depression",
            },
            "historical_observations": [
                {
                    "observed_at": "2023-05-13T06:00:00+00:00",
                    "latitude": 18.8,
                    "longitude": 92.5,
                    "wind_speed_kmh": 210.0,
                    "pressure_hpa": 928.0,
                    "movement_direction_deg": 15.0,
                    "movement_speed_kmh": 14.0,
                    "intensity_category": "Extremely Severe Cyclonic Storm",
                },
                {
                    "observed_at": "2023-05-14T00:00:00+00:00",
                    "latitude": 20.0,
                    "longitude": 93.0,
                    "wind_speed_kmh": 140.0,
                    "pressure_hpa": 960.0,
                    "movement_direction_deg": 20.0,
                    "movement_speed_kmh": 16.0,
                    "intensity_category": "Very Severe Cyclonic Storm",
                },
                {
                    "observed_at": "2023-05-14T12:00:00+00:00",
                    "latitude": 21.0,
                    "longitude": 93.3,
                    "wind_speed_kmh": 80.0,
                    "pressure_hpa": 988.0,
                    "movement_direction_deg": 25.0,
                    "movement_speed_kmh": 17.0,
                    "intensity_category": "Cyclonic Storm",
                },
            ],
            "weather": {
                "latitude": 21.5,
                "longitude": 93.5,
                "wind_speed_kmh": 45.0,
                "pressure_hpa": 998.0,
                "temperature_c": 29.0,
                "sea_surface_temp_c": None,
                "observed_at": "2023-05-14T18:00:00+00:00",
                "source": "demo",
            },
            "satellite": {
                "image_id": "demo_wv_cyclone_03",
                "cyclone_id": "DEMO_MOCHA_2023",
                "captured_at": "2023-05-13T12:00:00+00:00",
                "image_type": "water_vapor",
                "source": "demo",
                "storage_path": "data/demo/images/cyclone/demo_wv_cyclone_03.png",
                "is_cyclone": True,
            },
            "source": {
                "mode": "demo",
                "provider": "demo",
                "processing_script": "scripts/create_demo_scenarios.py",
                "processing_version": "0.1.0",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        },

        # ── Scenario 05: Landfall Threat (REMAL 2024, Bay of Bengal) ──
        {
            "scenario_id": "scenario_05",
            "title": "Landfall Threat — REMAL (2024)",
            "description": (
                "Severe Cyclonic Storm REMAL approaching the coast of West Bengal "
                "and Bangladesh. Demonstrates a landfall-threatening scenario with "
                "moderate intensity. Data curated from public records, marked as demo."
            ),
            "cyclone": {
                "id": "DEMO_REMAL_2024",
                "name": "REMAL",
                "basin": "NI",
                "season_year": 2024,
                "status": "demo",
            },
            "latest_observation": {
                "observed_at": "2024-05-26T12:00:00+00:00",
                "latitude": 20.8,
                "longitude": 88.5,
                "wind_speed_kmh": 110.0,
                "pressure_hpa": 978.0,
                "movement_direction_deg": 10.0,
                "movement_speed_kmh": 15.0,
                "intensity_category": "Severe Cyclonic Storm",
            },
            "historical_observations": [
                {
                    "observed_at": "2024-05-24T00:00:00+00:00",
                    "latitude": 17.5,
                    "longitude": 89.0,
                    "wind_speed_kmh": 55.0,
                    "pressure_hpa": 1000.0,
                    "movement_direction_deg": 5.0,
                    "movement_speed_kmh": 12.0,
                    "intensity_category": "Deep Depression",
                },
                {
                    "observed_at": "2024-05-25T00:00:00+00:00",
                    "latitude": 18.8,
                    "longitude": 88.8,
                    "wind_speed_kmh": 75.0,
                    "pressure_hpa": 992.0,
                    "movement_direction_deg": 8.0,
                    "movement_speed_kmh": 13.0,
                    "intensity_category": "Cyclonic Storm",
                },
                {
                    "observed_at": "2024-05-26T00:00:00+00:00",
                    "latitude": 19.8,
                    "longitude": 88.6,
                    "wind_speed_kmh": 95.0,
                    "pressure_hpa": 984.0,
                    "movement_direction_deg": 10.0,
                    "movement_speed_kmh": 14.0,
                    "intensity_category": "Severe Cyclonic Storm",
                },
            ],
            "weather": {
                "latitude": 20.8,
                "longitude": 88.5,
                "wind_speed_kmh": 110.0,
                "pressure_hpa": 978.0,
                "temperature_c": 29.5,
                "sea_surface_temp_c": None,
                "observed_at": "2024-05-26T12:00:00+00:00",
                "source": "demo",
            },
            "satellite": {
                "image_id": "demo_ir_cyclone_01",
                "cyclone_id": "DEMO_REMAL_2024",
                "captured_at": "2024-05-26T06:00:00+00:00",
                "image_type": "infrared",
                "source": "demo",
                "storage_path": "data/demo/images/cyclone/demo_ir_cyclone_01.png",
                "is_cyclone": True,
            },
            "source": {
                "mode": "demo",
                "provider": "demo",
                "processing_script": "scripts/create_demo_scenarios.py",
                "processing_version": "0.1.0",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]


def create_demo_scenarios() -> None:
    """Create all demo scenario directories and JSON files."""
    scenarios = _build_scenarios()

    for scenario in scenarios:
        scenario_dir = _SCENARIOS_DIR / scenario["scenario_id"]
        scenario_dir.mkdir(parents=True, exist_ok=True)

        scenario_path = scenario_dir / "scenario.json"
        with open(scenario_path, "w", encoding="utf-8") as f:
            json.dump(scenario, f, indent=2, ensure_ascii=False)

        logger.info(
            "Created scenario: %s - %s",
            scenario["scenario_id"],
            scenario["title"],
        )

    logger.info("Created %d demo scenarios in %s", len(scenarios), _SCENARIOS_DIR)


if __name__ == "__main__":
    create_demo_scenarios()
