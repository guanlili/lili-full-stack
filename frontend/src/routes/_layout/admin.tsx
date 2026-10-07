import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense } from "react"
import { type UserPublic, UsersService } from "@/client"
import AddUser from "@/components/Admin/AddUser"
import { columns, type UserTableData } from "@/components/Admin/columns"
import PlatformTools from "@/components/Admin/PlatformTools"
import { DataTable } from "@/components/Common/DataTable"
import PendingUsers from "@/components/Pending/PendingUsers"
import { LoadingButton } from "@/components/ui/loading-button"
import { APP_NAME } from "@/config"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

function getUsersQueryOptions() {
  return {
    queryFn: () => UsersService.readUsers({ skip: 0, limit: 100 }),
    queryKey: ["users"],
  }
}

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: `用户管理 - ${APP_NAME}`,
      },
    ],
  }),
})

function UsersTableContent() {
  const { user: currentUser } = useAuth()
  const { data: users } = useSuspenseQuery(getUsersQueryOptions())
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const deleteUsersMutation = useMutation({
    mutationFn: (userIds: string[]) =>
      Promise.all(userIds.map((userId) => UsersService.deleteUser({ userId }))),
    onError: handleError.bind(showErrorToast),
    onSuccess: (_result, userIds) => {
      showSuccessToast(`已删除 ${userIds.length} 个用户`)
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const tableData: UserTableData[] = users.data.map((user: UserPublic) => ({
    ...user,
    isCurrentUser: currentUser?.id === user.id,
  }))

  return (
    <DataTable
      bulkActions={(rows, clearSelection) => (
        <LoadingButton
          className="w-full sm:w-auto"
          loading={deleteUsersMutation.isPending}
          onClick={() => {
            if (
              window.confirm(
                `确定删除选中的 ${rows.length} 个用户吗？此操作无法撤销。`,
              )
            ) {
              deleteUsersMutation.mutate(
                rows.map((row) => row.id),
                { onSuccess: clearSelection },
              )
            }
          }}
          size="sm"
          variant="destructive"
        >
          删除选中（{rows.length}）
        </LoadingButton>
      )}
      columns={columns}
      data={tableData}
      enableRowSelection={(row) => row.id !== currentUser?.id}
      getRowId={(row) => row.id}
      searchPlaceholder="搜索姓名或邮箱"
    />
  )
}

function UsersTable() {
  return (
    <Suspense fallback={<PendingUsers />}>
      <UsersTableContent />
    </Suspense>
  )
}

function Admin() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">用户管理</h1>
          <p className="text-muted-foreground">管理用户账号和权限</p>
        </div>
        <AddUser />
      </div>
      <UsersTable />
      <PlatformTools />
    </div>
  )
}
