import { useQuery } from '@tanstack/react-query'

import { stormsApi } from '../api/storms'

/**
 * Full analysis for one instant, fetched on demand.
 *
 * `placeholderData: keepPreviousData` matters more than it looks: while scrubbing, the
 * previously loaded frame stays on screen instead of the panel emptying between
 * requests, so the detail panel does not flicker as the cursor moves.
 */
export function useFrame(sid: string | null, t: string | null) {
  return useQuery({
    queryKey: ['frame', sid, t],
    queryFn: () => stormsApi.frame(sid as string, t as string),
    enabled: Boolean(sid && t),
    staleTime: Infinity,
    placeholderData: (previous) => previous,
  })
}
