import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import axios from "axios"
import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { toast } from "sonner"
import { ApiError } from "./client"
import { ThemeProvider } from "./components/theme-provider"
import { Toaster } from "./components/ui/sonner"
import { configureSession, expireSession } from "./lib/session"
import "./index.css"
import { routeTree } from "./routeTree.gen"

configureSession()

const handleApiError = (error: Error) => {
  if (axios.isCancel(error)) return
  // 只在 401（token 无效/过期）时登出；403 是"已登录但权限不足"，
  // 一并登出会把正常用户误踢下线（例如访问一个无权限的资源）
  if (error instanceof ApiError && error.status === 401) {
    expireSession()
    return
  }

  if (error instanceof ApiError && error.status === 403) {
    toast.error("没有权限执行此操作")
  } else {
    toast.error("请求失败，请稍后重试")
  }
}
const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleApiError,
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      if (error instanceof ApiError && error.status === 401) {
        handleApiError(error)
      }
    },
  }),
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
})

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
        <Toaster richColors closeButton />
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)
