import { RefreshCw } from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useAuditLogs } from "@/hooks/useAuditLogs"

const PAGE_SIZE = 20

function formatTime(value?: string | null) {
  if (!value) return "—"
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString("zh-CN", { hour12: false })
}

function formatDetails(details?: Record<string, unknown> | null) {
  if (!details) return "—"
  return JSON.stringify(details)
}

export default function AuditPanel() {
  const [page, setPage] = useState(0)
  const [actionInput, setActionInput] = useState("")
  const [action, setAction] = useState("")
  const appliedActionRef = useRef("")
  const { query } = useAuditLogs(page, PAGE_SIZE, action)
  const total = query.data?.count ?? 0
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

  // 动作过滤走服务端模糊匹配，输入防抖后再查询；过滤词（trim 后）没变时
  // 不重置页码——否则多敲一个空格就会跳回第一页
  useEffect(() => {
    const timer = setTimeout(() => {
      const next = actionInput.trim()
      if (next !== appliedActionRef.current) {
        appliedActionRef.current = next
        setAction(next)
        setPage(0)
      }
    }, 400)
    return () => clearTimeout(timer)
  }, [actionInput])

  // 越界收敛：保留期清理/过滤使总页数缩小时回到最后一页（与 UsersPanel 同款）
  useEffect(() => {
    if (query.data && !query.isPlaceholderData && page >= pageCount)
      setPage(pageCount - 1)
  }, [query.data, query.isPlaceholderData, page, pageCount])

  return (
    <Card className="gap-0 overflow-hidden py-0 shadow-none">
      <div className="flex flex-col gap-4 border-b p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-semibold">审计记录</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            登录、权限与账号变更等关键操作的时间线，仅管理员可查。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            aria-label="按动作过滤"
            placeholder="按动作过滤，如 login"
            className="w-48"
            maxLength={100}
            value={actionInput}
            onChange={(event) => setActionInput(event.target.value)}
          />
          <Button
            variant="outline"
            size="icon"
            aria-label="刷新审计日志"
            disabled={query.isFetching}
            onClick={() => query.refetch()}
          >
            <RefreshCw className={query.isFetching ? "animate-spin" : ""} />
          </Button>
        </div>
      </div>
      <Table aria-busy={query.isFetching}>
        <TableHeader>
          <TableRow>
            <TableHead className="pl-5">时间</TableHead>
            <TableHead>动作</TableHead>
            <TableHead>操作者</TableHead>
            <TableHead>资源类型</TableHead>
            <TableHead>详情</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {query.isPending ? (
            <TableRow>
              <TableCell
                colSpan={5}
                role="status"
                className="h-24 text-center text-muted-foreground"
              >
                正在加载审计日志…
              </TableCell>
            </TableRow>
          ) : query.isError ? (
            <TableRow>
              <TableCell
                colSpan={5}
                role="alert"
                className="h-24 text-center text-muted-foreground"
              >
                审计日志加载失败{" "}
                <Button
                  variant="link"
                  onClick={() => query.refetch()}
                  className="h-auto p-0"
                >
                  重试
                </Button>
              </TableCell>
            </TableRow>
          ) : query.data && query.data.data.length > 0 ? (
            query.data.data.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="whitespace-nowrap pl-5 text-muted-foreground">
                  {formatTime(item.created_at)}
                </TableCell>
                <TableCell className="font-mono text-xs">
                  {item.action}
                </TableCell>
                <TableCell className="break-all">
                  {item.actor_email ?? (
                    <span
                      className="text-muted-foreground"
                      title={item.actor_user_id ?? undefined}
                    >
                      已删除用户
                    </span>
                  )}
                </TableCell>
                <TableCell>{item.resource_type}</TableCell>
                <TableCell
                  className="max-w-64 truncate font-mono text-xs text-muted-foreground"
                  tabIndex={0}
                  title={formatDetails(item.details)}
                >
                  {formatDetails(item.details)}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell
                colSpan={5}
                className="h-24 text-center text-muted-foreground"
              >
                没有匹配的审计记录。
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <div className="flex items-center justify-between gap-3 border-t p-4">
        <p className="text-sm text-muted-foreground">共 {total} 条</p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            aria-label="上一页"
            disabled={page <= 0 || query.isFetching}
            onClick={() => setPage((value) => Math.max(0, value - 1))}
          >
            上一页
          </Button>
          <span className="text-sm text-muted-foreground">
            {page + 1} / {pageCount}
          </span>
          <Button
            variant="outline"
            aria-label="下一页"
            disabled={page >= pageCount - 1 || query.isFetching}
            onClick={() => setPage((value) => value + 1)}
          >
            下一页
          </Button>
        </div>
      </div>
    </Card>
  )
}
