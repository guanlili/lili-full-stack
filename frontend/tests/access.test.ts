import assert from "node:assert/strict"
import test from "node:test"
import { canAccessPath } from "../src/lib/access.ts"

test("page access denies missing, unregistered and forbidden routes", () => {
  const pages = [
    { path: "/", allowed: true },
    { path: "/admin", allowed: false },
  ]
  assert.equal(canAccessPath(undefined, "/"), false)
  assert.equal(canAccessPath(pages, "/admin"), false)
  assert.equal(canAccessPath(pages, "/new-page"), false)
  assert.equal(canAccessPath(pages, "/admin/users"), false)
  assert.equal(canAccessPath(pages, "/"), true)
})

test("registered pages require an explicit grant and normalize trailing slash", () => {
  assert.equal(
    canAccessPath([{ path: "/admin", allowed: true }], "/admin/"),
    true,
  )
  assert.equal(
    canAccessPath([{ path: "/admin", allowed: true }], "/admin-other"),
    false,
  )
})
