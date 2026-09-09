/** Formatting helpers. Kept in one place so units are written the same way everywhere. */

export function formatUtc(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.toISOString().slice(0, 10)} ${d.toISOString().slice(11, 16)} UTC`
}

export function formatDay(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
}

export function knots(value: number | null | undefined): string {
  return value == null ? '—' : `${Math.round(value)} kt`
}

export function hpa(value: number | null | undefined): string {
  return value == null ? '—' : `${Math.round(value)} hPa`
}

export function km(value: number | null | undefined): string {
  return value == null ? '—' : `${Math.round(value)} km`
}

export function kelvin(value: number | null | undefined): string {
  return value == null ? '—' : `${value.toFixed(1)} K`
}

export function ratio(value: number | null | undefined, digits = 2): string {
  return value == null ? '—' : value.toFixed(digits)
}

export function percent(value: number | null | undefined): string {
  return value == null ? '—' : `${Math.round(value * 100)}%`
}

export function signedKnots(value: number | null | undefined): string {
  if (value == null) return '—'
  const rounded = Math.round(value)
  return `${rounded > 0 ? '+' : ''}${rounded} kt`
}

/** Storm categories arrive as SCREAMING_SNAKE; titles read better. */
export function humaniseCategory(category: string | null | undefined): string {
  if (!category) return '—'
  return category
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
