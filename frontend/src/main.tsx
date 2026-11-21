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
