import { expect, test } from "@playwright/test"
import { randomAccount } from "./helpers"

test("找回密码提交后返回防枚举提示", async ({ page }) => {
  await page.goto("/recover-password")
  await page.getByTestId("email-input").fill(randomAccount().email)
  await page.getByRole("button", { name: "继续" }).click()
  // 无论邮箱是否存在都返回同一文案（防枚举）
  await expect(page.getByText("密码重置邮件已发送")).toBeVisible()
})

test("无效重置 token 提交失败且停留在重置页", async ({ page }) => {
  await page.goto("/reset-password?token=invalid-token-e2e")
  const newPassword = `Reset-${Date.now()}-pass`
  await page.getByTestId("new-password-input").fill(newPassword)
  await page.getByTestId("confirm-password-input").fill(newPassword)
  await page.getByRole("button", { name: "重置密码" }).click()
  // 后端拒绝无效 token，不发生跳转（"Invalid token" 已映射为中文文案）
  await expect(page).toHaveURL(/\/reset-password/)
  await expect(page.getByText("链接无效或已过期").first()).toBeVisible()
})
