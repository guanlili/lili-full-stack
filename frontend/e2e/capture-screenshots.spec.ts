import { expect, test } from "@playwright/test"
import { ADMIN_EMAIL, ADMIN_PASSWORD } from "./helpers"

// README/文档截图刷新工具：默认跳过，CI 不跑。
// 用法：CAPTURE_SCREENSHOTS=1 npx playwright test capture-screenshots
// 产物覆盖 docs/screenshots/ 下同名文件（登录/工作台/用户管理/审计日志）。
const OUT_DIR = new URL("../../docs/screenshots/", import.meta.url).pathname

test.beforeEach(() => {
  test.skip(
    !process.env.CAPTURE_SCREENSHOTS,
    "仅显式设置 CAPTURE_SCREENSHOTS=1 时运行（截图刷新工具，非回归测试）",
  )
})

test("刷新基线截图", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 })

  // 1. 登录页（登出态）
  await page.goto("/login")
  await expect(
    page.getByRole("heading", { name: "登录你的账号" }),
  ).toBeVisible()
  await page.screenshot({ path: `${OUT_DIR}login.png` })

  // 2. 登录进工作台
  await page.getByTestId("email-input").fill(ADMIN_EMAIL)
  await page.getByTestId("password-input").fill(ADMIN_PASSWORD)
  await page.getByRole("button", { name: "登录" }).click()
  await expect(page.getByText("很高兴再次见到你")).toBeVisible()
  await page.screenshot({ path: `${OUT_DIR}dashboard.png` })

  // 3. 用户管理
  await page.goto("/admin")
  await expect(page.getByRole("heading", { name: "用户管理" })).toBeVisible()
  await expect(page.getByText("账号列表")).toBeVisible()
  await page.screenshot({ path: `${OUT_DIR}user-management.png` })

  // 4. 审计日志
  await page.goto("/admin/audit")
  await expect(page.getByRole("heading", { name: "审计日志" })).toBeVisible()
  await expect(page.getByText("共 ").first()).toBeVisible()
  await page.screenshot({ path: `${OUT_DIR}audit.png` })
})
