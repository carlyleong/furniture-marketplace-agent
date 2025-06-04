import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/static': {
        target: process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/processed': {
        target: process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
