import { type ErrorComponentProps, useRouter } from "@tanstack/react-router"
import { AxiosError } from "axios"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { reportError } from "@/lib/reportError"
import { extractErrorMessage } from "@/utils"

const ErrorComponent = ({ error, reset }: ErrorComponentProps) => {
  const router = useRouter()
  // API 错误翻译成友好文案；非 HTTP 错误（JS 异常/chunk 加载失败/beforeLoad 抛错）
  // 展示原始 message——路由错误多数不是"网络问题"，不能一律报网络文案
  const errorMessage =
    error instanceof AxiosError
      ? extractErrorMessage(error)
      : error instanceof Error
        ? error.message
        : String(error ?? "未知错误")

  useEffect(() => {
    if (!error) return
    // 统一上报入口（未配置 VITE_SENTRY_DSN 时零成本）
    reportError(error)
  }, [error])

  return (
    <div
      className="flex min-h-screen items-center justify-center flex-col p-4"
      data-testid="error-component"
    >
      <div className="flex items-center z-10">
        <div className="flex flex-col ml-4 items-center justify-center p-4">
          <span className="text-6xl md:text-8xl font-bold leading-none mb-4">
            出错了
          </span>
          <span className="text-2xl font-bold mb-2">操作失败</span>
        </div>
      </div>

      <p className="text-lg text-muted-foreground mb-4 text-center z-10">
        服务暂时遇到问题，请稍后重试。
      </p>
      {/* 原始错误信息：接入 Sentry 等上报时从这里取 error */}
      {error ? (
        <p
          className="mb-4 max-w-xl break-words rounded-md bg-muted px-3 py-2 font-mono text-xs text-muted-foreground"
          data-testid="error-component-message"
        >
          {errorMessage}
        </p>
      ) : null}
      <div className="flex flex-col items-center gap-3">
        <div className="flex gap-3">
          <Button onClick={() => (reset ? reset() : window.location.reload())}>
            重试
          </Button>
          <Button onClick={() => router.history.push("/")} variant="outline">
            返回首页
          </Button>
        </div>
        <Button
          className="mt-0"
          onClick={() => window.location.reload()}
          variant="ghost"
        >
          重新加载页面
        </Button>
      </div>
    </div>
  )
}

export default ErrorComponent
