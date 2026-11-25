// 统一错误上报入口：未配置 VITE_SENTRY_DSN 时零成本（不上报、不拉 SDK chunk）。
// DSN 指向自建 GlitchTip（与 Sentry 协议兼容，复用同一 SDK），不使用 Sentry 云。

/** 读取 DSN 入口：抽成函数便于测试注入；浏览器环境走 Vite 注入的 env。 */
export function resolveDsn(): string {
  return import.meta.env.VITE_SENTRY_DSN ?? ""
}

export function reportError(error: unknown, dsn: string = resolveDsn()): void {
  if (!dsn) return
  void import("@sentry/react")
    .then((Sentry) => Sentry.captureException(error))
    .catch(() => {
      // 上报通道失败静默跳过
    })
}
