import assert from "node:assert/strict"
import { test } from "node:test"

// node 测试环境无浏览器全局：先桩 localStorage 与 location，再导入 session 模块
const storage = new Map<string, string>()
;(globalThis as Record<string, unknown>).localStorage = {
  getItem: (key: string) => storage.get(key) ?? null,
  setItem: (key: string, value: string) => storage.set(key, String(value)),
  removeItem: (key: string) => {
    storage.delete(key)
  },
}
;(globalThis as Record<string, unknown>).window = {
  location: {
    pathname: "/admin",
    search: "",
    assign: (target: string) => (assigned = target),
  },
}

let assigned: string | null = null

const { clearSession, expireSession, startSession } = await import(
  "../src/lib/session.ts"
)

test("startSession 写入会话标记与 access token，兼容空 refresh_token", () => {
  storage.clear()
  startSession({ access_token: "abc", refresh_token: null })
  const ls = globalThis.localStorage
  assert.ok(ls.getItem("session_id"))
  assert.equal(ls.getItem("access_token"), "abc")
  assert.equal(ls.getItem("refresh_token"), null)
})

test("clearSession 清空三类本地凭据", () => {
  const ls = globalThis.localStorage
  ls.setItem("access_token", "x")
  ls.setItem("refresh_token", "y")
  ls.setItem("session_id", "z")
  clearSession()
  assert.equal(ls.getItem("access_token"), null)
  assert.equal(ls.getItem("refresh_token"), null)
  assert.equal(ls.getItem("session_id"), null)
})

test("expireSession 清空会话并跳回登录页，带当前路径 redirect", () => {
  const ls = globalThis.localStorage
  ls.setItem("access_token", "x")
  ls.setItem("session_id", "z")
  expireSession()
  assert.equal(ls.getItem("access_token"), null)
  assert.equal(assigned, `/login?redirect=${encodeURIComponent("/admin")}`)
})

test("已在登录页时 expireSession 不拼 redirect，避免跳转循环", () => {
  assigned = null
  ;(globalThis as Record<string, unknown>).window = {
    location: {
      pathname: "/login",
      search: "?redirect=/admin",
      assign: (target: string) => (assigned = target),
    },
  }
  expireSession()
  assert.equal(assigned, "/login")
})
