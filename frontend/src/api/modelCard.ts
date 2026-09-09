import type { ModelCard } from '../types/api'
import { api } from './client'

export const modelCardApi = {
  get: () => api.get<ModelCard>('/api/model-card'),
}
