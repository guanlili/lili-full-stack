import type { LucideIcon } from "lucide-react"
import { TrendingDown, TrendingUp } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

type Trend = "up" | "down" | "flat"

interface StatCardProps extends React.ComponentProps<"div"> {
  /** 指标名称 */
  label: React.ReactNode
  /** 指标数值（数字/ID 自动等宽对齐） */
  value: React.ReactNode
  /** 图标（Lucide），可选 */
  icon?: LucideIcon
  /** 描述/辅助说明，可选 */
  description?: React.ReactNode
  /** 环比趋势方向，可选 */
  trend?: Trend
  /** 环比数值文案（如 "+12.5%"），配合 trend 展示 */
  trendLabel?: React.ReactNode
}

const trendStyles: Record<Trend, { className: string; Icon: LucideIcon }> = {
  up: { className: "bg-success/10 text-success", Icon: TrendingUp },
  down: { className: "bg-destructive/10 text-destructive", Icon: TrendingDown },
  flat: {
    className: "bg-secondary text-secondary-foreground",
    Icon: TrendingUp,
  },
}

/**
 * 单个核心指标卡片：label + 等宽数字 + 图标 + 趋势徽章 + 描述。
 * 复用 Card 的 shadow-xs 与 hover 升阶质感；数值强制 tabular-nums 对齐。
 */
function StatCard({
  className,
  label,
  value,
  icon: Icon,
  description,
  trend,
  trendLabel,
  ...props
}: StatCardProps) {
  const trendMeta = trend ? trendStyles[trend] : null
  return (
    <Card className={cn("gap-0 py-0 shadow-xs", className)} {...props}>
      <CardContent className="flex items-start justify-between gap-4 p-4 sm:p-5">
        <div className="flex min-w-0 flex-col gap-2">
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="font-mono text-2xl font-semibold tracking-tight text-foreground [font-variant-numeric:tabular-nums] sm:text-3xl">
            {value}
          </p>
          {trendMeta && trendLabel ? (
            <Badge
              variant="outline"
              className={cn("w-fit", trendMeta.className)}
            >
              <trendMeta.Icon className="size-3" />
              {trendLabel}
            </Badge>
          ) : null}
          {description ? (
            <p className="hidden text-xs text-muted-foreground sm:block">
              {description}
            </p>
          ) : null}
        </div>
        {Icon ? (
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-accent text-muted-foreground">
            <Icon className="size-5" />
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

interface StatCardGridProps extends React.ComponentProps<"div"> {
  children: React.ReactNode
  /** 栅格列数响应式配置，默认 1 / 2 / 3 列 */
  columns?: 2 | 3 | 4
}

/** 指标卡组栅格：默认三列，随屏宽降为两列/单列 */
function StatCardGrid({
  className,
  children,
  columns = 3,
  ...props
}: StatCardGridProps) {
  const cols = {
    2: "sm:grid-cols-2",
    3: "sm:grid-cols-2 lg:grid-cols-3",
    4: "sm:grid-cols-2 lg:grid-cols-4",
  }[columns]
  return (
    <div className={cn("grid grid-cols-1 gap-4", cols, className)} {...props}>
      {children}
    </div>
  )
}

export { StatCard, StatCardGrid }
