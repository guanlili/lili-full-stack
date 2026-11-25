import assert from "node:assert/strict"
import { mock, test } from "node:test"

const captured: unknown[] = []

mock.module("@sentry/react", {
  namedExports: {
    captureException: (error: unknown) => captured.push(error),
  },
})

const { reportError } = await import("../src/lib/reportError.ts")

test("未传 DSN 时零上报：不加载 SDK、不记录异常", () => {
  captured.length = 0
  reportError(new Error("should not report"), "")
  assert.equal(captured.length, 0)
})

test("传入 DSN 时懒加载 SDK 并上报异常", async () => {
  captured.length = 0
  const boom = new Error("boom")
  reportError(boom, "https://example@glitchtip.example.com/1")
  // SDK 异步加载，等待微任务/宏任务排空后再断言
  await new Promise((resolve) => setTimeout(resolve, 20))
  assert.equal(captured.length, 1)
  assert.equal(captured[0], boom)
})
