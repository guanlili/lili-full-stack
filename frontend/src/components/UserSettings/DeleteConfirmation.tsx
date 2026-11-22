import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"

import { Users as UsersService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const DeleteConfirmation = () => {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { handleSubmit } = useForm()
  const { logout } = useAuth()
  // 注销是不可逆操作：必须输入当前密码复核（后端强校验）
  const [password, setPassword] = useState("")

  const mutation = useMutation({
    mutationFn: (currentPassword: string) =>
      UsersService.deleteUserMe({
        body: { current_password: currentPassword },
        throwOnError: true,
      }).then((response) => response.data),
    onSuccess: () => {
      showSuccessToast("账号已成功注销")
      void logout()
    },
    onError: handleError.bind(showErrorToast),
    // 不 invalidate currentUser：成功时账号已不存在（必然 401 触发硬跳转，
    // 与 logout 赛跑会丢成功 toast），失败时用户也没变
  })

  const onSubmit = async () => {
    mutation.mutate(password)
  }

  return (
    <Dialog
      onOpenChange={(open) => {
        // 关闭（取消/Esc/点遮罩）即清空密码：重新打开不残留上一次输入
        if (!open) setPassword("")
      }}
    >
      <DialogTrigger asChild>
        <Button variant="destructive" className="mt-3">
          注销账号
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>请确认操作</DialogTitle>
            <DialogDescription>
              你的账号数据将被<strong>永久删除</strong>
              。请输入当前密码确认身份，此操作无法撤销。
            </DialogDescription>
          </DialogHeader>

          <div className="py-2">
            <PasswordInput
              autoComplete="current-password"
              placeholder="当前密码"
              aria-label="当前密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={mutation.isPending}
            />
          </div>

          <DialogFooter className="mt-4">
            <DialogClose asChild>
              <Button variant="outline" disabled={mutation.isPending}>
                取消
              </Button>
            </DialogClose>
            <LoadingButton
              variant="destructive"
              type="submit"
              loading={mutation.isPending}
              disabled={!password}
            >
              确认注销
            </LoadingButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default DeleteConfirmation
