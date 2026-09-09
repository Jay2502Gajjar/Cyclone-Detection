import { useQuery } from '@tanstack/react-query'

import { modelCardApi } from '../api/modelCard'

export function useModelCard() {
  return useQuery({ queryKey: ['model-card'], queryFn: modelCardApi.get })
}
