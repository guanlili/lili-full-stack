import { QueryClientProvider } from "@tanstack/react-query"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import { lazy, StrictMode, Suspense } from "react"
import ReactDOM from "react-dom/client"
import { ThemeProvider } from "./components/theme-provider"
import { queryClient } from "./lib/queryClient"
import { configureSession } from "./lib/session"
import "./index.css"
import { routeTree } from "./routeTree.gen"

// Toaster（含 sonner，~34KB gzip）不进首屏关键路径；挂载前的 toast 由 lib/toast 队列兜底
const Toaster = lazy(() =>
  import("./components/ui/sonner").then((mod) => ({ default: mod.Toaster })),
)

// 前端 Sentry（可选）：配置了 VITE_SENTRY_DSN 才启用。SDK 异步加载不进首屏
// 关键路径（代价是错过最初几十毫秒的错误，可接受）；错误主动上报见 ErrorComponent
const sentryDsn = import.meta.env.VITE_SENTRY_DSN
if (sentryDsn) {
  void import("@sentry/react").then((Sentry) => {
    Sentry.init({
      dsn: sentryDsn,
      environment: import.meta.env.MODE,
      // 错误默认全采；链路追踪需要后端配套，先不采
      tracesSampleRate: 0,
    })
  })
}

configureSession()

const router = createRouter({ routeTree })
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Suspense fallback={null}>
          <Toaster richColors closeButton />
        </Suspense>
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)
