import assert from "node:assert/strict"
import { test } from "node:test"
import axios, { type AxiosAdapter, AxiosError, AxiosHeaders } from "axios"
import { installSessionRefresh } from "../src/lib/sessionRefresh.ts"

function fixture(
  options: { refreshFails?: number; retryFails?: boolean } = {},
) {
  let access = "old-access"
  let refresh: string | null = "old-refresh"
  let version = 0
  let refreshCount = 0
  let expired = 0
  const adapter: AxiosAdapter = async (config) => {
    const refreshing = config.data?.includes?.("refresh_token")
    const status = refreshing
      ? (options.refreshFails ?? 200)
      : config.headers.Authorization === "Bearer old-access" ||
          options.retryFails
        ? 401
        : 200
    const response = {
      config,
      status,
      statusText: String(status),
      headers: new AxiosHeaders(),
      data: refreshing
        ? { access_token: "new-access", refresh_token: "new-refresh" }
        : "ok",
    }
    if (status >= 400) {
      throw new AxiosError(
        "Request failed",
        "ERR_BAD_RESPONSE",
        config,
        undefined,
        response,
      )
    }
    return response
  }
  const client = axios.create({ adapter })
  let release: (() => void) | undefined
  const gate = new Promise<void>((resolve) => {
    release = resolve
  })
  installSessionRefresh(client, {
    version: () => version,
    accessToken: () => access,
    refreshToken: () => refresh,
    refresh: async (token) => {
      refreshCount += 1
      await gate
      return (await client.post("/refresh", { refresh_token: token })).data
    },
    save: (tokens) => {
      access = tokens.access_token
      refresh = tokens.refresh_token ?? null
    },
    expire: () => {
      expired += 1
      version += 1
      access = ""
      refresh = null
    },
  })
  return {
    request: (token = "old-access", signal?: AbortSignal) =>
      client.get("/protected", {
        headers: { Authorization: `Bearer ${token}` },
        signal,
      }),
    release: () => release?.(),
    logout: () => {
      version += 1
      access = ""
      refresh = null
    },
    rotateInOtherTab: () => {
      access = "other-tab-access"
      refresh = "other-tab-refresh"
    },
    state: () => ({ access, refresh, refreshCount, expired }),
  }
}

async function waitForRefresh(f: ReturnType<typeof fixture>) {
  for (let i = 0; i < 100 && !f.state().refreshCount; i += 1) {
    await new Promise((resolve) => setTimeout(resolve, 1))
  }
  assert.equal(f.state().refreshCount, 1)
}

test("concurrent 401s share one rotation and replay; late 401 uses current token", async () => {
  const f = fixture()
  const requests = [f.request(), f.request(), f.request()]
  await waitForRefresh(f)
  f.release()
  assert.deepEqual(
    (await Promise.all(requests)).map((r) => r.data),
    ["ok", "ok", "ok"],
  )
  assert.equal((await f.request()).status, 200)
  assert.equal(f.state().refreshCount, 1)
})

test("invalid refresh clears session without recursively refreshing", async () => {
  const f = fixture({ refreshFails: 401 })
  const request = f.request()
  await waitForRefresh(f)
  f.release()
  await assert.rejects(request, (error) => axios.isCancel(error))
  assert.deepEqual(f.state(), {
    access: "",
    refresh: null,
    refreshCount: 1,
    expired: 1,
  })
})

test("server failure retains session for a later retry", async () => {
  const f = fixture({ refreshFails: 503 })
  const request = f.request()
  await waitForRefresh(f)
  f.release()
  await assert.rejects(request)
  assert.equal(f.state().access, "old-access")
  assert.equal(f.state().expired, 0)
})

test("logout during refresh cannot restore old credentials", async () => {
  const f = fixture()
  const request = f.request()
  await waitForRefresh(f)
  f.logout()
  f.release()
  await assert.rejects(request, (error) => axios.isCancel(error))
  assert.equal(f.state().access, "")
  assert.equal(f.state().refresh, null)
})

test("a replayed 401 expires the session without a refresh loop", async () => {
  const f = fixture({ retryFails: true })
  const request = f.request()
  await waitForRefresh(f)
  f.release()
  await assert.rejects(request, (error) => axios.isCancel(error))
  assert.equal(f.state().refreshCount, 1)
  assert.equal(f.state().expired, 1)
})

test("canceled requests are not replayed after refresh", async () => {
  const f = fixture()
  const controller = new AbortController()
  const request = f.request("old-access", controller.signal)
  await waitForRefresh(f)
  controller.abort()
  f.release()
  await assert.rejects(request, (error) => axios.isCancel(error))
  assert.equal(f.state().expired, 0)
})

test("two tabs sharing an exclusive lock rotate once", async () => {
  let access = "old-access"
  let refresh = "old-refresh"
  let rotations = 0
  let queue = Promise.resolve()
  const createTab = () => {
    const client = axios.create({
      adapter: async (config) => {
        const status =
          config.headers.Authorization === "Bearer old-access" ? 401 : 200
        const response = {
          config,
          status,
          statusText: String(status),
          headers: new AxiosHeaders(),
          data: "ok",
        }
        if (status === 401) {
          throw new AxiosError(
            "Unauthorized",
            "ERR_BAD_RESPONSE",
            config,
            undefined,
            response,
          )
        }
        return response
      },
    })
    installSessionRefresh(client, {
      version: () => "shared-session",
      accessToken: () => access,
      refreshToken: () => refresh,
      refresh: async (token) => {
        assert.equal(token, "old-refresh")
        rotations += 1
        await new Promise((resolve) => setTimeout(resolve, 5))
        return { access_token: "new-access", refresh_token: "new-refresh" }
      },
      save: (tokens) => {
        access = tokens.access_token
        refresh = tokens.refresh_token ?? ""
      },
      expire: () =>
        assert.fail("A successful cross-tab refresh must not log out"),
      exclusive: (operation) => {
        const next = queue.then(operation)
        queue = next.catch(() => {})
        return next
      },
    })
    return client.get("/protected", {
      headers: { Authorization: "Bearer old-access" },
    })
  }
  const results = await Promise.all([createTab(), createTab()])
  assert.equal(rotations, 1)
  assert.deepEqual(
    results.map((r) => r.status),
    [200, 200],
  )
})

test("without Web Locks, a losing refresh cannot clear another tab's new tokens", async () => {
  const f = fixture({ refreshFails: 401 })
  const request = f.request()
  await waitForRefresh(f)
  f.rotateInOtherTab()
  f.release()
  await assert.rejects(request, (error) => axios.isCancel(error))
  assert.deepEqual(f.state(), {
    access: "other-tab-access",
    refresh: "other-tab-refresh",
    refreshCount: 1,
    expired: 0,
  })
})
