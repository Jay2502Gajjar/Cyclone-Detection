import { useQuery } from '@tanstack/react-query'

import { stormsApi } from '../api/storms'

/**
 * The whole storm — metadata and every frame — in one query.
 *
 * Held forever once fetched. The scrubber reads this cached array on every drag, so a
 * refetch mid-scrub would be both pointless and visible.
 */
export function useStorm(sid: string | null) {
  return useQuery({
    queryKey: ['storm', sid],
    queryFn: () => stormsApi.detail(sid as string),
    enabled: Boolean(sid),
    staleTime: Infinity,
  })
}
