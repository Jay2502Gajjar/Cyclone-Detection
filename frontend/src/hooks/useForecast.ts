import { useMutation } from '@tanstack/react-query'

import { forecastApi } from '../api/forecast'

/**
 * Rewind & Verify.
 *
 * A mutation rather than a query because running a forecast is an explicit act the user
 * takes at a chosen moment, and because it writes a forecast_run row on the server.
 */
export function useForecast(sid: string | null) {
  return useMutation({
    mutationFn: ({ from, reveal }: { from: string; reveal: boolean }) =>
      forecastApi.run(sid as string, from, reveal),
  })
}
