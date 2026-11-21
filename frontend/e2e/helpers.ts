import { readFileSync } from "node:fs"
import { resolve } from "node:path"

import { expect, type Page } from "@playwright/test"

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

/** 登录并等待工作台特征文案出现（登录页自身也有"欢迎回来"，不能用作断言）。 */
export async function login(page: Page, email: string, password: string) {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "登录" }).click()
  await expect(page.getByText("很高兴再次见到你")).toBeVisible()
}

export async function loginAsAdmin(page: Page) {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
}

/** 注册随机账号并登录（注册开关由 .env USERS_OPEN_REGISTRATION 控制）。 */
export async function registerAndLogin(page: Page) {
  const account = randomAccount()
  await page.goto("/signup")
  await page.getByTestId("full-name-input").fill(account.fullName)
  await page.getByTestId("email-input").fill(account.email)
  await page.getByTestId("password-input").fill(account.password)
  await page.getByTestId("confirm-password-input").fill(account.password)
  await page.getByRole("button", { name: "注册" }).click()
  await expect(page).toHaveURL(/\/login$/)
  await login(page, account.email, account.password)
  return account
}
