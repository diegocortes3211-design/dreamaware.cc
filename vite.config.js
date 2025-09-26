import { defineConfig } from "vite";

export default defineConfig({
  base: "/dreamaware.cc/",
  build: {
    // Optimize for production deployment
    minify: 'esbuild', // Use esbuild instead of terser for faster builds
    sourcemap: false, // Disable sourcemaps for production
    cssCodeSplit: true,
    chunkSizeWarningLimit: 1000,
  },
  // Security: prevent access to files outside project root  
  server: {
    fs: {
      strict: true
    }
  }
});