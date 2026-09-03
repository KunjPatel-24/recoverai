import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The frontend calls the backend at /api and /webhook; proxy those to uvicorn
// on :8000 during dev so you don't hit CORS and can use relative URLs.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/webhook': 'http://localhost:8000',
    },
  },
})
