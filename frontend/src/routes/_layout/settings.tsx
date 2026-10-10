import { createFileRoute } from "@tanstack/react-router"
import { KeyRound, ShieldAlert, UserRound } from "lucide-react"
import ChangePassword from "@/components/UserSettings/ChangePassword"
import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { APP_NAME } from "@/config"
import useAuth from "@/hooks/useAuth"

const tabsConfig = [
  {
    value: "my-profile",
    title: "个人资料",
    icon: UserRound,
    component: UserInformation,
  },
  {
    value: "password",
    title: "登录安全",
    icon: KeyRound,
    component: ChangePassword,
  },
  {
    value: "danger-zone",
    title: "账号注销",
    icon: ShieldAlert,
    component: DeleteAccount,
  },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
  head: () => ({
    meta: [
      {
        title: `账号设置 - ${APP_NAME}`,
      },
    ],
  }),
})

function UserSettings() {
  const { user: currentUser } = useAuth()

  if (!currentUser) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="mb-2 text-sm font-medium text-muted-foreground">
          个人中心
        </p>
        <h1 className="text-2xl font-bold tracking-tight">账号设置</h1>
        <p className="text-muted-foreground">
          维护个人资料、更新登录密码，以及管理账号状态
        </p>
      </div>

      <Card className="py-0 shadow-none">
        <CardContent className="flex min-w-0 items-center gap-4 p-5">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xl font-semibold text-primary">
            {(currentUser.full_name || currentUser.email)
              .slice(0, 1)
              .toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate font-semibold">
              {currentUser.full_name || "尚未填写姓名"}
            </p>
            <p className="truncate text-sm text-muted-foreground">
              {currentUser.email}
            </p>
          </div>
          <Badge variant="secondary" className="shrink-0">
            {currentUser.is_superuser ? "管理员" : "普通用户"}
          </Badge>
        </CardContent>
      </Card>
      <Tabs defaultValue="my-profile" className="gap-5">
        <TabsList className="h-auto w-full justify-start sm:w-auto">
          {tabsConfig.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              <tab.icon className="hidden size-4 sm:block" />
              {tab.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {tabsConfig.map((tab) => (
          <TabsContent key={tab.value} value={tab.value} className="mt-0">
            <tab.component />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
