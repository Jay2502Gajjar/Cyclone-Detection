# CycloVision Data Integration — Integration Contract

This document provides explicit guidelines for downstream developers (Backend / Spring Boot, AI Service / PyTorch, and Frontend / React) on how to interface with and consume normalized data produced by the `data-integration` module.

---

## 1. Interface Modalities

Downstream services can integrate with this module in two ways:

### A. HTTP REST API (Recommended for Prototyping & Live Runs)
Run the isolated data API server:
```bash
cd data-integration
python api/server.py
```
Base URL: `http://localhost:8001`

### B. Direct File Ingestion (Recommended for Batch Training & Database Seeders)
Directly read the preprocessed JSON/GeoJSON files:
- Cyclones list: `data-integration/data/processed/ibtracs/cyclones.json`
- Observations tracks: `data-integration/data/processed/ibtracs/observations.json`
- Demo Scenarios: `data-integration/data/demo/scenarios/scenario_01/scenario.json` ... `scenario_05`
- Satellite Catalog: `data-integration/data/demo/images/catalog.json`

---

## 2. Integration for Spring Boot Developers (Java / JPA / Flyway)

Spring Boot services (`backend/`) responsible for persistent storage and business logic can map to the following canonical structures.

### JSON Endpoint Consumption Example:
```java
// Spring WebClient / RestTemplate call to Data Integration API
String cycloneId = "2020139N11086";
DataEnvelopeDto envelope = restTemplate.getForObject(
    "http://localhost:8001/cyclones/" + cycloneId + "/envelope",
    DataEnvelopeDto.class
);
```

### Corresponding Java DTO Mapping:
```java
public record CycloneDto(
    String id,
    String name,
    String basin,
    int season_year,
    String status
) {}

public record ObservationDto(
    String observed_at,
    double latitude,
    double longitude,
    Double wind_speed_kmh,
    Double pressure_hpa,
    Double movement_direction_deg,
    Double movement_speed_kmh,
    String intensity_category
) {}

public record DataEnvelopeDto(
    CycloneDto cyclone,
    ObservationDto observation,
    WeatherDataDto weather,
    SatelliteImageDto satellite,
    SourceInfoDto source
) {}
```

---

## 3. Integration for AI Service Developers (FastAPI / PyTorch / ResNet / XGBoost)

The AI model developers can import the data layer directly as a Python package or consume the prepared satellite image directory.

### Python In-Code Usage:
```python
from data_integration.src.integration import DataIntegrationProvider

provider = DataIntegrationProvider()
provider.initialize()

# Retrieve full envelope (handles offline demo fallback transparently)
envelope = provider.get_cyclone_data("DEMO_AMPHAN_2020")
lat, lon = envelope.observation.latitude, envelope.observation.longitude
wind = envelope.observation.wind_speed_kmh
```

### Loading Satellite Training Data:
```python
import json
from pathlib import Path
from PIL import Image

CATALOG_PATH = Path("data-integration/data/demo/images/catalog.json")
with open(CATALOG_PATH, "r") as f:
    catalog = json.load(f)

for item in catalog:
    image_path = Path("data-integration") / item["storage_path"]
    is_cyclone = item["is_cyclone"]
    image = Image.open(image_path)
    # pass to PyTorch DataLoader / torchvision transform
```

---

## 4. Integration for Frontend Developers (React / Vite / Tailwind)

The frontend can directly poll or fetch track forecasts and demo scenarios for interactive dashboard rendering.

### Fetching Demo Scenarios for UI Dropdowns:
```typescript
interface DemoScenario {
  scenario_id: string;
  title: string;
  description: string;
  cyclone: { id: string; name: string; basin: string; season_year: number; status: string };
  latest_observation: {
    observed_at: string;
    latitude: number;
    longitude: number;
    wind_speed_kmh: number;
    pressure_hpa: number;
    intensity_category: string;
  };
}

export async function fetchDemoScenarios(): Promise<DemoScenario[]> {
  const res = await fetch("http://localhost:8001/demo/scenarios");
  return res.json();
}
```

---

## 5. Schema Validation

All endpoints and data structures conform to the draft-07 JSON schemas stored in:
- `data-integration/schemas/cyclone.json`
- `data-integration/schemas/observation.json`
- `data-integration/schemas/weather.json`
- `data-integration/schemas/demo_scenario.json`
