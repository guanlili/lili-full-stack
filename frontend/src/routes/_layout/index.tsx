import { createFileRoute } from "@tanstack/react-router"
import { APP_NAME } from "@/config"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: `工作台 - ${APP_NAME}`,
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <div>
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          {currentUser?.full_name || currentUser?.email}，你好 👋
        </h1>
        <p className="text-muted-foreground">欢迎回来，很高兴再次见到你！</p>
      </div>
    </div>
  )
}
