import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"

interface TableSkeletonProps extends React.ComponentProps<"div"> {
  /** 骨架行数，默认 6 */
  rows?: number
  /** 列宽比例（ Tailwind 宽度类），默认等分 4 列 */
  columns?: string[]
  /** 是否渲染表头骨架 */
  showHeader?: boolean
}

/**
 * 列表加载骨架屏：模拟真实表头与单元格高度，避免异步加载时页面高度塌陷闪烁。
 * 仅用于数据加载中占位，不承载任何业务数据。
 */
function TableSkeleton({
  className,
  rows = 6,
  columns = ["w-12", "flex-1", "flex-1", "w-32"],
  showHeader = true,
  ...props
}: TableSkeletonProps) {
  return (
    <div className={cn("w-full", className)} {...props}>
      <Table>
        {showHeader ? (
          <TableHeader>
            <TableRow>
              {columns.map((width, index) => (
                <TableHead key={index} className={width}>
                  <Skeleton className="h-3.5 w-3/4" />
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
        ) : null}
        <TableBody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <TableRow key={rowIndex}>
              {columns.map((width, colIndex) => (
                <TableCell key={colIndex} className={width}>
                  <Skeleton
                    className={cn(
                      "h-4",
                      colIndex === 0
                        ? "w-4"
                        : rowIndex % 3 === 0
                          ? "w-2/3"
                          : "w-1/2",
                    )}
                  />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export { TableSkeleton }
