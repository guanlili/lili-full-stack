import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query"
import axios from "axios"
import { describeApiError } from "@/lib/apiError"
import { expireSession } from "@/lib/session"
import { toastErrorMessage } from "@/lib/toast"

const handleApiError = (error: Error) => {
  if (axios.isCancel(error)) return
  // 只在 401（token 无效/过期）时登出；403 是"已登录但权限不足"，
  // 一并登出会把正常用户误踢下线（例如访问一个无权限的资源）
  if (axios.isAxiosError(error) && error.response?.status === 401) {
    expireSession()
    toastErrorMessage(describeApiError(error))
    return
  }

  // 其余状态码（403/422/500/网络异常等）统一收敛为中文友好提示，
  // 不透出原始英文报错或 Pydantic 校验数组
  toastErrorMessage(describeApiError(error))
}

/**
 * 导出纯分流函数便于单测：401 触发登出，其余状态码只弹中文提示。
 * 不直接挂在缓存实例上，避免测试依赖 React Query 内部 onError 调用时序。
 */
export const handleQueryError = handleApiError

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleApiError,
  }),
  mutationCache: new MutationCache({
    onError: handleApiError,
  }),
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
})
