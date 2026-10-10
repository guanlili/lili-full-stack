import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { UsersService } from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

export function useAdminUsers(page: number, pageSize: number) {
  const client = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const query = useQuery({
    queryKey: ["users", { page, pageSize }],
    queryFn: () =>
      UsersService.readUsers({ skip: page * pageSize, limit: pageSize }),
    placeholderData: keepPreviousData,
  })
  const remove = useMutation({
    mutationFn: async (ids: string[]) => {
      const results = await Promise.allSettled(
        ids.map((userId) => UsersService.deleteUser({ userId })),
      )
      return {
        succeeded: results.filter((result) => result.status === "fulfilled")
          .length,
        total: ids.length,
      }
    },
    onSuccess: ({ succeeded, total }) => {
      if (succeeded) showSuccessToast(`已删除 ${succeeded} 个账号`)
      if (succeeded < total)
        showErrorToast(`${total - succeeded} 个账号删除失败，请刷新列表后重试`)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => client.invalidateQueries({ queryKey: ["users"] }),
  })
  return { query, remove }
}
