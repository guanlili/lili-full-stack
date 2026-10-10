import axios from "axios"
import { LoginService, OpenAPI, type Token } from "@/client"
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
  clearSession()
  window.location.assign("/login")
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
  OpenAPI.BASE = import.meta.env.VITE_API_URL
  OpenAPI.TOKEN = async () => localStorage.getItem("access_token") || ""
  return installSessionRefresh(axios, {
    version: () => localStorage.getItem("session_id"),
    accessToken: () => localStorage.getItem("access_token"),
    refreshToken: () => localStorage.getItem("refresh_token"),
    refresh: (token) =>
      LoginService.refreshAccessToken({
        requestBody: { refresh_token: token },
      }),
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
