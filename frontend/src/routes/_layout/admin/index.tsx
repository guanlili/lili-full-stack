import { createFileRoute } from "@tanstack/react-router"
import UsersPanel from "@/components/Admin/UsersPanel"
import { PageContainer, PageHeader } from "@/components/patterns"
import { APP_NAME } from "@/config"

export const Route = createFileRoute("/_layout/admin/")({
  component: Admin,
  head: () => ({ meta: [{ title: `用户管理 - ${APP_NAME}` }] }),
})

function Admin() {
  return (
    <PageContainer>
      <PageHeader
        eyebrow="系统管理"
        title="用户管理"
        description="创建和维护用户账号，管理登录状态与管理员权限。"
      />
      <UsersPanel />
    </PageContainer>
  )
}
