import type { FrameAnalysis, HealthResponse, StormDetail, StormSummary } from '../types/api'
import { api } from './client'

export const stormsApi = {
  health: () => api.get<HealthResponse>('/api/health'),

  list: () => api.get<StormSummary[]>('/api/storms'),

  /**
   * Metadata plus the storm's entire frame index in one response. This is what makes the
   * scrubber instant: dragging it reads an array already in memory rather than issuing a
   * request per frame.
   */
  detail: (sid: string) => api.get<StormDetail>(`/api/storms/${encodeURIComponent(sid)}`),

  frame: (sid: string, isoTime: string) =>
    api.get<FrameAnalysis>(
      `/api/storms/${encodeURIComponent(sid)}/frames/${encodeURIComponent(isoTime)}`,
    ),
}
