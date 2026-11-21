"use client"

// 本组件由 main.tsx 懒加载（sonner ~34KB gzip 不进首屏关键路径）。
// toast 调用统一走 lib/toast 的队列，本组件挂载前的调用不会丢。
import { useEffect } from "react"
import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from "lucide-react"
import { Toaster as Sonner, type ToasterProps } from "sonner"

import { useTheme } from "@/components/theme-provider"
import { bindToast } from "@/lib/toast"

const Toaster = ({ ...props }: ToasterProps) => {
  // 用自研 ThemeProvider 的已解析主题，跟随用户手动切换（而非系统主题）
  const { resolvedTheme } = useTheme()

  // 挂载后激活 toast API 并冲排懒加载期间积压的调用
  useEffect(() => {
    bindToast(sonnerModule)
  }, [])

  return (
    <Sonner
      theme={resolvedTheme}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
          "--border-radius": "var(--radius)",
        } as React.CSSProperties
      }
      {...props}
    />
  )
}

// bindToast 需要完整 sonner 模块；本文件已静态引入，复用同一实例
import * as sonnerModule from "sonner"

export { Toaster }
