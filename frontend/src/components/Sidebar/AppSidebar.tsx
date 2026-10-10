import { Home, ShieldCheck, Users } from "lucide-react"

import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import { useAccess } from "@/hooks/useAccess"
import useAuth from "@/hooks/useAuth"
import { Main, type NavItem } from "./Main"
import { User } from "./User"

const baseItems: NavItem[] = [{ icon: Home, title: "工作台", path: "/" }]

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  const { data: access } = useAccess()
  const availableItems: NavItem[] = [
    ...baseItems,
    { icon: Users, title: "用户管理", path: "/admin" },
    { icon: ShieldCheck, title: "角色权限", path: "/roles" },
  ]
  const items = availableItems.filter((item) =>
    access?.pages.some((page) => page.path === item.path && page.allowed),
  )

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
