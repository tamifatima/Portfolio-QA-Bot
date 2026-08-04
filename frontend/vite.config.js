/*
=============================================================
  vite.config.js  —  Vite Build Configuration
=============================================================

PURPOSE:
  Vite is the build tool and dev server for the React frontend.

  @vitejs/plugin-react enables:
    - JSX transformation (converts JSX → JS)
    - Fast Refresh (HMR — edits update instantly without full reload)

  The proxy config is optional but useful:
  Any request from React to /api/... is forwarded to localhost:8000,
  so you can use fetch("/api/chat") instead of the full URL.
  (We're using the full URL in App.jsx for clarity, but this is an
  alternative approach that avoids CORS issues entirely.)
=============================================================
*/

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Optional: proxy API calls to avoid CORS in development
    // If you use this, change API_BASE in App.jsx to "" and use "/api/chat"
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
