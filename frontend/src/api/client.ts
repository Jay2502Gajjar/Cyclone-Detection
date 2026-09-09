/**
 * The HTTP client. Native fetch — a wrapper library would earn nothing here.
 *
 * The one job beyond fetching is turning the backend's error envelope into a thrown
 * `ApiRequestError` with its code intact, so callers can distinguish "this storm has no
 * frame at that instant" from "the AI service is down" without parsing strings.
 */

import type { ApiError } from '../types/api'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiRequestError extends Error {
  readonly code: string
  readonly status: number
  readonly detail?: string | null

  constructor(status: number, error: ApiError) {
    super(error.message)
    this.name = 'ApiRequestError'
    this.code = error.code
    this.status = status
    this.detail = error.detail
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { Accept: 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })

  if (!response.ok) {
    let error: ApiError = {
      code: 'UNKNOWN',
      message: `${response.status} ${response.statusText}`,
    }
    try {
      error = (await response.json()) as ApiError
    } catch {
      // Non-JSON error body (a proxy timeout, say). The status line above stands.
    }
    throw new ApiRequestError(response.status, error)
  }

  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'POST',
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
}

/** Resolves a `/media/...` path returned by the API against the configured origin. */
export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null
  return path.startsWith('http') ? path : `${BASE_URL}${path}`
}
