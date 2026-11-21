import { expect, test } from "@playwright/test"
import { registerAndLogin } from "./helpers"

// 覆盖本次安全加固的三条密码复核路径：改邮箱、改密码、注销账号。
// 设置页分三个标签（个人资料 / 登录安全 / 账号注销），toast 会堆叠，断言用 .first()
test("个人资料：改名免密，改邮箱必须复核当前密码", async ({ page }) => {
  test.skip(
    process.env.E2E_SIGNUP_DISABLED === "1",
    "注册开关关闭时跳过（.env USERS_OPEN_REGISTRATION）",
  )
  const account = await registerAndLogin(page)
  await page.goto("/settings")
  await expect(page.getByRole("heading", { name: "账号设置" })).toBeVisible()

  // 改名不需要密码
  await page.getByRole("button", { name: "编辑资料" }).click()
  await page.getByPlaceholder("填写你的姓名").fill("E2E 改名")
  await page.getByRole("button", { name: "保存资料" }).click()
  await expect(page.getByText("个人资料更新成功").first()).toBeVisible()

  // 改邮箱：不输密码 → 表单层拦截
  await page.getByRole("button", { name: "编辑资料" }).click()
  await page.getByLabel("邮箱").fill(`renamed-${account.email}`)
  await page.getByRole("button", { name: "保存资料" }).click()
  await expect(page.getByText("更改邮箱需要输入当前密码确认")).toBeVisible()

  // 错误密码 → 后端拒绝
  await page.getByLabel("当前密码").fill("wrong-password")
  await page.getByRole("button", { name: "保存资料" }).click()
  await expect(page.getByText("密码错误").first()).toBeVisible()

  // 正确密码 → 改绑成功
  await page.getByLabel("当前密码").fill(account.password)
  await page.getByRole("button", { name: "保存资料" }).click()
  await expect(page.getByText("个人资料更新成功").first()).toBeVisible()
  await expect(page.getByText(`renamed-${account.email}`).first()).toBeVisible()
})

test("修改密码：错误旧密码被拒，成功后旧会话失效", async ({ page }) => {
  test.skip(
    process.env.E2E_SIGNUP_DISABLED === "1",
    "注册开关关闭时跳过（.env USERS_OPEN_REGISTRATION）",
  )
  const account = await registerAndLogin(page)
  await page.goto("/settings")
  await page.getByRole("tab", { name: "登录安全" }).click()

  const newPassword = `New-${Date.now()}-pass`

  // 错误的当前密码 → 400
  await page.getByLabel("当前密码").fill("wrong-password")
  await page.getByLabel("新密码").fill(newPassword)
  await page.getByLabel("确认密码").fill(newPassword)
  await page.getByRole("button", { name: "修改密码" }).click()
  await expect(page.getByText("密码错误").first()).toBeVisible()

  // 正确修改 → token_version 提升，旧 access token 立即失效；
  // 前端在下次请求触发 401 时自动登出，这里主动导航触发它
  await page.getByLabel("当前密码").fill(account.password)
  await page.getByLabel("新密码").fill(newPassword)
  await page.getByLabel("确认密码").fill(newPassword)
  await page.getByRole("button", { name: "修改密码" }).click()
  await expect(page.getByText("密码修改成功").first()).toBeVisible()
  await page.goto("/")
  await expect(page).toHaveURL(/\/login/, { timeout: 15_000 })

  // 旧密码已失效，新密码可登录
  await page.getByTestId("email-input").fill(account.email)
  await page.getByTestId("password-input").fill(account.password)
  await page.getByRole("button", { name: "登录" }).click()
  await expect(page.getByText("邮箱或密码错误")).toBeVisible()

  await page.getByTestId("password-input").fill(newPassword)
  await page.getByRole("button", { name: "登录" }).click()
  await expect(page.getByText("很高兴再次见到你")).toBeVisible()
})

test("注销账号必须输入当前密码", async ({ page }) => {
  test.skip(
    process.env.E2E_SIGNUP_DISABLED === "1",
    "注册开关关闭时跳过（.env USERS_OPEN_REGISTRATION）",
  )
  const account = await registerAndLogin(page)
  await page.goto("/settings")
  await page.getByRole("tab", { name: "账号注销" }).click()

  await page.getByRole("button", { name: "注销账号" }).click()
  // 不输密码时确认按钮不可用
  const confirm = page.getByRole("button", { name: "确认注销" })
  await expect(confirm).toBeDisabled()

  await page.getByLabel("当前密码").fill(account.password)
  await expect(confirm).toBeEnabled()
  await confirm.click()

  await expect(page.getByText("账号已成功注销").first()).toBeVisible()
  await expect(page).toHaveURL(/\/login/)
})
