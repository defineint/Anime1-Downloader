import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  server: {
    proxy: {
      // 只要前端存取 /api，就自動轉發到後端 FastAPI
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // 如果後端 API 其實沒有 /api 前綴，可以用 rewrite 拿掉，但你的後端有，所以不用重寫
      },
    },
  },
})
