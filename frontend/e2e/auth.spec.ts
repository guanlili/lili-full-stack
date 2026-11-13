import { expect, test } from "@playwright/test"
import { ADMIN_EMAIL, ADMIN_PASSWORD } from "./helpers"

test("未登录访问受保护页重定向到登录页", async ({ page }) => {
  await page.goto("/admin")
  await expect(page).toHaveURL(/\/login/)
})

test("正确凭据登录进入工作台", async ({ page }) => {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(ADMIN_EMAIL)
  await page.getByTestId("password-input").fill(ADMIN_PASSWORD)
  await page.getByRole("button", { name: "登录" }).click()

  // 注意不能用"欢迎回来"做断言——那是登录页自己的标题文案
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByText("很高兴再次见到你")).toBeVisible()
})

test("错误密码提示且停留在登录页", async ({ page }) => {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(ADMIN_EMAIL)
  await page.getByTestId("password-input").fill("wrong-password")
  await page.getByRole("button", { name: "登录" }).click()

  await expect(page.getByText("邮箱或密码错误")).toBeVisible()
  await expect(page).toHaveURL(/\/login/)
})

test("退出登录后受保护页再次重定向", async ({ page }) => {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(ADMIN_EMAIL)
  await page.getByTestId("password-input").fill(ADMIN_PASSWORD)
  await page.getByRole("button", { name: "登录" }).click()
  await expect(page.getByText("很高兴再次见到你")).toBeVisible()

  // 退出登录在侧边栏用户菜单内，先点开用户菜单
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: /退出登录/ }).click()
  await expect(page).toHaveURL(/\/login/)

  await page.goto("/admin")
  await expect(page).toHaveURL(/\/login/)
})
