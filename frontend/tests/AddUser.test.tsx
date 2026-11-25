import assert from "node:assert/strict"
import { after, afterEach, mock, test } from "node:test"
import "./helpers/dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, render, within } from "@testing-library/react"
import { closeJSDom } from "./helpers/dom"

const bodies: unknown[] = []
let createUserImpl: (data: unknown) => Promise<unknown> = async () => ({
  ok: true,
})
const toasts: Array<[string, string]> = []
const queryClient = new QueryClient()
mock.module("@/client", {
  namedExports: {
    Users: {
      createUser: async ({ body }: { body: unknown }) => {
        bodies.push(body)
        return { data: await createUserImpl(body) }
      },
    },
  },
})
mock.module("@/lib/toast", {
  namedExports: {
    toastSuccess: (msg: string) => toasts.push(["success", msg]),
    toastError: () => {},
    toastErrorMessage: () => {},
  },
})
const { default: AddUser } = await import("@/components/Admin/AddUser.tsx")
afterEach(() => {
  cleanup()
  document.body.innerHTML = ""
  bodies.length = 0
  toasts.length = 0
  queryClient.clear()
  queryClient.cancelQueries()
})
after(() => {
  closeJSDom()
  queryClient.clear()
})
function renderWithProvider() {
  return render(
    <QueryClientProvider client={queryClient}>
      <AddUser />
    </QueryClientProvider>,
  )
}
function dialog() {
  return within(document.body)
}
async function waitForText(re: RegExp) {
  for (let i = 0; i < 20; i++) {
    const m = dialog()
      .queryAllByText(re)
      .find((e) => re.test(e.textContent ?? ""))
    if (m) return m
    await new Promise((r) => setTimeout(r, 10))
  }
  throw new Error("timeout")
}
async function open(container: HTMLElement) {
  await fireEvent.click(
    within(container).getByRole("button", { name: /新增用户/ }),
  )
  await new Promise((x) => setTimeout(x, 20))
  const f = document.body.querySelector("form")
  if (f) f.noValidate = true
}
test("c1", async () => {
  const r = renderWithProvider()
  await open(r.container)
  await fireEvent.click(dialog().getByRole("button", { name: /创建账号/ }))
  assert.match(
    (await waitForText(/请输入密码/)).textContent ?? "",
    /请输入密码/,
  )
})
test("c2", async () => {
  const r = renderWithProvider()
  await open(r.container)
  const view = dialog()
  await fireEvent.change(view.getByPlaceholderText("请输入邮箱"), {
    target: { value: "demo@example.com" },
  })
  await fireEvent.change(view.getByPlaceholderText("至少 8 个字符"), {
    target: { value: "password123" },
  })
  await fireEvent.change(view.getByPlaceholderText("请再次输入密码"), {
    target: { value: "different1" },
  })
  await fireEvent.click(view.getByRole("button", { name: /创建账号/ }))
  await new Promise((x) => setTimeout(x, 30))
})

test("c3", async () => {
  createUserImpl = async () => ({ id: 1, email: "demo@example.com" })
  const r = renderWithProvider()
  await open(r.container)
  const view = dialog()
  await fireEvent.change(view.getByPlaceholderText("请输入邮箱"), {
    target: { value: "demo@example.com" },
  })
  await fireEvent.change(view.getByPlaceholderText("至少 8 个字符"), {
    target: { value: "password123" },
  })
  await fireEvent.change(view.getByPlaceholderText("请再次输入密码"), {
    target: { value: "password123" },
  })
  await fireEvent.click(view.getByRole("button", { name: /创建账号/ }))
  await new Promise((x) => setTimeout(x, 20))
  assert.equal(bodies.length, 1)
  const body = bodies[0] as Record<string, unknown>
  assert.equal(body.email, "demo@example.com")
  assert.equal(body.password, "password123")
  assert.equal("confirm_password" in body, false)
  assert.deepEqual(
    toasts.find(([kind]) => kind === "success"),
    ["success", "用户创建成功"],
  )
})
