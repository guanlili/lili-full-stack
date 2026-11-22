// 统一错误上报入口：未配置 VITE_SENTRY_DSN 时零成本（不拉 Sentry chunk）
export function reportError(error: unknown): void {
  if (!import.meta.env.VITE_SENTRY_DSN) return
  void import("@sentry/react")
    .then((Sentry) => Sentry.captureException(error))
    .catch(() => {
      // 上报通道失败静默跳过
    })
}
