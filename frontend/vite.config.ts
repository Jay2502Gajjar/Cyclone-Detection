import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // The backend serves /media/** (satellite frames, Grad-CAM overlays) from disk.
    // Proxying in dev keeps image URLs identical to production, so nothing has to know
    // whether it is running locally.
    proxy: {
      '/api': { target: 'http://localhost:8090', changeOrigin: true },
      '/media': { target: 'http://localhost:8090', changeOrigin: true },
    },
  },
})
