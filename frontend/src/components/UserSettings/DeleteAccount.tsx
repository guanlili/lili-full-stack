import { ShieldAlert } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import useAuth from "@/hooks/useAuth"
import DeleteConfirmation from "./DeleteConfirmation"

export default function DeleteAccount() {
  const { user } = useAuth()
  return (
    <Card className="gap-5 border-destructive/30 shadow-none">
      <CardHeader className="border-b border-destructive/20 pb-5">
        <CardTitle className="flex items-center gap-2 text-destructive">
          <ShieldAlert className="size-5" />
          注销账号
        </CardTitle>
        <CardDescription>
          注销是永久操作，请在继续前确认不再需要此账号。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {user?.is_superuser ? (
          <p className="text-sm text-muted-foreground">
            管理员账号不能自行注销。如需处理此账号，请联系其他管理员。
          </p>
        ) : (
          <>
            <div className="max-w-xl space-y-2 text-sm text-muted-foreground">
              <p>注销后将无法登录，账号及其关联数据会被永久删除，无法恢复。</p>
              <p>如果只是暂时不使用，可以退出登录，或联系管理员停用账号。</p>
            </div>
            <DeleteConfirmation />
          </>
        )}
      </CardContent>
    </Card>
  )
}
