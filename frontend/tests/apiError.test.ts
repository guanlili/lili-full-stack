import assert from "node:assert/strict"
import { test } from "node:test"
import { AxiosError } from "axios"

import { describeApiError } from "../src/lib/apiError"

function axiosError(status: number, detail?: unknown) {
  const error = new AxiosError(
    `Request failed with status ${status}`,
    String(status),
    {},
    null,
    { status, data: detail ? { detail } : {}, statusText: "" },
  )
  return error as unknown as Error
}

test("401 映射为登录过期提示", () => {
  assert.equal(describeApiError(axiosError(401)), "登录已过期，请重新登录")
})

test("403 映射为无权限提示", () => {
  assert.equal(describeApiError(axiosError(403)), "没有权限执行此操作")
})

test("422 解析 Pydantic detail 为友好中文，字段名映射中文", () => {
  const detail = [
    { loc: ["body", "email"], msg: "field required", type: "missing" },
    {
      loc: ["body", "password"],
      msg: "ensure this value has at least 8 characters",
      type: "string_too_short",
    },
  ]
  const message = describeApiError(axiosError(422, detail))
  assert.match(message, /邮箱/)
  assert.match(message, /密码/)
  assert.match(message, /field required|ensure this value/)
})

test("422 多条错误截断为前三条并提示总数", () => {
  const detail = Array.from({ length: 5 }, (_, i) => ({
    loc: ["body", `field_${i}`],
    msg: "invalid",
    type: "value_error",
  }))
  const message = describeApiError(axiosError(422, detail))
  assert.match(message, /等 5 处问题/)
})

test("422 无 detail 时回退通用提示", () => {
  assert.equal(
    describeApiError(axiosError(422)),
    "提交的信息有误，请检查后重试",
  )
})

test("500 映射为服务异常提示", () => {
  assert.equal(describeApiError(axiosError(500)), "服务器开了小差，请稍后重试")
})

test("网络异常（非 Axios 错误）返回通用提示", () => {
  assert.equal(
    describeApiError(new Error("Network Error")),
    "网络异常，请检查连接后重试",
  )
})
