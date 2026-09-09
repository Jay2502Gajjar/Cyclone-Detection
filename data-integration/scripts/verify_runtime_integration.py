"""
Runtime Integration Verification Script for CycloVision
Tests complete runtime integration between FastAPI Data Integration service (port 8001)
and Spring Boot backend (port 8080).
"""
import json
import urllib.request
import urllib.error
import sys

SPRING_BOOT_URL = "http://localhost:8080"
FASTAPI_URL = "http://localhost:8001"


def http_get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post(url):
    req = urllib.request.Request(url, method="POST", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("=" * 70)
    print("CYCLOVISION REAL END-TO-END RUNTIME INTEGRATION TEST")
    print("=" * 70)

    # 1. Check health
    print("\n1. Verifying service health...")
    fastapi_health = http_get(f"{FASTAPI_URL}/health")
    print(f"   FastAPI (:8001): {fastapi_health.get('status')} | Service: {fastapi_health.get('service')} | Cyclones: {fastapi_health.get('sources', {}).get('ibtracs_cyclones_count')}")
    sb_health = http_get(f"{SPRING_BOOT_URL}/actuator/health")
    print(f"   Spring Boot (:8080): {sb_health.get('status')}")

    # 2. Get all cyclones from Spring Boot
    print("\n2. Fetching cyclones from Spring Boot DB via GET /api/cyclones...")
    sb_cyclones = http_get(f"{SPRING_BOOT_URL}/api/cyclones")
    print(f"   Total cyclones returned by Spring Boot: {len(sb_cyclones)}")

    # Index by externalId and by name
    by_ext_id = {c.get("externalId"): c for c in sb_cyclones}
    by_name = {c.get("name"): c for c in sb_cyclones if c.get("name")}

    # 3. Test representative cyclones
    targets = [
        {"name": "AMPHAN", "sid": "2020136N10088"},
        {"name": "FANI", "sid": "2019116N02090"},
        {"name": "MOCHA", "sid": "2023129N08091"},
    ]

    all_verified = True
    print("\n3. Verifying Representative Cyclones:")

    for t in targets:
        name = t["name"]
        sid = t["sid"]
        print(f"\n   --- Checking Cyclone: {name} (SID: {sid}) ---")

        # Spring Boot cyclone entity
        sb_cyclone = by_ext_id.get(sid) or by_name.get(name)
        if not sb_cyclone:
            print(f"   [FAIL] {name} not found in Spring Boot DB!")
            all_verified = False
            continue

        sb_id = sb_cyclone.get("id")
        print(f"   Spring Boot ID: {sb_id}")
        print(f"   External ID / SID: {sb_cyclone.get('externalId')}")
        print(f"   Name: {sb_cyclone.get('name')}")
        print(f"   Basin: {sb_cyclone.get('basin')}")
        print(f"   Status: {sb_cyclone.get('status')}")

        # Fetch observations from Spring Boot
        sb_obs = http_get(f"{SPRING_BOOT_URL}/api/cyclones/{sb_id}/observations")
        print(f"   Spring Boot Observations Count: {len(sb_obs)}")

        # Fetch observations from FastAPI Data Integration
        py_obs_resp = http_get(f"{FASTAPI_URL}/cyclones/{sid}/observations")
        py_obs = py_obs_resp if isinstance(py_obs_resp, list) else py_obs_resp.get("data", [])
        print(f"   FastAPI Observations Count: {len(py_obs)}")

        if len(sb_obs) == 0:
            print(f"   [FAIL] {name} has 0 observations in Spring Boot!")
            all_verified = False
            continue

        # Check latest / peak values
        first_sb_obs = sb_obs[0]
        last_sb_obs = sb_obs[-1]
        print(f"   First Obs: time={first_sb_obs.get('observedAt')}, lat={first_sb_obs.get('latitude')}, lon={first_sb_obs.get('longitude')}, wind={first_sb_obs.get('windSpeedKph')} km/h, pres={first_sb_obs.get('pressureHpa')} hPa")
        print(f"   Last Obs:  time={last_sb_obs.get('observedAt')}, lat={last_sb_obs.get('latitude')}, lon={last_sb_obs.get('longitude')}, wind={last_sb_obs.get('windSpeedKph')} km/h, pres={last_sb_obs.get('pressureHpa')} hPa")

        # Peak wind comparison
        sb_max_wind = max((o.get("windSpeedKph") or 0) for o in sb_obs)
        sb_min_pres = min((o.get("pressureHpa") or 9999) for o in sb_obs if o.get("pressureHpa") is not None)
        py_max_wind = max((o.get("wind_speed_kmh") or 0) for o in py_obs)
        py_min_pres = min((o.get("pressure_hpa") or 9999) for o in py_obs if o.get("pressure_hpa") is not None)

        print(f"   Peak Wind: Spring Boot = {sb_max_wind} km/h | FastAPI = {py_max_wind} km/h")
        print(f"   Min Pressure: Spring Boot = {sb_min_pres} hPa | FastAPI = {py_min_pres} hPa")

        # Consistency check
        if len(sb_obs) == len(py_obs) and abs(sb_max_wind - py_max_wind) < 0.1:
            print(f"   [PASS] {name} matches perfectly between Python Data Integration and Spring Boot!")
        else:
            print(f"   [WARN/FAIL] Count or value mismatch for {name}: SB={len(sb_obs)} vs PY={len(py_obs)}")
            all_verified = False

    # 4. Deduplication test
    print("\n4. Testing Duplicate Ingestion Prevention...")
    initial_count = len(sb_cyclones)
    amphan_sb_id = (by_ext_id.get("2020136N10088") or by_name.get("AMPHAN", {})).get("id")
    initial_amphan_obs = len(http_get(f"{SPRING_BOOT_URL}/api/cyclones/{amphan_sb_id}/observations")) if amphan_sb_id else 0

    print(f"   Initial Cyclone Count: {initial_count}")
    print(f"   Initial AMPHAN Obs Count: {initial_amphan_obs}")
    print("   Triggering Ingestion a 2nd time: POST /api/internal/ingest/trigger...")
    trigger_resp = http_post(f"{SPRING_BOOT_URL}/api/internal/ingest/trigger")
    print(f"   Trigger Response: {trigger_resp}")

    post_dup_cyclones = http_get(f"{SPRING_BOOT_URL}/api/cyclones")
    post_dup_count = len(post_dup_cyclones)
    post_amphan_obs = len(http_get(f"{SPRING_BOOT_URL}/api/cyclones/{amphan_sb_id}/observations")) if amphan_sb_id else 0

    print(f"   Post-trigger Cyclone Count: {post_dup_count}")
    print(f"   Post-trigger AMPHAN Obs Count: {post_amphan_obs}")

    if post_dup_count == initial_count and post_amphan_obs == initial_amphan_obs:
        print("   [PASS] Deduplication verified: No duplicate cyclones or observations created!")
    else:
        print(f"   [FAIL] Deduplication failed: count grew from {initial_count} to {post_dup_count}")
        all_verified = False

    print("\n" + "=" * 70)
    if all_verified:
        print("RESULT: ALL INTEGRATION CHECKS PASSED")
    else:
        print("RESULT: INTEGRATION CHECKS HAD FAILURES")
    print("=" * 70)


if __name__ == "__main__":
    main()
