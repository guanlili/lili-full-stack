import { queryOptions, useQuery } from "@tanstack/react-query"
import { Access as AccessService } from "@/client"
import { isLoggedIn } from "@/hooks/useAuth"

// 路由守卫（_layout beforeLoad）与组件取数共用同一份配置与缓存，
// 避免每次导航都绕过缓存直发请求。权限变更最迟在 staleTime 后生效
//（服务端 403 校验不受影响）。
export const accessQueryOptions = queryOptions({
  queryKey: ["access"],
  queryFn: () =>
    AccessService.readAccess({ throwOnError: true }).then(
      (response) => response.data,
    ),
  staleTime: 30_000,
})

export function useAccess() {
  return useQuery({
    ...accessQueryOptions,
    enabled: isLoggedIn(),
    refetchOnWindowFocus: true,
  })
}
