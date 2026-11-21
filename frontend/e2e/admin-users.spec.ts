import { expect, test } from "@playwright/test"
import { loginAsAdmin, randomAccount } from "./helpers"

test("管理员建号 → 分配角色 → 改名 → 删除账号", async ({ page }) => {
  await loginAsAdmin(page)
  await page.goto("/admin")
  await expect(page.getByText("账号列表")).toBeVisible()

  // 建号
  const account = randomAccount()
  await page.getByRole("button", { name: "新增用户" }).click()
  await page.getByPlaceholder("请输入邮箱").fill(account.email)
  await page.getByPlaceholder("请输入姓名").fill(account.fullName)
  await page.getByPlaceholder("至少 8 个字符").fill(account.password)
  await page.getByPlaceholder("请再次输入密码").fill(account.password)
  await page.getByRole("button", { name: "创建账号" }).click()
  await expect(page.getByText(account.email).first()).toBeVisible()

  // 分配角色（行菜单 → 分配角色 → 直接保存默认访客勾选）
  await page.getByRole("button", { name: `管理 ${account.email}` }).click()
  await page.getByRole("menuitem", { name: "分配角色" }).click()
  const rolesDialog = page.getByRole("heading", { name: "分配角色" })
  await expect(rolesDialog).toBeVisible()
  await page.getByRole("button", { name: "保存角色" }).click()
  await expect(rolesDialog).toBeHidden()

  // 编辑姓名（行菜单 → 编辑用户）
  const renamed = `改名 ${Date.now()}`
  await page.getByRole("button", { name: `管理 ${account.email}` }).click()
  await page.getByRole("menuitem", { name: "编辑用户" }).click()
  await page.getByPlaceholder("请输入姓名").fill(renamed)
  await page.getByRole("button", { name: "保存", exact: true }).click()
  await expect(page.getByText(renamed).first()).toBeVisible()

  // 删除账号（行菜单 → 删除用户 → 确认）
  await page.getByRole("button", { name: `管理 ${account.email}` }).click()
  await page.getByRole("menuitem", { name: "删除用户" }).click()
  await expect(page.getByText("此操作将永久删除该用户")).toBeVisible()
  await page.getByRole("button", { name: "删除", exact: true }).click()
  await expect(page.getByText(account.email)).toHaveCount(0)
})

test("批量删除所选账号", async ({ page }) => {
  await loginAsAdmin(page)
  await page.goto("/admin")
  await expect(page.getByText("账号列表")).toBeVisible()

  const account = randomAccount()
  await page.getByRole("button", { name: "新增用户" }).click()
  await page.getByPlaceholder("请输入邮箱").fill(account.email)
  await page.getByPlaceholder("请输入姓名").fill(account.fullName)
  await page.getByPlaceholder("至少 8 个字符").fill(account.password)
  await page.getByPlaceholder("请再次输入密码").fill(account.password)
  await page.getByRole("button", { name: "创建账号" }).click()
  await expect(page.getByText(account.email).first()).toBeVisible()

  // 搜索定位该账号，勾选后批量删除
  await page.getByLabel("搜索当前页账号").fill(account.email)
  await page.getByLabel(`选择 ${account.email}`).click()
  await page.getByRole("button", { name: "删除所选" }).click()
  await expect(page.getByText(/个账号？/)).toBeVisible()
  await page.getByRole("button", { name: "确认删除" }).click()
  await expect(page.getByText(account.email)).toHaveCount(0)
})
