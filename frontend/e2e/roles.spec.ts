import { expect, test } from "@playwright/test"
import { loginAsAdmin } from "./helpers"

// 角色卡片按列表顺序渲染，新建角色追加在末尾，用 .last() 定位新建的卡
test("建角色 → 勾权限保存 → 删除角色", async ({ page }) => {
  await loginAsAdmin(page)
  await page.goto("/roles")
  await expect(page.getByText("新建角色")).toBeVisible()

  const roleName = `e2e角色${Date.now()}`
  await page.getByLabel("新角色名称").fill(roleName)
  await page.getByRole("button", { name: "新建角色" }).click()

  const card = page.locator('[data-slot="card"]').filter({
    hasText: roleName,
  })
  await expect(card).toBeVisible()
  // 新角色默认无权限，保存按钮在勾选前不可用
  await expect(card.getByRole("button", { name: "保存权限" })).toBeDisabled()

  // 勾选"账号设置"后保存
  await card.getByText("账号设置").click()
  await card.getByRole("button", { name: "保存权限" }).click()
  // 保存成功后权限与服务器一致，按钮回到禁用态
  await expect(card.getByRole("button", { name: "保存权限" })).toBeDisabled()

  // 删除角色（未被使用，可删）
  await card.getByRole("button", { name: "删除角色" }).click()
  await expect(page.getByText(/将被永久删除/)).toBeVisible()
  await page.getByRole("button", { name: "确认删除" }).click()
  await expect(card).toHaveCount(0)
})
