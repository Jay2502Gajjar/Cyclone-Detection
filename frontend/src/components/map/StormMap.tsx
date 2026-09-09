import { LngLatBounds, Map as MapLibreMap, NavigationControl } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useEffect, useRef } from 'react'

import { mediaUrl } from '../../api/client'
import type { ForecastResponse, StormDetail, TrackFrame } from '../../types/api'
import { updateIrOverlay } from './layers/irOverlay'
import {
  installLayers,
  updateAnalogueTracks,
  updateCurrentPosition,
  updateForecast,
  updateObservedTrack,
  updateTruthOverlay,
} from './layers/track'

/**
 * The map. It is the page background, at full bleed, and everything else floats on it.
 *
 * It owns the MapLibre instance and updates layers imperatively as props change. React
 * never re-creates the map; only the data in its sources changes, which is what keeps
 * scrubbing at 60fps.
 *
 * Basemap: CARTO dark-matter, which is free and needs no API key — one less thing that
 * can fail on a venue network during a demo.
 */

const BASEMAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

const DEFAULT_CENTER: [number, number] = [86, 17] // Bay of Bengal
const DEFAULT_ZOOM = 4.2

export function StormMap({
  storm,
  currentFrame,
  forecast,
}: {
  storm: StormDetail | undefined
  currentFrame: TrackFrame | null
  forecast: ForecastResponse | null
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const readyRef = useRef(false)
  const fittedSidRef = useRef<string | null>(null)

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = new MapLibreMap({
      container: containerRef.current,
      style: BASEMAP_STYLE,
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      attributionControl: { compact: true },
    })
    map.addControl(new NavigationControl({ showCompass: false }), 'bottom-right')

    map.on('load', () => {
      installLayers(map)
      readyRef.current = true
    })

    mapRef.current = map
    return () => {
      readyRef.current = false
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Observed track, redrawn when the selected storm changes.
  useEffect(() => {
    const map = mapRef.current
    if (!map || !readyRef.current || !storm) return

    updateObservedTrack(map, storm.frames)

    // Fit once per storm. Refitting on every scrub would fight the user's own panning.
    if (storm.frames.length > 0 && fittedSidRef.current !== storm.sid) {
      const bounds = new LngLatBounds()
      for (const frame of storm.frames) bounds.extend([frame.lon, frame.lat])
      map.fitBounds(bounds, { padding: 140, duration: 400, maxZoom: 6 })
      fittedSidRef.current = storm.sid
    }
  }, [storm])

  // The scrubber's frame: marker and satellite imagery move together.
  useEffect(() => {
    const map = mapRef.current
    if (!map || !readyRef.current) return

    updateCurrentPosition(map, currentFrame)
    updateIrOverlay(map, currentFrame, mediaUrl(currentFrame?.imageUrl))
  }, [currentFrame])

  // Forecast, cone, analogues and the verification reveal.
  useEffect(() => {
    const map = mapRef.current
    if (!map || !readyRef.current) return

    updateForecast(map, forecast, currentFrame)
    updateAnalogueTracks(map, forecast)
    updateTruthOverlay(map, forecast, currentFrame)
  }, [forecast, currentFrame])

  return <div ref={containerRef} className="absolute inset-0" aria-label="Cyclone map" />
}
