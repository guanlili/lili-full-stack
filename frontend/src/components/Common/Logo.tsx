import { Link } from "@tanstack/react-router"
import { APP_NAME } from "@/config"
import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

// 替换成你自己的品牌 Logo，或者修改下方的文字/图标
export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const mark = (
    <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-primary text-sm font-bold text-primary-foreground shadow-sm">
      {APP_NAME.trim().charAt(0).toUpperCase() || "A"}
    </span>
  )
  const content = (
    <span className={cn("inline-flex items-center gap-3", className)}>
      {mark}
      {variant !== "icon" && (
        <span
          className={cn(
            "font-semibold tracking-tight",
            variant === "responsive" && "group-data-[collapsible=icon]:hidden",
          )}
        >
          {APP_NAME}
        </span>
      )}
    </span>
  )

  if (!asLink) return content
  return <Link to="/">{content}</Link>
}
