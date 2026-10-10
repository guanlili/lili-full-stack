import { createFileRoute, redirect } from "@tanstack/react-router"
import { UsersService } from "@/client"
import UsersPanel from "@/components/Admin/UsersPanel"
import { APP_NAME } from "@/config"

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) throw redirect({ to: "/" })
  },
  head: () => ({ meta: [{ title: `用户管理 - ${APP_NAME}` }] }),
})

function Admin() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <div>
        <p className="mb-2 text-xs font-medium tracking-widest text-muted-foreground">
          系统管理
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">用户管理</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          创建和维护用户账号，管理登录状态与管理员权限。
        </p>
      </div>
      <UsersPanel />
    </div>
  )
}
