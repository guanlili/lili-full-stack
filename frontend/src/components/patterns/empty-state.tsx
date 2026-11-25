import type { LucideIcon } from "lucide-react"
import { Inbox } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface EmptyStateProps extends Omit<React.ComponentProps<"div">, "title"> {
  /** 空态图标（Lucide），默认 Inbox */
  icon?: LucideIcon
  /** 主说明文案 */
  title: React.ReactNode
  /** 副说明文案，可选 */
  description?: React.ReactNode
  /** 引导操作 CTA，可选；传入按钮配置或自定义节点 */
  action?: React.ReactNode
}

/**
 * 标准空状态：图标 + 主副文案 + 引导操作，替换裸纯文本"暂无数据"。
 * 用于列表无数据、搜索无结果、空面板等场景。
 */
function EmptyState({
  className,
  icon: Icon = Inbox,
  title,
  description,
  action,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 px-6 py-12 text-center",
        className,
      )}
      {...props}
    >
      <div className="flex size-12 items-center justify-center rounded-full bg-accent text-muted-foreground">
        <Icon className="size-6" />
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-foreground">{title}</p>
        {description ? (
          <p className="max-w-sm text-sm text-muted-foreground">
            {description}
          </p>
        ) : null}
      </div>
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  )
}

/** 空态 CTA 按钮的快捷封装，保持与主按钮令牌一致 */
function EmptyStateAction(props: React.ComponentProps<typeof Button>) {
  return <Button variant="outline" size="sm" {...props} />
}

export { EmptyState, EmptyStateAction }
