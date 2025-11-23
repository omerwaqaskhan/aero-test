import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  esbuild: {
    jsx: 'automatic',
  },
  server: {
    host: true,
    port: 3000,
    hmr: {
      port: 3000,
      host: 'localhost',
      clientPort: 3000,
      overlay: false, // Disable error overlay to reduce connection issues
    },
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  define: {
    // Reduce WebSocket reconnection attempts
    __VITE_WS_RECONNECT_INTERVAL__: 5000,
    __VITE_WS_MAX_RECONNECT_ATTEMPTS__: 3,
  },
})
