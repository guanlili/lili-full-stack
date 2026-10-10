import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import type { RoleDetailPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { APP_NAME } from "@/config"
import { useAccess } from "@/hooks/useAccess"
import { useRoles } from "@/hooks/useRoles"

export const Route = createFileRoute("/_layout/roles")({
  component: Roles,
  head: () => ({ meta: [{ title: `角色权限 - ${APP_NAME}` }] }),
})

function RoleCard({ role }: { role: RoleDetailPublic }) {
  const { data: access } = useAccess()
  const { update } = useRoles()
  const [permissions, setPermissions] = useState(role.permissions)
  return (
    <Card className="shadow-none">
      <CardHeader>
        <CardTitle>{role.name}</CardTitle>
        <CardDescription>
          {role.description || "勾选此角色允许访问的页面"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-2">
          {access?.pages
            .filter((page) => !page.admin_only)
            .map((page) => (
              <label
                key={page.codename}
                htmlFor={`${role.id}-${page.codename}`}
                className="flex cursor-pointer items-center gap-3 rounded-lg border p-4"
              >
                <Checkbox
                  id={`${role.id}-${page.codename}`}
                  disabled={update.isPending}
                  checked={permissions.includes(page.codename)}
                  onCheckedChange={(checked) =>
                    setPermissions((previous) =>
                      checked
                        ? [...previous, page.codename]
                        : previous.filter((code) => code !== page.codename),
                    )
                  }
                />
                <span className="text-sm">
                  {page.title}
                  {page.path === "/admin" && (
                    <span className="block text-xs text-muted-foreground">
                      只读列表，不能修改账号或权限
                    </span>
                  )}
                </span>
              </label>
            ))}
        </div>
        <LoadingButton
          loading={update.isPending}
          disabled={
            !access ||
            permissions.slice().sort().join() ===
              role.permissions.slice().sort().join()
          }
          onClick={() => update.mutate({ roleId: role.id, permissions })}
        >
          保存权限
        </LoadingButton>
      </CardContent>
    </Card>
  )
}

function Roles() {
  const { query, create } = useRoles()
  const [name, setName] = useState("")
  return (
    <div className="space-y-6">
      <div>
        <p className="mb-2 text-sm text-muted-foreground">系统管理</p>
        <h1 className="text-3xl font-semibold">角色权限</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          配置每种角色可以访问的页面，再在用户管理中分配角色。
        </p>
      </div>
      <Card className="shadow-none">
        <CardHeader>
          <CardTitle>管理员</CardTitle>
          <CardDescription>
            管理员拥有全部页面和管理权限，不能通过普通角色授权或取消。只有管理员可以配置角色及管理账号。
          </CardDescription>
        </CardHeader>
      </Card>
      <form
        className="flex flex-wrap gap-3"
        onSubmit={(event) => {
          event.preventDefault()
          create.mutate(name.trim(), { onSuccess: () => setName("") })
        }}
      >
        <Input
          aria-label="新角色名称"
          placeholder="角色名称，如运营人员"
          maxLength={100}
          className="max-w-sm"
          value={name}
          onChange={(event) => setName(event.target.value)}
          disabled={create.isPending}
        />
        <LoadingButton
          type="submit"
          loading={create.isPending}
          disabled={!name.trim()}
        >
          新建角色
        </LoadingButton>
      </form>
      <p className="text-sm text-muted-foreground">
        未分配角色的普通账号使用“访客”权限；多个角色的权限合并。新增角色默认没有页面权限。
      </p>
      {query.isPending && <p>正在加载角色…</p>}
      {query.isError && (
        <div role="alert">
          角色加载失败{" "}
          <Button variant="link" onClick={() => query.refetch()}>
            重试
          </Button>
        </div>
      )}
      {query.data?.map((role) => (
        <RoleCard
          key={`${role.id}:${role.permissions.slice().sort().join()}`}
          role={role}
        />
      ))}
    </div>
  )
}
