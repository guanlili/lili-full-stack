import axios from "axios"
import { Login as LoginService, type Token } from "@/client"
import { client } from "@/client/client.gen"
import { installSessionRefresh } from "./sessionRefresh"

export function clearSession() {
  localStorage.removeItem("session_id")
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")
}

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
    throwOnError: true,
  })
  return installSessionRefresh(axios, {
    version: () => localStorage.getItem("session_id"),
    accessToken: () => localStorage.getItem("access_token"),
    refreshToken: () => localStorage.getItem("refresh_token"),
    refresh: (token) =>
      LoginService.refreshAccessToken({
        body: { refresh_token: token },
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
