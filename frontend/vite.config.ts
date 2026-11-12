import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
  build: {
    // hidden：生成 .map 但产物不引用——线上错误栈可本地还原，不向访客暴露源码映射
    sourcemap: "hidden",
    rollupOptions: {
      output: {
        // rolldown（Vite 8）只支持函数形式：稳定依赖单独成 chunk，
        // 业务代码迭代时这些层的浏览器缓存不失效
        manualChunks(id: string) {
          if (!id.includes("node_modules")) return undefined
          if (
            /node_modules\/react\//.test(id) ||
            /node_modules\/react-dom\//.test(id)
          ) {
            return "vendor-react"
          }
          if (id.includes("node_modules/@tanstack/")) {
            return "vendor-tanstack"
          }
          return undefined
        },
      },
    },
  },
})
