import assert from "node:assert/strict"
import { test } from "node:test"
import { AxiosError } from "axios"

import { extractErrorMessage, getInitials, handleError } from "../src/utils"

function axiosError(status: number, detail?: unknown) {
  const error = new AxiosError(
    `Request failed with status ${status}`,
    String(status),
    {},
    null,
    { status, data: detail ? { detail } : {}, statusText: "" },
  )
  return error
}

test("非 AxiosError / 无响应体回退网络异常提示", () => {
  assert.equal(
    extractErrorMessage(new Error("boom")),
    "网络请求失败，请检查网络后重试。",
  )
  assert.equal(extractErrorMessage(null), "网络请求失败，请检查网络后重试。")
})

test("string 型 detail 命中中英文案翻译", () => {
  const err = axiosError(400, "Incorrect email or password")
  assert.equal(extractErrorMessage(err), "邮箱或密码错误")
})

test("422 detail 数组取首条 msg 并翻译", () => {
  const err = axiosError(422, [
    { msg: "field required", type: "missing" },
    { msg: "Incorrect password", type: "value_error" },
  ])
  // 首条 msg 无翻译表命中，原样透出；第二条不参与取值
  assert.equal(extractErrorMessage(err), "field required")
})

test("未命中翻译表的英文 detail 原样返回", () => {
  const err = axiosError(500, "some unknown backend message")
  assert.equal(extractErrorMessage(err), "some unknown backend message")
})

test("空 detail 回退通用操作失败提示", () => {
  const err = axiosError(500)
  assert.equal(extractErrorMessage(err), "操作失败，请稍后重试。")
})

test("handleError 以 this 回调下发翻译后文案", () => {
  let captured = ""
  const bound = handleError.bind((msg: string) => {
    captured = msg
  })
  bound(axiosError(400, "Incorrect email or password"))
  assert.equal(captured, "邮箱或密码错误")
})

test("getInitials 取前两个单词首字母并大写", () => {
  assert.equal(getInitials("Ada Lovelace"), "AL")
  assert.equal(getInitials("bob"), "B")
  assert.equal(getInitials("grace hopper"), "GH")
})
