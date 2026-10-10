import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { PlatformService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export default function PlatformTools({
  section,
}: {
  section: "roles" | "audit"
}) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [roleName, setRoleName] = useState("")
  const [roleDescription, setRoleDescription] = useState("")

  const rolesQuery = useQuery({
    enabled: section === "roles",
    queryKey: ["platform-roles"],
    queryFn: () => PlatformService.readRoles({ limit: 100 }),
  })
  const auditQuery = useQuery({
    enabled: section === "audit",
    queryKey: ["audit-logs"],
    queryFn: () => PlatformService.readAuditLogs({ limit: 20 }),
  })
  const createRoleMutation = useMutation({
    mutationFn: () =>
      PlatformService.createRole({
        requestBody: { name: roleName, description: roleDescription || null },
      }),
    onSuccess: () => {
      setRoleName("")
      setRoleDescription("")
      showSuccessToast("角色创建成功")
      queryClient.invalidateQueries({ queryKey: ["platform-roles"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <div className="space-y-6">
      {section === "roles" && (
        <Card className="shadow-none">
          <CardHeader>
            <CardTitle>角色管理</CardTitle>
            <CardDescription>
              自定义业务角色。账号类型中的超级管理员拥有系统完整权限。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2 sm:grid-cols-2">
              <Input
                aria-label="角色名称"
                placeholder="角色名称，如运营人员"
                value={roleName}
                onChange={(event) => setRoleName(event.target.value)}
              />
              <Input
                aria-label="角色说明"
                placeholder="描述角色的职责"
                value={roleDescription}
                onChange={(event) => setRoleDescription(event.target.value)}
              />
            </div>
            <Button
              disabled={!roleName.trim() || createRoleMutation.isPending}
              onClick={() => createRoleMutation.mutate()}
            >
              新建角色
            </Button>
            {rolesQuery.isPending && (
              <p className="py-8 text-center text-sm text-muted-foreground">
                正在加载…
              </p>
            )}
            {rolesQuery.isError && (
              <div role="alert" className="py-6 text-center">
                <p className="text-sm">加载失败，请重试。</p>
                <Button variant="link" onClick={() => rolesQuery.refetch()}>
                  重新加载
                </Button>
              </div>
            )}
            {rolesQuery.data && rolesQuery.data.data.length === 0 && (
              <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                暂无记录
              </p>
            )}
            <div className="space-y-2 text-sm">
              {rolesQuery.data?.data.map((role) => (
                <div
                  className="flex justify-between rounded border p-2"
                  key={role.id}
                >
                  <span>{role.name}</span>
                  <span className="text-muted-foreground">
                    {role.description || "未填写说明"}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {section === "audit" && (
        <Card className="shadow-none">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle>操作日志</CardTitle>
                <CardDescription>
                  查看最近 20 条管理操作，追踪谁更改了什么。
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {auditQuery.isPending && (
              <p className="py-8 text-center text-sm text-muted-foreground">
                正在加载…
              </p>
            )}
            {auditQuery.isError && (
              <div role="alert" className="py-6 text-center">
                <p className="text-sm">加载失败，请重试。</p>
                <Button variant="link" onClick={() => auditQuery.refetch()}>
                  重新加载
                </Button>
              </div>
            )}
            {auditQuery.data && auditQuery.data.data.length === 0 && (
              <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                暂无记录
              </p>
            )}
            <div className="space-y-2 text-sm">
              {auditQuery.data?.data.map((log) => (
                <div
                  className="grid gap-1 rounded border p-2 sm:grid-cols-[180px_1fr_auto]"
                  key={log.id}
                >
                  <span>{log.action}</span>
                  <span className="text-muted-foreground">
                    {log.resource_type}
                    {log.resource_id ? ` / ${log.resource_id}` : ""}
                  </span>
                  <span className="text-muted-foreground">
                    {log.created_at
                      ? new Date(log.created_at).toLocaleString()
                      : ""}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
