import {
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table"
import {
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  Users,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useAdminUsers } from "@/hooks/useAdminUsers"
import useAuth from "@/hooks/useAuth"
import AddUser from "./AddUser"
import { columns } from "./columns"

export default function UsersPanel() {
  const { user } = useAuth()
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("all")
  const [selected, setSelected] = useState<string[]>([])
  const [confirmDelete, setConfirmDelete] = useState(false)
  const { query, remove } = useAdminUsers(page, pageSize)
  const total = query.data?.count ?? 0
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  useEffect(() => {
    if (query.data && !query.isPlaceholderData && page >= pageCount)
      setPage(pageCount - 1)
  }, [query.data, query.isPlaceholderData, page, pageCount])
  const data = useMemo(
    () =>
      (query.data?.data ?? [])
        .filter((account) => {
          const matchesSearch = `${account.full_name ?? ""} ${account.email}`
            .toLowerCase()
            .includes(search.trim().toLowerCase())
          return (
            matchesSearch &&
            (status === "all" || account.is_active === (status === "active"))
          )
        })
        .map((account) => ({
          ...account,
          isCurrentUser: account.id === user?.id,
        })),
    [query.data, search, status, user?.id],
  )
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })
  const selectable = data
    .filter((account) => !account.isCurrentUser)
    .map((account) => account.id)
  const allSelected =
    selectable.length > 0 && selectable.every((id) => selected.includes(id))
  const changePage = (next: number) => {
    setPage(next)
    setSelected([])
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-3">
        {[
          {
            label: "账号总数",
            value: query.isPending ? "—" : total,
            icon: Users,
            description: "系统中的所有账号",
          },
          {
            label: "本页已启用",
            value:
              query.data?.data.filter((account) => account.is_active).length ??
              "—",
            icon: ShieldCheck,
            description: "可正常登录的账号",
          },
          {
            label: "本页管理员",
            value:
              query.data?.data.filter((account) => account.is_superuser)
                .length ?? "—",
            icon: ShieldCheck,
            description: "拥有系统完整管理权限",
          },
        ].map((item) => (
          <Card key={item.label} className="gap-0 py-0 shadow-none">
            <CardContent className="flex items-start justify-between p-3 sm:p-5">
              <div>
                <p className="text-sm text-muted-foreground">{item.label}</p>
                <p className="my-2 text-3xl font-semibold tracking-tight">
                  {item.value}
                </p>
                <p className="hidden text-xs text-muted-foreground sm:block">
                  {item.description}
                </p>
              </div>
              <item.icon className="hidden size-5 text-muted-foreground md:block" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="gap-0 overflow-hidden py-0 shadow-none">
        <div className="flex flex-col gap-4 border-b p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-semibold">账号列表</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              创建账号、调整访问权限，或停用不再使用的账号。
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <AddUser />
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 border-b p-4">
          <div className="relative min-w-48 flex-1 sm:max-w-sm">
            <Search className="absolute left-3 top-3 size-4 text-muted-foreground" />
            <Input
              aria-label="搜索当前页账号"
              className="pl-9"
              placeholder="搜索当前页的姓名、邮箱"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value)
                setSelected([])
              }}
            />
          </div>
          <Select
            value={status}
            onValueChange={(value) => {
              setStatus(value)
              setSelected([])
            }}
          >
            <SelectTrigger className="w-36" aria-label="筛选当前页状态">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="active">已启用</SelectItem>
              <SelectItem value="inactive">已停用</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="ghost"
            size="icon"
            aria-label="刷新账号列表"
            disabled={query.isFetching}
            onClick={() => {
              setSelected([])
              query.refetch()
            }}
          >
            <RefreshCw
              className={query.isFetching ? "size-4 animate-spin" : "size-4"}
            />
          </Button>
        </div>
        {selected.length > 0 && (
          <div className="flex flex-wrap items-center gap-3 border-b bg-muted/40 px-5 py-3 text-sm">
            <span>已选择 {selected.length} 个账号</span>
            <Button variant="ghost" size="sm" onClick={() => setSelected([])}>
              取消选择
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setConfirmDelete(true)}
            >
              <Trash2 className="size-4" />
              删除所选
            </Button>
          </div>
        )}
        {query.isError ? (
          <div role="alert" className="space-y-3 p-10 text-center">
            <p>账号列表加载失败</p>
            <Button variant="outline" onClick={() => query.refetch()}>
              重新加载
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12 pl-5">
                  <Checkbox
                    aria-label="选择当前页可操作账号"
                    disabled={query.isPlaceholderData || !selectable.length}
                    checked={
                      allSelected ||
                      (selectable.some((id) => selected.includes(id)) &&
                        "indeterminate")
                    }
                    onCheckedChange={(checked) =>
                      setSelected(checked ? selectable : [])
                    }
                  />
                </TableHead>
                {table.getHeaderGroups()[0]?.headers.map((header) => (
                  <TableHead key={header.id}>
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext(),
                    )}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {query.isPending ? (
                <TableRow>
                  <TableCell
                    colSpan={columns.length + 1}
                    className="h-40 text-center text-muted-foreground"
                  >
                    正在加载账号…
                  </TableCell>
                </TableRow>
              ) : table.getRowModel().rows.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.original.id}
                    className={
                      selected.includes(row.original.id) ? "bg-muted/40" : ""
                    }
                  >
                    <TableCell className="pl-5">
                      <Checkbox
                        aria-label={`选择 ${row.original.email}`}
                        disabled={
                          row.original.isCurrentUser || query.isPlaceholderData
                        }
                        checked={selected.includes(row.original.id)}
                        onCheckedChange={(checked) =>
                          setSelected((previous) =>
                            checked
                              ? [...previous, row.original.id]
                              : previous.filter((id) => id !== row.original.id),
                          )
                        }
                      />
                    </TableCell>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={columns.length + 1}
                    className="h-40 text-center text-muted-foreground"
                  >
                    {search || status !== "all"
                      ? "当前页没有符合条件的账号，请调整筛选或切换页面。"
                      : "还没有用户，点击新增用户创建第一个账号。"}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t px-5 py-4 text-sm text-muted-foreground">
          <span>
            共 {total} 个账号 · 本页显示 {data.length} 个
          </span>
          <div className="flex items-center gap-3">
            <Select
              value={String(pageSize)}
              onValueChange={(value) => {
                setPageSize(Number(value))
                changePage(0)
              }}
            >
              <SelectTrigger className="w-28" aria-label="每页账号数">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[10, 25, 50].map((size) => (
                  <SelectItem key={size} value={String(size)}>
                    {size} 条 / 页
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <span>
              {page + 1} / {pageCount}
            </span>
            <Button
              variant="outline"
              size="icon"
              aria-label="上一页"
              disabled={page === 0 || query.isFetching}
              onClick={() => changePage(page - 1)}
            >
              <ChevronLeft className="size-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              aria-label="下一页"
              disabled={page + 1 >= pageCount || query.isFetching}
              onClick={() => changePage(page + 1)}
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      </Card>
      <Dialog
        open={confirmDelete}
        onOpenChange={(open) => {
          if (!remove.isPending) setConfirmDelete(open)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>删除 {selected.length} 个账号？</DialogTitle>
            <DialogDescription>
              这些账号将被永久删除，无法恢复。如仅需限制登录，建议编辑账号并取消启用。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              disabled={remove.isPending}
              onClick={() => setConfirmDelete(false)}
            >
              取消
            </Button>
            <LoadingButton
              variant="destructive"
              loading={remove.isPending}
              onClick={() =>
                remove.mutate(selected, {
                  onSuccess: () => {
                    setSelected([])
                    setConfirmDelete(false)
                  },
                })
              }
            >
              确认删除
            </LoadingButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
