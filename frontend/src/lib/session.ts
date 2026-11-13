import axios from "axios"
import { Login as LoginService, type Token } from "@/client"
import { client } from "@/client/client.gen"
import { installSessionRefresh } from "./sessionRefresh"

export function clearSession() {
  localStorage.removeItem("session_id")
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")
}

// refresh token 存 HttpOnly Cookie（后端下发，JS 不可读），本地只保留短命
// access token 与会话标记；storeTokens 兼容旧字段（refresh_token 恒为空）
function storeTokens(tokens: Token) {
  localStorage.setItem("access_token", tokens.access_token)
  if (tokens.refresh_token) {
    localStorage.setItem("refresh_token", tokens.refresh_token)
  } else {
    localStorage.removeItem("refresh_token")
  }
}

export function startSession(tokens: Token) {
  localStorage.setItem(
    "session_id",
    crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
  )
  storeTokens(tokens)
}

export function expireSession() {
  // 记住当前页面，登录后回来；已在 /login（含带参）时直接去登录页避免循环
  const current = window.location.pathname + window.location.search
  clearSession()
  const target = current.startsWith("/login")
    ? "/login"
    : `/login?redirect=${encodeURIComponent(current)}`
  window.location.assign(target)
}

export function configureSession() {
  if (
    localStorage.getItem("access_token") &&
    !localStorage.getItem("session_id")
  ) {
    localStorage.setItem(
      "session_id",
      crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
    )
  }
  client.setConfig({
    axios,
    baseURL: import.meta.env.VITE_API_URL,
    auth: () => localStorage.getItem("access_token") || "",
    // refresh token 在 HttpOnly Cookie 里，刷新请求需带凭据（同源/配置好的 CORS 域）
    withCredentials: true,
    throwOnError: true,
  })
  return installSessionRefresh(axios, {
    version: () => localStorage.getItem("session_id"),
    accessToken: () => localStorage.getItem("access_token"),
    // refresh token 已 HttpOnly 化（JS 不可读）：这里返回会话哨兵，仅表示
    // "本浏览器持有一个 refresh cookie"，供拦截器判断是否可刷新/是否已被轮换替换
    refreshToken: () =>
      localStorage.getItem("session_id") ? "refresh-cookie" : null,
    refresh: () =>
      LoginService.refreshAccessToken({
        throwOnError: true,
      }).then((response) => response.data),
    save: storeTokens,
    expire: expireSession,
    exclusive: async (operation) => {
      if (navigator.locks) {
        await navigator.locks.request("session-refresh", operation)
      } else {
        await operation()
      }
    },
  })
}
