import { cn } from "@/lib/utils"

/**
 * 标准页面壳子：统一最大宽度、上下内边距与纵向节奏。
 * 所有业务页面最外层优先使用本容器，不再手写 mx-auto max-w-* 的裸布局。
 */
function PageContainer({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8",
        className,
      )}
      {...props}
    />
  )
}

export { PageContainer }
