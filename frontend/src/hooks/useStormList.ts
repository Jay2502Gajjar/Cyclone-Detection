import { useQuery } from '@tanstack/react-query'

import { stormsApi } from '../api/storms'

export function useStormList() {
  return useQuery({
    queryKey: ['storms'],
    queryFn: stormsApi.list,
    staleTime: Infinity, // the curated storm set does not change while the app is open
  })
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: stormsApi.health,
    refetchInterval: 30_000,
  })
}
