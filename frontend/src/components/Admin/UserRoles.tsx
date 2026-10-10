import { useEffect, useState } from "react"
import type { UserPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import { useRoles, useUserRoles } from "@/hooks/useRoles"

export default function UserRoles({
  user,
  open,
  setOpen,
}: {
  user: UserPublic
  open: boolean
  setOpen: (open: boolean) => void
}) {
  const { query: roles } = useRoles()
  const { query, update } = useUserRoles(user.id, open)
  const [selected, setSelected] = useState<string[]>([])
  useEffect(() => {
    if (query.data && open) setSelected(query.data.data.map((role) => role.id))
  }, [query.data, open])
  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        if (!update.isPending) setOpen(value)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>分配角色</DialogTitle>
          <DialogDescription>
            {user.email} · 不选择角色时使用默认访客权限。
          </DialogDescription>
        </DialogHeader>
        {query.isPending || roles.isPending ? (
          <p>正在加载…</p>
        ) : query.isError || roles.isError ? (
          <div role="alert">
            加载失败{" "}
            <Button
              onClick={() => {
                query.refetch()
                roles.refetch()
              }}
            >
              重试
            </Button>
          </div>
        ) : (
          <div className="max-h-72 space-y-3 overflow-y-auto">
            {roles.data?.map((role) => (
              <label
                key={role.id}
                htmlFor={`user-role-${user.id}-${role.id}`}
                className="flex items-center gap-3 rounded-lg border p-3"
              >
                <Checkbox
                  id={`user-role-${user.id}-${role.id}`}
                  disabled={update.isPending}
                  checked={selected.includes(role.id)}
                  onCheckedChange={(checked) =>
                    setSelected((previous) =>
                      checked
                        ? [...previous, role.id]
                        : previous.filter((id) => id !== role.id),
                    )
                  }
                />
                {role.name}
              </label>
            ))}
          </div>
        )}
        <DialogFooter>
          <Button
            variant="outline"
            disabled={update.isPending}
            onClick={() => setOpen(false)}
          >
            取消
          </Button>
          <LoadingButton
            loading={update.isPending}
            disabled={
              !query.data || !roles.data || query.isError || roles.isError
            }
            onClick={() =>
              update.mutate(selected, { onSuccess: () => setOpen(false) })
            }
          >
            保存角色
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
