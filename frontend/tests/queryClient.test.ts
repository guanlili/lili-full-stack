import assert from "node:assert/strict"
import { mock, test } from "node:test"
import { AxiosError, CanceledError } from "axios"

const toasts: string[] = []
let expired = 0

mock.module("../src/lib/toast.ts", {
  namedExports: {
    toastErrorMessage: (message: string) => toasts.push(message),
  },
})
mock.module("../src/lib/session.ts", {
  namedExports: {
    expireSession: () => {
      expired += 1
    },
  },
})

const { handleQueryError } = await import("../src/lib/queryClient.ts")

function axiosError(status: number, detail?: unknown) {
  return new AxiosError(
    `Request failed with status ${status}`,
    String(status),
    {},
    null,
    { status, data: detail ? { detail } : {}, statusText: "" },
  ) as unknown as Error
}

test("401 触发登出并弹登录过期提示", () => {
  expired = 0
  toasts.length = 0
  handleQueryError(axiosError(401))
  assert.equal(expired, 1)
  assert.deepEqual(toasts, ["登录已过期，请重新登录"])
})

test("403 不登出，只弹无权限提示", () => {
  expired = 0
  toasts.length = 0
  handleQueryError(axiosError(403))
  assert.equal(expired, 0)
  assert.deepEqual(toasts, ["没有权限执行此操作"])
})

test("422 走字段级中文映射，不踢下线", () => {
  expired = 0
  toasts.length = 0
  handleQueryError(
    axiosError(422, [
      { loc: ["body", "email"], msg: "field required", type: "missing" },
    ]),
  )
  assert.equal(expired, 0)
  assert.ok(toasts[0].includes("邮箱"))
})

test("500 弹服务异常提示，不登出", () => {
  expired = 0
  toasts.length = 0
  handleQueryError(axiosError(500))
  assert.equal(expired, 0)
  assert.deepEqual(toasts, ["服务器开了小差，请稍后重试"])
})

test("取消的请求静默忽略，不弹提示", () => {
  expired = 0
  toasts.length = 0
  const canceled = new CanceledError("canceled")
  handleQueryError(canceled as unknown as Error)
  assert.equal(expired, 0)
  assert.deepEqual(toasts, [])
})
