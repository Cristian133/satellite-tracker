import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Deliberately separate from vite.config.ts: it doesn't need the Cesium vite
// plugin (that only wires up Cesium's static assets for the dev/build
// server), and tests mock out 'cesium'/'resium' entirely rather than
// exercising the real WebGL-dependent library under jsdom.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
