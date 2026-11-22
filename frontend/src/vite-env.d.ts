/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  /** 可选：配置后启用前端 Sentry（与后端共用一个 DSN 即可） */
  readonly VITE_SENTRY_DSN: string | undefined
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
