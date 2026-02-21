import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        proxyTimeout: 900_000, // 15 min – book analysis can be very slow
        timeout: 900_000,
      },
      '/static': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
