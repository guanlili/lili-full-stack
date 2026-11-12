import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { Footer } from "@/components/Common/Footer"
import AppSidebar from "@/components/Sidebar/AppSidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { accessQueryOptions } from "@/hooks/useAccess"
import { isLoggedIn } from "@/hooks/useAuth"
import { canAccessPath } from "@/lib/access"
import { queryClient } from "@/lib/queryClient"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async ({ location }) => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
    if (location.pathname.replace(/\/$/, "") !== "/forbidden") {
      // 复用 ["access"] 查询缓存（staleTime 内不重复请求），与 useAccess 同源
      const access = await queryClient.ensureQueryData(accessQueryOptions)
      if (!canAccessPath(access.pages, location.pathname)) {
        throw redirect({ to: "/forbidden" })
      }
    }
  },
})

function Layout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-w-0">
        <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
        </header>
        <main className="min-w-0 flex-1 p-4 sm:p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}
