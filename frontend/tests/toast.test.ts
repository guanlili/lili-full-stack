import assert from "node:assert/strict"
import { test } from "node:test"

import { bindToast, toastError, toastSuccess } from "../src/lib/toast"

type Call = [string, string, string | undefined]

function fakeSonner() {
  const calls: Call[] = []
  const record =
    (kind: string) => (title: string, options?: { description?: string }) => {
      calls.push([kind, title, options?.description])
    }
  return {
    calls,
    module: {
      toast: { success: record("success"), error: record("error") },
    } as unknown as Parameters<typeof bindToast>[0],
  }
}

test("toast 队列兜底：挂载前排队不丢，bind 后即时派发且幂等", () => {
  const first = fakeSonner()

  // Toaster 挂载前发起的 toast 排队等待
  toastSuccess("排队一")
  toastError("排队二")
  assert.deepEqual(first.calls, [])

  // bind 后按发起顺序冲排
  bindToast(first.module)
  assert.deepEqual(first.calls, [
    ["success", "操作成功", "排队一"],
    ["error", "操作失败", "排队二"],
  ])

  // bind 之后即时派发，不再排队
  toastSuccess("即时")
  assert.deepEqual(first.calls.at(-1), ["success", "操作成功", "即时"])

  // 重复 bind 幂等：不切换到新模块
  const second = fakeSonner()
  bindToast(second.module)
  toastError("仍走第一个")
  assert.deepEqual(second.calls, [])
  assert.deepEqual(first.calls.at(-1), ["error", "操作失败", "仍走第一个"])
})
