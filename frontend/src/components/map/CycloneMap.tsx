import "leaflet/dist/leaflet.css";
import { Circle, CircleMarker, MapContainer, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import { useEffect } from "react";

import { useCyclone } from "@/state/cyclone-store";
import { WindParticleCanvas } from "./WindParticleCanvas";

const WORLD_BOUNDS: LatLngBoundsExpression = [
  [-85.051128, -180],
  [85.051128, 180],
];

function Recenter({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lon], 5, { duration: 1.1 });
  }, [lat, lon, map]);
  return null;
}

function MapResizer() {
  const map = useMap();
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 150);
    const handleResize = () => map.invalidateSize();
    window.addEventListener("resize", handleResize);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", handleResize);
    };
  }, [map]);
  return null;
}

export default function CycloneMap() {
  const { cyclone, layers, prediction, compareId, setFocusHour, focusHour } = useCyclone();

  const revealed =
    prediction.status === "idle" ? cyclone.forecast : cyclone.forecast.filter((f) => prediction.revealedHours.includes(f.hour));
  const forecastPoints = revealed;
  const compare = compareId ? cyclone.historical.find((h) => h.id === compareId) : null;

  const hasCoords = cyclone.lat !== 0 || cyclone.lon !== 0;
  const mapLat = hasCoords ? cyclone.lat : 16.0;
  const mapLon = hasCoords ? cyclone.lon : 78.0;

  const validTrack = cyclone.track.filter(
    (p) => typeof p.lat === "number" && typeof p.lon === "number" && (p.lat !== 0 || p.lon !== 0)
  );

  return (
    <div className="relative h-full w-full overflow-hidden rounded-[18px] bg-[#080C14]">
      <MapContainer
        center={[mapLat, mapLon]}
        zoom={5}
        minZoom={3}
        maxZoom={18}
        maxBounds={WORLD_BOUNDS}
        maxBoundsViscosity={1.0}
        className="h-full w-full bg-[#080C14]"
        zoomControl={false}
      >
        <MapResizer />

        {/* Photorealistic Single Earth Imagery Tile Layer */}
        <TileLayer
          attribution="Esri World Imagery"
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
          minZoom={3}
          bounds={WORLD_BOUNDS}
          noWrap={true}
        />

        <Recenter lat={mapLat} lon={mapLon} />

        {/* Historical Past Path */}
        {layers.history && validTrack.length > 1 ? (
          <Polyline positions={validTrack.map((p) => [p.lat, p.lon] as [number, number])} pathOptions={{ color: "#CBD5E1", weight: 2 }} />
        ) : null}

        {/* Forecast Trajectory Line (Toggled by Prediction checkbox) */}
        {layers.prediction && forecastPoints.length > 0 && hasCoords ? (
          <Polyline
            positions={[[cyclone.lat, cyclone.lon], ...forecastPoints.map((f) => [f.lat, f.lon] as [number, number])]}
            pathOptions={{ color: "#38BDF8", weight: 2.5, dashArray: "5 7" }}
          />
        ) : null}

        {/* Confidence Corridor & Cyclone Intensity Circles (Toggled by Confidence Corridor checkbox) */}
        {layers.corridor && hasCoords ? (
          <>
            {/* Core Eyewall Intensity Circle around storm center */}
            <Circle
              center={[cyclone.lat, cyclone.lon]}
              radius={Math.max(35000, Math.min(65000, (cyclone.windKph || 70) * 450))}
              pathOptions={{
                color: "#EF4444",
                weight: 1.5,
                fillColor: "#EF4444",
                fillOpacity: 0.12,
              }}
            >
              <Popup>
                <div className="font-display text-[11px] font-bold text-red-500">Core Eyewall Intensity</div>
                <div className="text-[11px] text-muted-foreground">High velocity storm core (~{Math.round(Math.max(35, Math.min(65, (cyclone.windKph || 70) * 0.45)))} km radius)</div>
              </Popup>
            </Circle>

            {/* Storm-Force Wind Radius Circle around storm center */}
            <Circle
              center={[cyclone.lat, cyclone.lon]}
              radius={Math.max(70000, Math.min(130000, (cyclone.windKph || 70) * 900))}
              pathOptions={{
                color: "#0284C7",
                weight: 1.2,
                fillColor: "#0284C7",
                fillOpacity: 0.06,
              }}
            >
              <Popup>
                <div className="font-display text-[11px] font-bold text-sky-400">Storm Wind Radius (50kt)</div>
                <div className="text-[11px] text-muted-foreground">Sustained storm force wind field (~{Math.round(Math.max(70, Math.min(130, (cyclone.windKph || 70) * 0.9)))} km radius)</div>
              </Popup>
            </Circle>

            {/* Outer Circulation Radius Circle around storm center */}
            <Circle
              center={[cyclone.lat, cyclone.lon]}
              radius={Math.max(120000, Math.min(210000, (cyclone.windKph || 70) * 1500))}
              pathOptions={{
                color: "#38BDF8",
                weight: 1,
                dashArray: "5 7",
                fillColor: "#38BDF8",
                fillOpacity: 0.03,
              }}
            >
              <Popup>
                <div className="font-display text-[11px] font-bold text-cyan-400">Gale / Outer Circulation Radius (34kt)</div>
                <div className="text-[11px] text-muted-foreground">Outer tropical storm circulation limit (~{Math.round(Math.max(120, Math.min(210, (cyclone.windKph || 70) * 1.5)))} km radius)</div>
              </Popup>
            </Circle>

            {/* Forecast Waypoint Uncertainty Circles */}
            {forecastPoints.map((f) => (
              <Circle
                key={`cor-${f.hour}`}
                center={[f.lat, f.lon]}
                radius={f.confidenceRadiusKm * 1000}
                pathOptions={{
                  color: "#38BDF8",
                  weight: 1.2,
                  dashArray: "4 6",
                  fillColor: "#38BDF8",
                  fillOpacity: 0.08,
                }}
              >
                <Popup>
                  <div className="font-display text-[11px] font-bold text-cyan-400">+{f.hour}H Confidence Corridor</div>
                  <div className="text-[11px] text-muted-foreground">Estimated track uncertainty cone: ±{f.confidenceRadiusKm} km</div>
                </Popup>
              </Circle>
            ))}
          </>
        ) : null}

        {/* Risk Zone Impact Circle */}
        {layers.risk && cyclone.risk.score > 0 && hasCoords ? (
          <Circle
            center={[
              cyclone.forecast[cyclone.forecast.length - 1]?.lat ?? cyclone.lat,
              cyclone.forecast[cyclone.forecast.length - 1]?.lon ?? cyclone.lon,
            ]}
            radius={cyclone.risk.score * 5000}
            pathOptions={{ color: cyclone.risk.level === "LOW" ? "#10B981" : "#EF4444", weight: 1, fillOpacity: 0.12 }}
          />
        ) : null}

        {/* Historical Compare Storm */}
        {compare && compare.track.length > 0 ? (
          <Polyline
            positions={compare.track.map((p) => [p.lat, p.lon] as [number, number])}
            pathOptions={{ color: "#F59E0B", weight: 1.8, dashArray: "3 6" }}
          />
        ) : null}

        {/* Minimalist Forecast Waypoint Nodes (Toggled by Prediction checkbox) */}
        {layers.prediction
          ? forecastPoints.map((f) => {
              const isFocused = focusHour === f.hour;
              return (
                <CircleMarker
                  key={`pred-node-${f.hour}`}
                  center={[f.lat, f.lon]}
                  radius={isFocused ? 7 : 5}
                  pathOptions={{
                    color: isFocused ? "#FFFFFF" : "#38BDF8",
                    fillColor: isFocused ? "#0284C7" : "#0F172A",
                    fillOpacity: 0.95,
                    weight: isFocused ? 2.5 : 1.8,
                  }}
                  eventHandlers={{ click: () => setFocusHour(isFocused ? null : f.hour) }}
                >
                  <Popup>
                    <div className="font-display text-[11px] font-semibold uppercase tracking-wider text-primary">+{f.hour}H Telemetry Prediction</div>
                    <div className="mt-1 font-mono text-[12px] text-foreground">
                      {f.lat.toFixed(1)}°N {f.lon.toFixed(1)}°E
                    </div>
                    <div className="text-[11px] text-muted-foreground">Confidence: ±{f.confidenceRadiusKm} km</div>
                    <div className="text-[11px] text-muted-foreground">
                      {f.windKph > 0 ? `${f.windKph} km/h` : "Pending"} · {f.intensityTrend}
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })
          : null}

        {/* Sleek Live Cyclone Pinpoint */}
        {hasCoords ? (
          <CircleMarker
            center={[cyclone.lat, cyclone.lon]}
            radius={8}
            pathOptions={{ color: "#FFFFFF", fillColor: "#EF4444", fillOpacity: 1, weight: 2 }}
          >
            <Popup>
              <div className="font-display text-[11px] font-bold uppercase tracking-wider text-red-600">{cyclone.name}</div>
              <div className="mt-0.5 font-mono text-[12px] font-medium">
                {cyclone.windKph > 0 ? `${cyclone.windKph} km/h` : "Wind unavailable"} · {cyclone.pressureHpa > 0 ? `${cyclone.pressureHpa} hPa` : ""}
              </div>
              <div className="text-[11px] text-muted-foreground">{cyclone.category}</div>
            </Popup>
          </CircleMarker>
        ) : null}

        {/* Wind Vortex Streamlines anchored to storm center */}
        {layers.wind && hasCoords && (cyclone.windKph > 0 || cyclone.lat !== 0) ? (
          <WindParticleCanvas lat={cyclone.lat} lon={cyclone.lon} speed={Math.max(0.6, cyclone.windKph / 120)} />
        ) : null}
      </MapContainer>
    </div>
  );
}
