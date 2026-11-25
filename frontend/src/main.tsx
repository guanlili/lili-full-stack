import { QueryClientProvider } from "@tanstack/react-query"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import type { ReactNode } from "react"
import { Component, lazy, StrictMode, Suspense } from "react"
import ReactDOM from "react-dom/client"
import { ThemeProvider } from "./components/theme-provider"
import { queryClient } from "./lib/queryClient"
import { configureSession } from "./lib/session"
// 离线自托管字体（fontsource variable，内网/私有化部署不依赖外部 CDN）
import "@fontsource-variable/inter"
import "@fontsource-variable/plus-jakarta-sans"
import "@fontsource-variable/jetbrains-mono"
import "./index.css"
import { routeTree } from "./routeTree.gen"

// Toaster（含 sonner，~34KB gzip）不进首屏关键路径；挂载前的 toast 由 lib/toast 队列兜底。
// chunk 拉取失败时降级为无 toast（.catch 返回空片段），绝不能让 React 卸载整棵树打白屏
type ToasterProps = React.ComponentProps<
  typeof import("./components/ui/sonner")["Toaster"]
>
const Toaster = lazy(
  (): Promise<{ default: React.ComponentType<ToasterProps> }> =>
    import("./components/ui/sonner")
      .then((mod) => ({ default: mod.Toaster }))
      .catch(() => ({ default: () => null })),
)

// 前端 Sentry（可选）：配置了 VITE_SENTRY_DSN 才启用。SDK 异步加载不进首屏
// 关键路径（代价是错过最初几十毫秒的错误，可接受）；错误主动上报见 ErrorComponent
const sentryDsn = import.meta.env.VITE_SENTRY_DSN
if (sentryDsn) {
  void import("@sentry/react")
    .then((Sentry) => {
      Sentry.init({
        dsn: sentryDsn,
        environment: import.meta.env.MODE,
        // 错误默认全采；链路追踪需要后端配套，先不采
        tracesSampleRate: 0,
      })
    })
    .catch(() => {
      // 上报通道初始化失败不影响应用
    })
}

// 发布窗口内旧页面请求新 hash 的 chunk 会 404：拦截后整页重载拿新资源，
// 而不是让 React 抛错白屏
window.addEventListener("vite:preloadError", (event) => {
  event.preventDefault()
  window.location.reload()
})

/** Toaster 的兜底边界：Suspense 内的任何意外渲染错误降级为 null */
class ToasterErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  render() {
    return this.state.hasError ? null : this.props.children
  }
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
        <ToasterErrorBoundary>
          <Suspense fallback={null}>
            <Toaster richColors closeButton />
          </Suspense>
        </ToasterErrorBoundary>
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)
