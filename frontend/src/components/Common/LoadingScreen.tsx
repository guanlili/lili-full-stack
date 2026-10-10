import { Loader2 } from "lucide-react"

const LoadingScreen = () => (
  <div
    aria-label="页面加载中"
    aria-live="polite"
    className="flex min-h-[40vh] items-center justify-center"
    role="status"
  >
    <Loader2 className="size-6 animate-spin text-primary" />
    <span className="sr-only">页面加载中</span>
  </div>
)

export default LoadingScreen
