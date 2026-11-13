import { readFileSync } from "node:fs"
import { resolve } from "node:path"

/** 读取仓库根 .env 的应用配置（与后端 pydantic-settings 同源），CI 由 .env.example 复制而来。 */
export function readRootEnv(): Record<string, string> {
  const env: Record<string, string> = {}
  const content = readFileSync(
    resolve(import.meta.dirname, "../../.env"),
    "utf8",
  )
  for (const line of content.split("\n")) {
    const m = line.match(/^([A-Z_]+)=(.*)$/)
    if (m) env[m[1]] = m[2].replace(/^"(.*)"$/, "$1")
  }
  return env
}

export const appEnv = readRootEnv()

export const ADMIN_EMAIL = appEnv.FIRST_SUPERUSER ?? "admin@example.com"
export const ADMIN_PASSWORD = appEnv.FIRST_SUPERUSER_PASSWORD ?? "changethis"

/** 生成不冲突的临时测试账号（普通用户走注册流程，注册开放开关由 .env 控制）。 */
export function randomAccount() {
  const stamp = `${Date.now()}-${Math.floor(Math.random() * 10_000)}`
  return {
    email: `e2e-${stamp}@example.com`,
    password: `E2e-${stamp}-pass`,
    fullName: `E2E ${stamp}`,
  }
}
