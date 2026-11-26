import assert from "node:assert/strict"
import { after, afterEach, test } from "node:test"
import "./helpers/dom"
import { cleanup, render, waitFor } from "@testing-library/react"
import { closeJSDom } from "./helpers/dom"

// jsdom 不提供 matchMedia，这里按 useIsMobile 的用法补一套可触发回调的桩。
let changeListeners: Array<() => void> = []
let viewportWidth = 1024

const matchMediaStub = (query: string) => ({
  matches: viewportWidth < 768,
  media: query,
  onchange: null,
  addEventListener: (_event: string, cb: () => void) => {
    changeListeners.push(cb)
  },
  removeEventListener: (_event: string, cb: () => void) => {
    changeListeners = changeListeners.filter((l) => l !== cb)
  },
  addListener: () => {},
  removeListener: () => {},
  dispatchEvent: () => true,
})

Object.defineProperty(window, "matchMedia", {
  value: matchMediaStub,
  configurable: true,
  writable: true,
})
Object.defineProperty(window, "innerWidth", {
  get: () => viewportWidth,
  configurable: true,
})

const { useIsMobile } = await import("@/hooks/useMobile")

let mobileResult: boolean | undefined
function Probe() {
  mobileResult = useIsMobile()
  return null
}

afterEach(() => {
  cleanup()
  document.body.innerHTML = ""
  changeListeners = []
  mobileResult = undefined
  viewportWidth = 1024
})
after(() => {
  closeJSDom()
})

test("宽屏初始判定为非移动端", async () => {
  viewportWidth = 1024
  render(<Probe />)
  await waitFor(() => assert.equal(mobileResult, false))
})

test("窄屏初始判定为移动端", async () => {
  viewportWidth = 375
  render(<Probe />)
  await waitFor(() => assert.equal(mobileResult, true))
})

test("视口由宽变窄时监听回调更新判定", async () => {
  viewportWidth = 1024
  render(<Probe />)
  await waitFor(() => assert.equal(mobileResult, false))

  viewportWidth = 360
  for (const cb of changeListeners) cb()
  await waitFor(() => assert.equal(mobileResult, true))
})
