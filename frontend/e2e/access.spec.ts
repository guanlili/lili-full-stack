import { expect, test } from "@playwright/test"
import { ADMIN_EMAIL, ADMIN_PASSWORD, appEnv, randomAccount } from "./helpers"

test("注册 → 登录 → 无权限页跳 forbidden", async ({ page }) => {
  test.skip(
    appEnv.USERS_OPEN_REGISTRATION?.toLowerCase() === "false",
    "注册开关关闭时跳过（.env USERS_OPEN_REGISTRATION）",
  )
  const account = randomAccount()

  await page.goto("/signup")
  await page.getByTestId("full-name-input").fill(account.fullName)
  await page.getByTestId("email-input").fill(account.email)
  await page.getByTestId("password-input").fill(account.password)
  await page.getByTestId("confirm-password-input").fill(account.password)
  await page.getByRole("button", { name: "注册" }).click()
  await expect(page).toHaveURL(/\/login$/)
  // 注册完成后登录（断言用工作台独有文案，不能用登录页自身的"欢迎回来"）。
  // 冷启动时跳转后表单可能重挂载吞掉 fill 的值，fill+校验整体重试到值落住
  await expect(async () => {
    await page.getByTestId("email-input").fill(account.email)
    await expect(page.getByTestId("email-input")).toHaveValue(account.email)
  }).toPass()
  await page.getByTestId("password-input").fill(account.password)
  await page.getByRole("button", { name: "登录" }).click()
  await expect(page.getByText("很高兴再次见到你")).toBeVisible()

  // 普通用户访问管理页 → 权限守卫重定向 forbidden
  await page.goto("/admin")
  await expect(page).toHaveURL(/\/forbidden$/)
})

test("管理员可访问用户管理页", async ({ page }) => {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(ADMIN_EMAIL)
  await page.getByTestId("password-input").fill(ADMIN_PASSWORD)
  await page.getByRole("button", { name: "登录" }).click()
  await expect(page.getByText("很高兴再次见到你")).toBeVisible()

  await page.goto("/admin")
  await expect(page).toHaveURL(/\/admin$/)
  // 用户列表已加载（管理页特征：表格表头）
  await expect(page.getByText("邮箱")).toBeVisible()
})
