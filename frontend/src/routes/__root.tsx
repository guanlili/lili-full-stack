import { createRootRoute, HeadContent, Outlet } from "@tanstack/react-router"
import { lazy, Suspense } from "react"
import ErrorComponent from "@/components/Common/ErrorComponent"
import LoadingScreen from "@/components/Common/LoadingScreen"
import NotFound from "@/components/Common/NotFound"

const TanStackRouterDevtools = import.meta.env.PROD
  ? () => null
  : lazy(() =>
      import("@tanstack/react-router-devtools").then((r) => ({
        default: r.TanStackRouterDevtools,
      })),
    )

const ReactQueryDevtools = import.meta.env.PROD
  ? () => null
  : lazy(() =>
      import("@tanstack/react-query-devtools").then((r) => ({
        default: r.ReactQueryDevtools,
      })),
    )

export const Route = createRootRoute({
  component: () => (
    <>
      <HeadContent />
      <Outlet />
      <Suspense>
        <TanStackRouterDevtools position="bottom-right" />
        <ReactQueryDevtools initialIsOpen={false} />
      </Suspense>
    </>
  ),
  pendingComponent: () => <LoadingScreen />,
  notFoundComponent: () => <NotFound />,
  errorComponent: () => <ErrorComponent />,
})
