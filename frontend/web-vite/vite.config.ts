import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Development configuration with reduced HMR issues
export default defineConfig({
  plugins: [react()],
  esbuild: {
    jsx: 'automatic',
  },
  server: {
    host: true,
    port: 3000,
    hmr: false, // Disable HMR completely to avoid connection issues
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
})
