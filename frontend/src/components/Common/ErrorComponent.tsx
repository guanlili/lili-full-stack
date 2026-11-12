import { type ErrorComponentProps, useRouter } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"

const ErrorComponent = ({ error, reset }: ErrorComponentProps) => {
  const router = useRouter()
  const errorMessage = error instanceof Error ? error.message : String(error)

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
