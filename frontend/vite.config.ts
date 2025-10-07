import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    allowedHosts: ['dev.dc.vasiliy-ivanov.ru', 'localhost', '127.0.0.1'],
    hmr: {
      clientPort: 8083,
      host: 'dev.dc.vasiliy-ivanov.ru'
    },
    proxy: {
      '/api': {
        target: 'http://dc-dev-api:8000',
        changeOrigin: true,
      },
    },
  },
})
