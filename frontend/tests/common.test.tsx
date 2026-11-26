import assert from "node:assert/strict"
import { after, afterEach, mock, test } from "node:test"
import { AxiosError } from "axios"
import "./helpers/dom"
import { cleanup, render, within } from "@testing-library/react"
import { APP_NAME } from "@/config"
import { closeJSDom } from "./helpers/dom"

const reported: unknown[] = []
const pushed: string[] = []
let resetCalled = 0

mock.module("@/lib/reportError", {
  namedExports: {
    reportError: (err: unknown) => reported.push(err),
  },
})
mock.module("@/utils", {
  namedExports: {
    extractErrorMessage: () => "这是翻译后的接口错误",
  },
})
mock.module("@tanstack/react-router", {
  namedExports: {
    useRouter: () => ({
      history: { push: (path: string) => pushed.push(path) },
    }),
  },
})

const { Footer } = await import("@/components/Common/Footer")
const { default: LoadingScreen } = await import(
  "@/components/Common/LoadingScreen"
)
const { default: ErrorComponent } = await import(
  "@/components/Common/ErrorComponent"
)

afterEach(() => {
  cleanup()
  document.body.innerHTML = ""
  reported.length = 0
  pushed.length = 0
  resetCalled = 0
})
after(() => {
  closeJSDom()
})

// ---------- Footer ----------

test("Footer 展示当前年份与应用名", () => {
  const r = render(<Footer />)
  const view = within(r.container)
  const year = String(new Date().getFullYear())
  const text = view.getByText(new RegExp(year)).textContent ?? ""
  assert.match(text, new RegExp(year))
  assert.ok(text.includes(APP_NAME))
})

// ---------- LoadingScreen ----------

test("LoadingScreen 渲染 status 角色与 sr-only 文案", () => {
  const r = render(<LoadingScreen />)
  const view = within(r.container)
  assert.ok(view.getByRole("status"))
  assert.ok(view.getByText("页面加载中"))
})

// ---------- ErrorComponent ----------

test("普通 Error：展示原始 message，上报并调用 reset 重试", () => {
  const err = new Error("boom")
  const r = render(
    <ErrorComponent
      error={err}
      reset={() => {
        resetCalled += 1
      }}
    />,
  )
  const view = within(r.container)
  assert.ok(view.getByTestId("error-component-message"))
  assert.match(
    view.getByTestId("error-component-message").textContent ?? "",
    /boom/,
  )
  assert.equal(reported.length, 1)
  assert.equal(reported[0], err)

  view.getByRole("button", { name: "重试" }).click()
  assert.equal(resetCalled, 1)
})

test("AxiosError：走 extractErrorMessage 翻译文案", () => {
  const err = new AxiosError("network")
  const r = render(<ErrorComponent error={err} />)
  const view = within(r.container)
  assert.ok(view.getByText("这是翻译后的接口错误"))
})

test("非 Error 未知值：降级为字符串展示", () => {
  const r = render(<ErrorComponent error="weird" />)
  const view = within(r.container)
  assert.ok(view.getByText("weird"))
})

test("error 为空：不展示错误信息块，返回首页跳转根路径", () => {
  const r = render(<ErrorComponent error={null} reset={() => {}} />)
  const view = within(r.container)
  assert.equal(view.queryByTestId("error-component-message"), null)
  view.getByRole("button", { name: "返回首页" }).click()
  assert.deepEqual(pushed, ["/"])
})
