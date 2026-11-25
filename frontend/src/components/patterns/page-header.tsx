import { cn } from "@/lib/utils"

interface PageHeaderProps
  extends Omit<React.ComponentProps<"header">, "title"> {
  /** 眉标（分组/面包屑层级），可选 */
  eyebrow?: string
  /** 页面主标题 */
  title: React.ReactNode
  /** 副标题/说明文案，可选 */
  description?: React.ReactNode
  /** 右上角主操作区插槽（主按钮、筛选、批量操作等） */
  actions?: React.ReactNode
}

/**
 * 标准页头：眉标 + 主标题（display 字体）+ 副标题 + 右侧操作区插槽。
 * 统一标题字阶、字距与下方内容区呼吸间距；业务页面禁止手写裸 h1 + p 组合。
 */
function PageHeader({
  className,
  eyebrow,
  title,
  description,
  actions,
  ...props
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between",
        className,
      )}
      {...props}
    >
      <div className="flex min-w-0 flex-col gap-2">
        {eyebrow ? (
          <p className="text-xs font-medium tracking-widest text-muted-foreground">
            {eyebrow}
          </p>
        ) : null}
        <h1 className="font-display text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          {title}
        </h1>
        {description ? (
          <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {actions}
        </div>
      ) : null}
    </header>
  )
}

export { PageHeader }
