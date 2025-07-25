import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  server: {
    // frontend
    port: 3000,

    // backend server
    proxy: {
      '/api': {
        target: 'https://google-drive-organizer.onrender.com',
        changeOrigin: true,
      }
    },
  },
})
