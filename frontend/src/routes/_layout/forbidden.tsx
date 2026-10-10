import { createFileRoute, Link } from "@tanstack/react-router"
import { ShieldAlert } from "lucide-react"
import { useAccess } from "@/hooks/useAccess"

export const Route = createFileRoute("/_layout/forbidden")({
  component: Forbidden,
})

function Forbidden() {
  const { data } = useAccess()
  return (
    <div className="mx-auto max-w-xl space-y-5 rounded-xl border p-8">
      <ShieldAlert className="size-8 text-muted-foreground" />
      <h1 className="text-2xl font-semibold">暂无访问权限</h1>
      <p className="text-muted-foreground">
        你的角色尚未获得此页面的权限，请联系管理员调整。
      </p>
      <div className="flex flex-wrap gap-4">
        {data?.pages
          .filter((page) => page.allowed)
          .map((page) => (
            <Link
              key={page.path}
              to={page.path}
              className="text-primary underline underline-offset-4"
            >
              {page.title}
            </Link>
          ))}
      </div>
    </div>
  )
}
