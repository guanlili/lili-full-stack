import { createFileRoute } from "@tanstack/react-router"

import AuditPanel from "@/components/Admin/AuditPanel"
import { APP_NAME } from "@/config"

export const Route = createFileRoute("/_layout/admin/audit")({
  component: Audit,
  head: () => ({ meta: [{ title: `审计日志 - ${APP_NAME}` }] }),
})

function Audit() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <div>
        <p className="mb-2 text-xs font-medium tracking-widest text-muted-foreground">
          系统管理
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">审计日志</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          追溯关键操作的执行者与时间，满足内部审计与安全排查需要。
        </p>
      </div>
      <AuditPanel />
    </div>
  )
}
