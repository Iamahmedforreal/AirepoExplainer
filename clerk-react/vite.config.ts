import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    fs: {
      // Allow importing the CodeGrok agent skill.md from the repo-level .agents folder
      allow: [fileURLToPath(new URL('..', import.meta.url))],
    },
  },
})
