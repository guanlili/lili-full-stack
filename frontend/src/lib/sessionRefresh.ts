import { AxiosError, type AxiosInstance, CanceledError } from "axios"

declare module "axios" {
  interface AxiosRequestConfig {
    sessionVersion?: string | number | null
    sessionRefresh?: boolean
    sessionRetried?: boolean
  }
}

type Tokens = { access_token: string; refresh_token?: string | null }

type SessionCallbacks = {
  version: () => string | number | null
  accessToken: () => string | null
  refreshToken: () => string | null
  refresh: (token: string) => Promise<Tokens>
  save: (tokens: Tokens) => void
  expire: () => void
  exclusive?: (operation: () => Promise<void>) => Promise<void>
}

// The generated SDK uses this Axios instance. Keep transport customizations here,
// outside generated files, so regenerating the client preserves session behavior.
export function installSessionRefresh(
  client: AxiosInstance,
  session: SessionCallbacks,
) {
  let pending: Promise<void> | null = null
  let pendingVersion: string | number | null = null
  const requestId = client.interceptors.request.use((config) => {
    config.sessionVersion ??= session.version()
    config.sessionRefresh =
      typeof config.data === "object" &&
      config.data !== null &&
      "refresh_token" in config.data
    return config
  })
  const responseId = client.interceptors.response.use(
    undefined,
    async (error) => {
      if (!(error instanceof AxiosError) || error.response?.status !== 401) {
        throw error
      }
      const config = error.config
      if (!config || config.sessionRefresh || !config.headers.Authorization) {
        throw error
      }
      const version = config.sessionVersion
      if (version !== session.version()) {
        throw new CanceledError("Session changed")
      }
      if (config.sessionRetried) {
        session.expire()
        throw new CanceledError("Session expired")
      }
      const refreshToken = session.refreshToken()
      if (!refreshToken) {
        session.expire()
        throw new CanceledError("Session expired")
      }
      config.sessionRetried = true
      // A late 401 from a request sent before an already-completed refresh should
      // replay with the current token without rotating again.
      if (config.headers.Authorization === `Bearer ${session.accessToken()}`) {
        if (!pending || pendingVersion !== version) {
          pendingVersion = version ?? null
          const rotate = async () => {
            try {
              if (version !== session.version()) {
                throw new CanceledError("Session changed")
              }
              // Another tab may have rotated while this one waited for the lock.
              if (session.refreshToken() !== refreshToken) return
              const tokens = await session.refresh(refreshToken)
              if (
                version !== session.version() ||
                session.refreshToken() !== refreshToken
              ) {
                throw new CanceledError("Session changed")
              }
              session.save(tokens)
            } catch (refreshError) {
              if (version !== session.version()) {
                throw new CanceledError("Session changed")
              }
              // A network/server failure is retryable; only invalid credentials
              // should destroy a session. SDK ApiError also exposes status.
              const status =
                refreshError instanceof AxiosError
                  ? refreshError.response?.status
                  : (refreshError as { status?: number }).status
              if (status === 401) {
                session.expire()
                throw new CanceledError("Session expired")
              }
              throw refreshError
            }
          }
          const operation = session.exclusive
            ? session.exclusive(rotate)
            : rotate()
          pending = operation
          void operation
            .finally(() => {
              if (pending === operation) pending = null
            })
            .catch(() => {})
        }
        await pending
      }
      if (version !== session.version() || config.signal?.aborted) {
        throw new CanceledError("Request canceled")
      }
      config.headers.Authorization = `Bearer ${session.accessToken()}`
      return client.request(config)
    },
  )
  return () => {
    client.interceptors.request.eject(requestId)
    client.interceptors.response.eject(responseId)
  }
}
