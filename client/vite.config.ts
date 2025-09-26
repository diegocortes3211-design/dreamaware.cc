import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 3000,
    // Security: only listen on localhost in development
    host: 'localhost',
    fs: {
      strict: true
    }
  },
  build: {
    // Optimize for production
    minify: 'esbuild', // Use esbuild instead of terser for faster builds
    // Generate source maps for debugging but keep them separate
    sourcemap: 'hidden',
    // Enable CSS code splitting
    cssCodeSplit: true,
    // Set chunk size warning limit
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // Optimize chunking strategy
        manualChunks: {
          vendor: ['zod']
        }
      }
    }
  }
})