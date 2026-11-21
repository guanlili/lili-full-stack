import { expect, test } from "@playwright/test"
import { loginAsAdmin, registerAndLogin } from "./helpers"

test("管理员查看审计日志并按动作过滤", async ({ page }) => {
  await loginAsAdmin(page)
  await page.goto("/admin/audit")
  // 自己的登录必然产生 login.success 审计（服务端时间倒序，首页可见）
  await expect(page.getByText("login.success").first()).toBeVisible()

  // 动作过滤（服务端模糊匹配）：不存在的动作得到空态
  await page.getByLabel("按动作过滤").fill("no-such-action")
  await expect(page.getByText("没有匹配的审计记录。")).toBeVisible()
})

test("普通用户无法访问审计日志", async ({ page }) => {
  test.skip(
    process.env.E2E_SIGNUP_DISABLED === "1",
    "注册开关关闭时跳过（.env USERS_OPEN_REGISTRATION）",
  )
  await registerAndLogin(page)
  await page.goto("/admin/audit")
  await expect(page).toHaveURL(/\/forbidden$/)
})
