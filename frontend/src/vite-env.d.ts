/// <reference types="vite/client" />

/**
 * Type declarations for Vite-specific features.
 *
 * This file provides TypeScript with type information for:
 * - import.meta.env (environment variables)
 * - Static asset imports (.css, .svg, .png, etc.)
 * - Vite's module resolution
 *
 * Reference: https://vitejs.dev/guide/env-and-mode.html
 */

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_APP_ENV: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
