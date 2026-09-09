import type { ImageSource, Map as MapLibreMap } from 'maplibre-gl'

import type { TrackFrame } from '../../../types/api'

/**
 * The georeferenced infrared satellite frame, pinned to the storm's position.
 *
 * This is the single most important visual in the application: it is what turns a track
 * on a map into a storm. It is redrawn on every scrub, so the update path has to be
 * cheap — MapLibre's image source lets us swap the URL and the corner coordinates
 * without tearing down layers.
 *
 * The footprint is approximate. HURSAT-B1 tiles are storm-centred on an equal-angle
 * grid, so we place a square of the tile's ground width around the storm centre. That is
 * accurate enough to read at basin zoom and honest about being a placement, not a
 * reprojection; Phase 1 replaces the assumed width with the value parsed from the file.
 */

export const IR_SOURCE = 'ir-frame'
export const IR_LAYER = 'ir-frame-layer'

/** HURSAT-B1 IRWIN: roughly 301 pixels at ~8 km. Overridden per source in Phase 1. */
const DEFAULT_TILE_WIDTH_KM = 301 * 8

let currentUrl: string | null = null

function corners(lat: number, lon: number, widthKm: number) {
  const halfLat = widthKm / 2 / 110.574
  const halfLon = widthKm / 2 / (111.32 * Math.cos((lat * Math.PI) / 180) || 1)

  // Clockwise from top-left, as MapLibre's image source expects.
  return [
    [lon - halfLon, lat + halfLat],
    [lon + halfLon, lat + halfLat],
    [lon + halfLon, lat - halfLat],
    [lon - halfLon, lat - halfLat],
  ] as [[number, number], [number, number], [number, number], [number, number]]
}

/**
 * Places the IR frame for the current scrubber position.
 *
 * Passing a frame with no imagery removes the overlay rather than leaving a stale image
 * behind — showing the previous frame's satellite picture at a new timestamp would be a
 * quiet lie about what was observed.
 */
export function updateIrOverlay(
  map: MapLibreMap,
  frame: TrackFrame | null,
  imageUrl: string | null,
  widthKm: number = DEFAULT_TILE_WIDTH_KM,
) {
  if (!frame || !imageUrl) {
    removeIrOverlay(map)
    return
  }

  const coords = corners(frame.lat, frame.lon, widthKm)

  if (currentUrl === imageUrl && map.getSource(IR_SOURCE)) {
    const source = map.getSource(IR_SOURCE) as ImageSource
    source.setCoordinates(coords)
    return
  }

  removeIrOverlay(map)
  map.addSource(IR_SOURCE, { type: 'image', url: imageUrl, coordinates: coords })
  map.addLayer(
    {
      id: IR_LAYER,
      type: 'raster',
      source: IR_SOURCE,
      paint: { 'raster-opacity': 0.72, 'raster-fade-duration': 0 },
    },
    // Beneath the tracks: the imagery is the ground the analysis is drawn on.
    map.getLayer('analogue-tracks-line') ? 'analogue-tracks-line' : undefined,
  )
  currentUrl = imageUrl
}

export function removeIrOverlay(map: MapLibreMap) {
  if (map.getLayer(IR_LAYER)) map.removeLayer(IR_LAYER)
  if (map.getSource(IR_SOURCE)) map.removeSource(IR_SOURCE)
  currentUrl = null
}
