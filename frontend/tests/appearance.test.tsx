import assert from "node:assert/strict"
import { after, afterEach, test } from "node:test"
import "./helpers/dom"
import { cleanup, render, within } from "@testing-library/react"
import { ThemeProvider } from "@/components/theme-provider"
import { closeJSDom } from "./helpers/dom"

// ThemeProvider 初始化读取 prefers-color-scheme，jsdom 无 matchMedia，补桩。
window.matchMedia = (() => ({
  matches: false,
  media: "(prefers-color-scheme: dark)",
  onchange: null,
  addEventListener: () => {},
  removeEventListener: () => {},
  addListener: () => {},
  removeListener: () => {},
  dispatchEvent: () => true,
})) as typeof window.matchMedia
// node 测试环境裸 localStorage 不在 globalThis，挂到 jsdom window 的存储。
;(globalThis as Record<string, unknown>).localStorage = window.localStorage

const { Appearance } = await import("@/components/Common/Appearance")

afterEach(() => {
  cleanup()
  document.body.innerHTML = ""
  localStorage.clear()
})
after(() => {
  closeJSDom()
})

test("Appearance 在 ThemeProvider 内渲染主题切换触发器与 sr-only 文案", () => {
  const r = render(
    <ThemeProvider>
      <Appearance />
    </ThemeProvider>,
  )
  const view = within(r.container)
  assert.ok(view.getByTestId("theme-button"))
  assert.ok(view.getByText("切换主题"))
})
