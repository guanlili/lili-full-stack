import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { RolesService } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export function useRoles() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const query = useQuery({
    queryKey: ["roles"],
    queryFn: RolesService.readRoles,
  })
  const create = useMutation({
    mutationFn: (name: string) =>
      RolesService.createRole({ requestBody: { name } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] })
      showSuccessToast("角色已创建，请配置页面权限")
    },
    onError: handleError.bind(showErrorToast),
  })
  const update = useMutation({
    mutationFn: ({
      roleId,
      permissions,
    }: {
      roleId: string
      permissions: string[]
    }) =>
      RolesService.updatePermissions({ roleId, requestBody: { permissions } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] })
      queryClient.invalidateQueries({ queryKey: ["access"] })
      showSuccessToast("权限已保存")
    },
    onError: handleError.bind(showErrorToast),
  })
  return { query, create, update }
}

export function useUserRoles(userId: string, enabled: boolean) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const query = useQuery({
    queryKey: ["user-roles", userId],
    queryFn: () => RolesService.readUserRoles({ userId }),
    enabled,
  })
  const update = useMutation({
    mutationFn: (roleIds: string[]) =>
      RolesService.updateUserRoles({
        userId,
        requestBody: { role_ids: roleIds },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user-roles", userId] })
      queryClient.invalidateQueries({ queryKey: ["access"] })
      showSuccessToast("用户角色已更新")
    },
    onError: handleError.bind(showErrorToast),
  })
  return { query, update }
}
