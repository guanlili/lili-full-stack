// sonner 体积较大（~34KB gzip），首帧不需要：Toaster 由 main.tsx 懒加载，
// 本模块提供队列兜底——Toaster 挂载（bindToast）前发起的 toast 会排队，挂载后冲排，不丢。
type SonnerModule = typeof import("sonner")

let api: SonnerModule | null = null
const queue: Array<() => void> = []

/** Toaster 挂载（sonner chunk 就绪）后回填 API 并冲排队列；幂等。 */
export function bindToast(loaded: SonnerModule) {
  if (api) return
  api = loaded
  for (const fire of queue.splice(0)) {
    fire()
  }
}

function dispatch(fire: (mod: SonnerModule) => void) {
  if (api) {
    fire(api)
    return
  }
  // 排队等待 bindToast（Toaster 懒挂载即触发）冲排；不做预热——根级 lazy
  // Toaster 首帧就会请求同一 chunk
  queue.push(() => fire(api as SonnerModule))
}

export function toastSuccess(description: string) {
  dispatch((mod) => mod.toast.success("操作成功", { description }))
}

export function toastError(description: string) {
  dispatch((mod) => mod.toast.error("操作失败", { description }))
}

export function toastErrorMessage(message: string) {
  dispatch((mod) => mod.toast.error(message))
}
