import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND = process.env.VITE_BACKEND_URL || 'http://backend:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/auth':       { target: BACKEND, changeOrigin: true },
      '/sheets':     { target: BACKEND, changeOrigin: true },
      '/query':      { target: BACKEND, changeOrigin: true },
      '/connectors': { target: BACKEND, changeOrigin: true },
    },
  },
})
