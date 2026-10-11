import assert from "node:assert/strict"
import test from "node:test"
import axios, { AxiosError } from "axios"
import { client } from "../src/client/client.gen"
import { Access, Login, Roles, Users } from "../src/client/sdk.gen"
import { installSessionRefresh } from "../src/lib/sessionRefresh"
import { handleError } from "../src/utils"

test("generated SDK serializes form, JSON, path and query parameters", async () => {
  const requests: Array<{ url?: string; data: unknown; auth: unknown }> = []
  const transport = axios.create({
    adapter: async (config) => {
      requests.push({
        url: config.url,
        data: config.data,
        auth: config.headers.Authorization,
      })
      return {
        data: { ok: true },
        status: 200,
        statusText: "OK",
        headers: {},
        config,
      }
    },
  })
  client.setConfig({
    axios: transport,
    baseURL: "https://example.test",
    auth: () => "test-token",
  })
  await Login.loginAccessToken({
    body: { username: "a+b@example.test", password: "test-only" },
    throwOnError: true,
  })
  await Users.readUsers({ query: { skip: 10, limit: 5 }, throwOnError: true })
  await Roles.updatePermissions({
    path: { role_id: "role-1" },
    body: { permissions: ["users.view"] },
    throwOnError: true,
  })
  assert.match(String(requests[0].data), /username=a%2Bb%40example.test/)
  assert.equal(
    requests[1].url,
    "https://example.test/api/v1/users/?skip=10&limit=5",
  )
  assert.equal(requests[1].auth, "Bearer test-token")
  assert.equal(
    requests[2].url,
    "https://example.test/api/v1/roles/role-1/permissions",
  )
  assert.deepEqual(JSON.parse(String(requests[2].data)), {
    permissions: ["users.view"],
  })
})

test("generated SDK preserves session refresh and rejects 403 with its error body", async () => {
  let token = "old"
  let rotations = 0
  let denied = false
  const transport = axios.create({
    adapter: async (config) => {
      const status = denied
        ? 403
        : config.headers.Authorization === "Bearer old"
          ? 401
          : 200
      const response = {
        data: status === 200 ? { permissions: [] } : { detail: "没有权限" },
        status,
        statusText: "test",
        headers: {},
        config,
      }
      if (status !== 200)
        throw new AxiosError(
          "denied",
          "ERR_BAD_REQUEST",
          config,
          undefined,
          response,
        )
      return response
    },
  })
  client.setConfig({ axios: transport, auth: () => token })
  const dispose = installSessionRefresh(transport, {
    version: () => "session",
    accessToken: () => token,
    refreshToken: () => "refresh",
    refresh: async () => {
      rotations++
      return { access_token: "new" }
    },
    save: (tokens) => {
      token = tokens.access_token
    },
    expire: () => assert.fail("must retain session"),
  })
  try {
    const response = await Access.readAccess({ throwOnError: true })
    assert.deepEqual(response.data, { permissions: [] })
    assert.equal(rotations, 1)
    denied = true
    await assert.rejects(
      Access.readAccess({ throwOnError: true }),
      (error: unknown) => {
        assert.ok(axios.isAxiosError(error))
        assert.equal(error.response?.status, 403)
        let message = ""
        handleError.call((value) => {
          message = value
        }, error)
        assert.equal(message, "没有权限")
        return true
      },
    )
    assert.equal(rotations, 1)
  } finally {
    dispose()
  }
})
