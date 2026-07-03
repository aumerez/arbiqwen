import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Standalone browser client build. Emits static assets only; there is no
// Electron main/preload step and no native runtime dependency.
export default defineConfig({
  root: '.',
  base: './',
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 5174,
    strictPort: true,
  },
});
