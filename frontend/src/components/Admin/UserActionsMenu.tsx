import { EllipsisVertical, ShieldCheck } from "lucide-react"
import { useState } from "react"

import type { UserPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useAuth from "@/hooks/useAuth"
import DeleteUser from "./DeleteUser"
import EditUser from "./EditUser"
import UserRoles from "./UserRoles"

interface UserActionsMenuProps {
  user: UserPublic
}

export const UserActionsMenu = ({ user }: UserActionsMenuProps) => {
  const [open, setOpen] = useState(false)
  const [rolesOpen, setRolesOpen] = useState(false)
  const { user: currentUser } = useAuth()

  if (!currentUser?.is_superuser || user.id === currentUser?.id) {
    return null
  }

  return (
    <>
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" aria-label={`管理 ${user.email}`}>
            <EllipsisVertical />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          onCloseAutoFocus={(event) => {
            if (rolesOpen) event.preventDefault()
          }}
        >
          <EditUser user={user} onSuccess={() => setOpen(false)} />
          {!user.is_superuser && (
            <DropdownMenuItem
              onSelect={() => {
                setOpen(false)
                setRolesOpen(true)
              }}
            >
              <ShieldCheck />
              分配角色
            </DropdownMenuItem>
          )}
          <DeleteUser id={user.id} onSuccess={() => setOpen(false)} />
        </DropdownMenuContent>
      </DropdownMenu>
      {!user.is_superuser && (
        <UserRoles user={user} open={rolesOpen} setOpen={setRolesOpen} />
      )}
    </>
  )
}
