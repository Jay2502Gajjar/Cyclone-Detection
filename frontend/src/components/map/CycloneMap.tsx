import "leaflet/dist/leaflet.css";
import { Circle, CircleMarker, MapContainer, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import { useEffect } from "react";

import { useCyclone } from "@/state/cyclone-store";
import { WindParticleCanvas } from "./WindParticleCanvas";

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
  const forecast = layers.prediction ? revealed : [];
  const compare = compareId ? cyclone.historical.find((h) => h.id === compareId) : null;

  const hasCoords = cyclone.lat !== 0 || cyclone.lon !== 0;
  const mapLat = hasCoords ? cyclone.lat : 16.0;
  const mapLon = hasCoords ? cyclone.lon : 78.0;

  return (
    <div className="relative h-full w-full overflow-hidden rounded-[18px]">
      <MapContainer center={[mapLat, mapLon]} zoom={5} className="h-full w-full" zoomControl={false}>
        <MapResizer />

        {/* Photorealistic Satellite Earth Imagery */}
        <TileLayer
          attribution="Esri World Imagery"
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
        />

        <Recenter lat={mapLat} lon={mapLon} />

        {/* Historical Past Path */}
        {layers.history && cyclone.track.length > 1 ? (
          <Polyline positions={cyclone.track.map((p) => [p.lat, p.lon] as [number, number])} pathOptions={{ color: "#CBD5E1", weight: 2 }} />
        ) : null}

        {/* Forecast Trajectory Line */}
        {forecast.length > 0 && hasCoords ? (
          <Polyline
            positions={[[cyclone.lat, cyclone.lon], ...forecast.map((f) => [f.lat, f.lon] as [number, number])]}
            pathOptions={{ color: "#38BDF8", weight: 2.5, dashArray: "5 7" }}
          />
        ) : null}

        {/* Uncertainty Confidence Corridor */}
        {layers.corridor
          ? forecast.map((f) => (
            <Circle
              key={`cor-${f.hour}`}
              center={[f.lat, f.lon]}
              radius={f.confidenceRadiusKm * 1000}
              pathOptions={{ color: "#38BDF8", weight: 1, fillOpacity: 0.08 }}
            />
          ))
          : null}

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

        {/* Minimalist Forecast Waypoint Nodes */}
        {forecast.map((f) => {
          const isFocused = focusHour === f.hour;
          return (
            <CircleMarker
              key={f.hour}
              center={[f.lat, f.lon]}
              radius={isFocused ? 6 : 4}
              pathOptions={{
                color: isFocused ? "#FFFFFF" : "#38BDF8",
                fillColor: isFocused ? "#0284C7" : "#0F172A",
                fillOpacity: 0.95,
                weight: isFocused ? 2 : 1.5,
              }}
              eventHandlers={{ click: () => setFocusHour(isFocused ? null : f.hour) }}
            >
              <Popup>
                <div className="font-display text-[11px] font-semibold uppercase tracking-wider text-primary">+{f.hour}H Telemetry</div>
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
        })}

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
      </MapContainer>

      {layers.wind && cyclone.windKph > 0 ? <WindParticleCanvas speed={cyclone.windKph / 120} /> : null}
    </div>
  );
}
