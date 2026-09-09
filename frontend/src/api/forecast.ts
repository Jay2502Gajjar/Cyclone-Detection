import type { ForecastResponse } from '../types/api'
import { api } from './client'

export const forecastApi = {
  /**
   * Rewind & Verify.
   *
   * `from` is the temporal-mask boundary: the backend loads only observations at or
   * before it, and the AI service rejects anything later. `reveal` controls whether
   * ground truth is attached afterwards — it never changes what the models were given.
   */
  run: (sid: string, from: string, reveal: boolean) =>
    api.post<ForecastResponse>(
      `/api/storms/${encodeURIComponent(sid)}/forecast` +
        `?from=${encodeURIComponent(from)}&reveal=${reveal}`,
    ),
}
