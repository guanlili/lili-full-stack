import { AxiosError } from "axios"
import type { ApiError } from "./client"

const ERROR_MESSAGE_TRANSLATIONS: Record<string, string> = {
  "Could not validate credentials": "登录凭证无效",
  "Incorrect email or password": "邮箱或密码错误",
  "Incorrect password": "密码错误",
  "Inactive user": "账号未启用",
  "User not found": "用户不存在",
  "The user doesn't have enough privileges": "你没有执行此操作的权限",
  "The user with this id does not exist in the system": "用户不存在",
  "The user with this email already exists in the system.": "该邮箱已注册",
  "User with this email already exists": "该邮箱已注册",
  "Open user registration is forbidden on this server":
    "当前服务器未开放用户注册",
  "Super users are not allowed to delete themselves":
    "超级管理员不能删除自己的账号",
  "New password cannot be the same as the current one":
    "新密码不能与当前密码相同",
  "Password updated successfully": "密码修改成功",
  "User updated successfully": "用户信息更新成功",
  "User deleted successfully": "用户删除成功",
  "Invalid token": "链接无效或已过期",
}

function translateErrorMessage(message: string): string {
  return ERROR_MESSAGE_TRANSLATIONS[message] ?? message
}

function extractErrorMessage(err: ApiError): string {
  if (err instanceof AxiosError) {
    return "网络请求失败，请检查网络后重试。"
  }

  // FastAPI 的错误体：HTTPException 是 string，422 校验错误是 {msg} 数组
  const body = err.body as
    | { detail?: string | Array<{ msg: string }> }
    | undefined
  const errDetail = body?.detail
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    return translateErrorMessage(errDetail[0].msg)
  }
  return typeof errDetail === "string"
    ? translateErrorMessage(errDetail)
    : "操作失败，请稍后重试。"
}

export const handleError = function (
  this: (msg: string) => void,
  err: ApiError,
) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
