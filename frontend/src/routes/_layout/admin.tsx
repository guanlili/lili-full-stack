import { createFileRoute, redirect } from "@tanstack/react-router"
import { History, Settings2, ShieldCheck, Users } from "lucide-react"
import { UsersService } from "@/client"
import PlatformTools from "@/components/Admin/PlatformTools"
import UsersPanel from "@/components/Admin/UsersPanel"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
        <h1 className="text-3xl font-semibold tracking-tight">
          用户与访问管理
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          统一管理账号、角色和系统访问，重要操作均可追溯。
        </p>
      </div>
      <Tabs defaultValue="users" className="gap-6">
        <TabsList className="h-auto w-full justify-start gap-1 overflow-x-auto rounded-none border-b bg-transparent p-0 pb-2 sm:w-fit">
          <TabsTrigger value="users" className="px-2 py-2 sm:px-4">
            <Users className="hidden sm:block" />
            用户账号
          </TabsTrigger>
          <TabsTrigger value="roles" className="px-2 py-2 sm:px-4">
            <ShieldCheck className="hidden sm:block" />
            角色管理
          </TabsTrigger>
          <TabsTrigger value="audit" className="px-2 py-2 sm:px-4">
            <History className="hidden sm:block" />
            操作日志
          </TabsTrigger>
          <TabsTrigger value="settings" className="px-2 py-2 sm:px-4">
            <Settings2 className="hidden sm:block" />
            系统配置
          </TabsTrigger>
        </TabsList>
        <TabsContent
          value="users"
          forceMount
          className="data-[state=inactive]:hidden"
        >
          <UsersPanel />
        </TabsContent>
        <TabsContent value="roles">
          <PlatformTools section="roles" />
        </TabsContent>
        <TabsContent value="audit">
          <PlatformTools section="audit" />
        </TabsContent>
        <TabsContent value="settings">
          <PlatformTools section="settings" />
        </TabsContent>
      </Tabs>
    </div>
  )
}
