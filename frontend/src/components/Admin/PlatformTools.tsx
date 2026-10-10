import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { PlatformService, SettingsService } from "@/client"
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
import { useUserExport } from "@/hooks/useUserExport"
import { handleError } from "@/utils"

export default function PlatformTools() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [roleName, setRoleName] = useState("")
  const [roleDescription, setRoleDescription] = useState("")
  const [settingKey, setSettingKey] = useState("")
  const [settingValue, setSettingValue] = useState("")
  const { enqueue, jobQuery, download, downloadUrl, downloadRef } =
    useUserExport()

  const rolesQuery = useQuery({
    queryKey: ["platform-roles"],
    queryFn: () => PlatformService.readRoles({ limit: 100 }),
  })
  const auditQuery = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => PlatformService.readAuditLogs({ limit: 20 }),
  })
  const settingsQuery = useQuery({
    queryKey: ["system-settings"],
    queryFn: () => SettingsService.readSettings(),
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

  const updateSettingMutation = useMutation({
    mutationFn: () =>
      SettingsService.updateSetting({
        key: settingKey,
        requestBody: { value: settingValue },
      }),
    onSuccess: () => {
      setSettingKey("")
      setSettingValue("")
      showSuccessToast("系统配置已保存")
      queryClient.invalidateQueries({ queryKey: ["system-settings"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>角色管理</CardTitle>
          <CardDescription>
            为后续业务模块提供可复用的角色基础。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input
              placeholder="角色名称"
              value={roleName}
              onChange={(event) => setRoleName(event.target.value)}
            />
            <Input
              placeholder="角色说明"
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

      <Card>
        <CardHeader>
          <CardTitle>系统配置</CardTitle>
          <CardDescription>
            保存项目级开关和展示配置，不存放密码或密钥。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input
              placeholder="配置键，如 site.title"
              value={settingKey}
              onChange={(event) => setSettingKey(event.target.value)}
            />
            <Input
              placeholder="配置值"
              value={settingValue}
              onChange={(event) => setSettingValue(event.target.value)}
            />
          </div>
          <Button
            disabled={!settingKey.trim() || updateSettingMutation.isPending}
            onClick={() => updateSettingMutation.mutate()}
          >
            保存配置
          </Button>
          <div className="space-y-2 text-sm">
            {settingsQuery.data?.map((setting) => (
              <div
                className="flex justify-between rounded border p-2"
                key={setting.key}
              >
                <span>{setting.key}</span>
                <span className="text-muted-foreground truncate max-w-[60%]">
                  {setting.value}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div>
              <CardTitle>最近操作</CardTitle>
              <CardDescription>
                审计日志用于定位误操作和追踪数据变更。
              </CardDescription>
            </div>
            <Button
              disabled={
                enqueue.isPending ||
                jobQuery.isLoading ||
                jobQuery.data?.status === "queued" ||
                jobQuery.data?.status === "running"
              }
              onClick={() => enqueue.mutate()}
              variant="outline"
            >
              导出用户 CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {jobQuery.data && (
            <div className="mb-4 flex items-center gap-3 text-sm">
              <span>导出任务状态：{jobQuery.data.status}</span>
              {jobQuery.data.status === "failed" && (
                <span role="alert">导出失败，请重新提交。</span>
              )}
              {jobQuery.data.status === "completed" &&
                typeof jobQuery.data.result?.file_id === "string" && (
                  <Button
                    variant="outline"
                    disabled={download.isPending}
                    onClick={() => {
                      const fileId = jobQuery.data?.result?.file_id
                      if (typeof fileId === "string") download.mutate(fileId)
                    }}
                  >
                    {download.isPending ? "准备下载…" : "下载 CSV"}
                  </Button>
                )}
            </div>
          )}
          {jobQuery.isError && (
            <p role="alert" className="mb-4 text-sm">
              无法查询导出状态。
              <Button variant="link" onClick={() => jobQuery.refetch()}>
                重试
              </Button>
            </p>
          )}
          <a
            ref={downloadRef}
            href={downloadUrl ?? undefined}
            download="users.csv"
            hidden
          >
            下载用户 CSV
          </a>
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
    </div>
  )
}
