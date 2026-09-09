import type { GeoJSONSource, Map as MapLibreMap } from 'maplibre-gl'
import type { Feature, FeatureCollection } from 'geojson'

import type { ForecastResponse, TrackFrame } from '../../../types/api'

/**
 * Map layers, driven imperatively.
 *
 * MapLibre owns a WebGL canvas and its own layer graph. Wrapping that in a declarative
 * component tree buys very little for the five layers we need and adds a version-compat
 * dependency, so `StormMap` owns the instance and these functions update sources on it.
 * Everything is scoped to this folder, which is also what makes a swap to Leaflet a
 * local change rather than a rewrite.
 */

export const OBSERVED_TRACK_SOURCE = 'observed-track'
export const OBSERVED_TRACK_LINE = 'observed-track-line'
export const OBSERVED_TRACK_POINTS = 'observed-track-points'
export const CURRENT_POSITION_SOURCE = 'current-position'
export const CURRENT_POSITION_LAYER = 'current-position-marker'

export const FORECAST_SOURCE = 'forecast-track'
export const FORECAST_LINE = 'forecast-track-line'
export const CONE_SOURCE = 'forecast-cone'
export const CONE_FILL = 'forecast-cone-fill'

export const TRUTH_SOURCE = 'observed-future'
export const TRUTH_LINE = 'observed-future-line'

export const ANALOGUE_SOURCE = 'analogue-tracks'
export const ANALOGUE_LINE = 'analogue-tracks-line'

function emptyCollection(): FeatureCollection {
  return { type: 'FeatureCollection', features: [] }
}

function setData(map: MapLibreMap, sourceId: string, data: FeatureCollection) {
  const source = map.getSource(sourceId)
  if (source && 'setData' in source) {
    ;(source as GeoJSONSource).setData(data)
  }
}

/** Registers every source and layer once, on map load. */
export function installLayers(map: MapLibreMap) {
  const sources = [
    OBSERVED_TRACK_SOURCE,
    CURRENT_POSITION_SOURCE,
    FORECAST_SOURCE,
    CONE_SOURCE,
    TRUTH_SOURCE,
    ANALOGUE_SOURCE,
  ]
  for (const id of sources) {
    if (!map.getSource(id)) {
      map.addSource(id, { type: 'geojson', data: emptyCollection() })
    }
  }

  // Analogue tracks sit at the bottom: they are context, not the subject.
  if (!map.getLayer(ANALOGUE_LINE)) {
    map.addLayer({
      id: ANALOGUE_LINE,
      type: 'line',
      source: ANALOGUE_SOURCE,
      paint: {
        'line-color': '#8791ac',
        'line-width': 1,
        'line-opacity': 0.35,
      },
    })
  }

  if (!map.getLayer(CONE_FILL)) {
    map.addLayer({
      id: CONE_FILL,
      type: 'fill',
      source: CONE_SOURCE,
      paint: {
        'fill-color': '#4dd4ce',
        'fill-opacity': ['case', ['==', ['get', 'band'], 'p90'], 0.06, 0.12],
      },
    })
  }

  // Observed track uses the truth colour and is never accented — the accent is reserved
  // for AI output, so a viewer can tell measurement from prediction without a legend.
  if (!map.getLayer(OBSERVED_TRACK_LINE)) {
    map.addLayer({
      id: OBSERVED_TRACK_LINE,
      type: 'line',
      source: OBSERVED_TRACK_SOURCE,
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#e8eaf0', 'line-width': 1.8, 'line-opacity': 0.85 },
    })
  }

  if (!map.getLayer(OBSERVED_TRACK_POINTS)) {
    map.addLayer({
      id: OBSERVED_TRACK_POINTS,
      type: 'circle',
      source: OBSERVED_TRACK_SOURCE,
      filter: ['==', ['geometry-type'], 'Point'],
      paint: {
        'circle-radius': 2,
        'circle-color': '#e8eaf0',
        'circle-opacity': 0.5,
      },
    })
  }

  // Forecast is dashed and accented: it is a claim, not an observation.
  if (!map.getLayer(FORECAST_LINE)) {
    map.addLayer({
      id: FORECAST_LINE,
      type: 'line',
      source: FORECAST_SOURCE,
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: {
        'line-color': '#4dd4ce',
        'line-width': 2,
        'line-dasharray': [2, 2],
      },
    })
  }

  // Ground truth revealed during verification: solid, drawn over the prediction.
  if (!map.getLayer(TRUTH_LINE)) {
    map.addLayer({
      id: TRUTH_LINE,
      type: 'line',
      source: TRUTH_SOURCE,
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#e8eaf0', 'line-width': 2.4 },
    })
  }

  if (!map.getLayer(CURRENT_POSITION_LAYER)) {
    map.addLayer({
      id: CURRENT_POSITION_LAYER,
      type: 'circle',
      source: CURRENT_POSITION_SOURCE,
      paint: {
        'circle-radius': 6,
        'circle-color': '#e8eaf0',
        'circle-stroke-color': '#0b1020',
        'circle-stroke-width': 2,
      },
    })
  }
}

