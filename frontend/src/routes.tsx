import { Route, Routes } from 'react-router-dom'

import { CommandCenter } from './pages/CommandCenter'
import { ModelCard } from './pages/ModelCard'

/**
 * Two routes. That is the whole application.
 *
 * Depth on one screen beats breadth across seven: every extra route dilutes a four-minute
 * demo, and everything that would have been a page here is a drawer instead.
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<CommandCenter />} />
      <Route path="/model" element={<ModelCard />} />
      <Route path="*" element={<CommandCenter />} />
    </Routes>
  )
}