/** Draws the observed track for the whole storm, plus a dot per observation. */
export function updateObservedTrack(map: MapLibreMap, frames: TrackFrame[]) {
  const line: Feature = {
    type: 'Feature',
    properties: {},
    geometry: {
      type: 'LineString',
      coordinates: frames.map((f) => [f.lon, f.lat]),
    },
  }
  const points: Feature[] = frames.map((f) => ({
    type: 'Feature',
    properties: { t: f.t, vmaxKt: f.vmaxKt },
    geometry: { type: 'Point', coordinates: [f.lon, f.lat] },
  }))

  setData(map, OBSERVED_TRACK_SOURCE, {
    type: 'FeatureCollection',
    features: frames.length >= 2 ? [line, ...points] : points,
  })
}

/** Moves the storm marker to the scrubber's current frame. */
export function updateCurrentPosition(map: MapLibreMap, frame: TrackFrame | null) {
  setData(map, CURRENT_POSITION_SOURCE, {
    type: 'FeatureCollection',
    features: frame
      ? [
          {
            type: 'Feature',
            properties: { t: frame.t },
            geometry: { type: 'Point', coordinates: [frame.lon, frame.lat] },
          },
        ]
      : [],
  })
}

/**
 * Draws the predicted track and its uncertainty cone.
 *
 * A point with no cone radii draws no cone. That is deliberate: an uncalibrated cone
 * would be the single most misleading thing on the map, because its width *is* the
 * product's visual statement about uncertainty.
 */
export function updateForecast(
  map: MapLibreMap,
  forecast: ForecastResponse | null,
  origin: TrackFrame | null,
) {
  if (!forecast || forecast.trackForecast.points.length === 0) {
    setData(map, FORECAST_SOURCE, emptyCollection())
    setData(map, CONE_SOURCE, emptyCollection())
    return
  }

  const points = [...forecast.trackForecast.points].sort(
    (a, b) => a.leadHours - b.leadHours,
  )
  const coordinates: [number, number][] = origin
    ? [[origin.lon, origin.lat], ...points.map((p): [number, number] => [p.lon, p.lat])]
    : points.map((p): [number, number] => [p.lon, p.lat])

  setData(map, FORECAST_SOURCE, {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: {},
        geometry: { type: 'LineString', coordinates },
      },
    ],
  })

  const coneFeatures: Feature[] = []
  for (const point of points) {
    if (point.coneRadiusP90Km != null) {
      coneFeatures.push(circle(point.lon, point.lat, point.coneRadiusP90Km, 'p90'))
    }
    if (point.coneRadiusP67Km != null) {
      coneFeatures.push(circle(point.lon, point.lat, point.coneRadiusP67Km, 'p67'))
    }
  }
  setData(map, CONE_SOURCE, { type: 'FeatureCollection', features: coneFeatures })
}

/** Draws what actually happened, over the prediction. The Verify reveal. */
export function updateTruthOverlay(
  map: MapLibreMap,
  forecast: ForecastResponse | null,
  origin: TrackFrame | null,
) {
  const verification = forecast?.verification
  if (!verification?.available) {
    setData(map, TRUTH_SOURCE, emptyCollection())
    return
  }

  const observed = [verification.observedAt24h, verification.observedAt48h].filter(
    (p): p is NonNullable<typeof p> => p != null,
  )
  if (observed.length === 0) {
    setData(map, TRUTH_SOURCE, emptyCollection())
    return
  }

  const coordinates: [number, number][] = origin
    ? [[origin.lon, origin.lat], ...observed.map((p): [number, number] => [p.lon, p.lat])]
    : observed.map((p): [number, number] => [p.lon, p.lat])

  setData(map, TRUTH_SOURCE, {
    type: 'FeatureCollection',
    features: [
      { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates } },
    ],
  })
}

/** Faint spaghetti of what the closest historical analogues did next. */
export function updateAnalogueTracks(map: MapLibreMap, forecast: ForecastResponse | null) {
  const matches = forecast?.analogues.matches ?? []
  setData(map, ANALOGUE_SOURCE, {
    type: 'FeatureCollection',
    features: matches
      .filter((m) => m.onwardTrack.length >= 2)
      .map((m) => ({
        type: 'Feature',
        properties: { sid: m.sid, similarity: m.similarity },
        geometry: {
          type: 'LineString',
          coordinates: m.onwardTrack.map(([lat, lon]) => [lon, lat]),
        },
      })),
  })
}

/** A geodesic-ish circle for the cone bands. 48 segments is smooth at demo zoom levels. */
function circle(
  lon: number,
  lat: number,
  radiusKm: number,
  band: string,
  segments = 48,
): Feature {
  const coordinates: [number, number][] = []
  const latRadius = radiusKm / 110.574
  const lonRadius = radiusKm / (111.32 * Math.cos((lat * Math.PI) / 180) || 1)

  for (let i = 0; i <= segments; i += 1) {
    const angle = (i / segments) * 2 * Math.PI
    coordinates.push([lon + lonRadius * Math.cos(angle), lat + latRadius * Math.sin(angle)])
  }

  return {
    type: 'Feature',
    properties: { band },
    geometry: { type: 'Polygon', coordinates: [coordinates] },
  }
}
