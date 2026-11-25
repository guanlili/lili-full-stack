import { JSDOM } from "jsdom"

/**
 * 在 node:test + tsx 下为 RTL 装配一套 jsdom 全局环境。
 *
 * 现有纯函数测试走 node:test，不依赖 DOM；渲染类组件测试（RTL）需要浏览器全局。
 *
 * 注意两点：
 * 1. @testing-library/dom 的 `screen` 在模块导入时即读取 `document.body` 绑定查询函数，
 *    而被测模块通常先于测试体导入，`screen` 会拿到抛错的惰性代理。渲染测试请统一用
 *    `render()` 返回的 `container` + `within(container)` 查询，不要用 `screen`。
 * 2. Radix 的 `react-use-layout-effect` 在模块求值时根据 `globalThis.document` 是否存在
 *    决定导出真实 `useLayoutEffect` 还是空 hook；ES 模块在测试体之前就已求值。因此本文件
 *    在模块顶层（导入链最靠前）即完成 jsdom 装配，保证 Radix 模块读到的是真实 layout effect。
 */

const DOM_GLOBALS = [
  "window",
  "document",
  "navigator",
  "HTMLElement",
  "Node",
  "Element",
  "Event",
  "EventTarget",
  "KeyboardEvent",
  "MouseEvent",
  "FocusEvent",
  "PointerEvent",
  "InputEvent",
  "CompositionEvent",
  "CustomEvent",
  "NodeList",
  "NodeFilter",
  "DOMRect",
  "DOMTokenList",
  "MutationObserver",
  "ResizeObserver",
  "IntersectionObserver",
  "getComputedStyle",
] as const

function createJSDom() {
  const dom = new JSDOM("<!doctype html><html><body></body></html>", {
    url: "http://localhost/",
    pretendToBeVisual: true,
  })
  const { window } = dom

  // 事件类：jsdom 内部 dispatchEvent 用 `event instanceof window.Event` 校验；
  // 必须把同一套构造器挂到 globalThis，避免测试侧 `new Event(...)` 与 window 内 instanceof 判定分裂。
  // react-dom 还会在 window 上探测 `InputEvent`/`CompositionEvent` 是否存在，决定走原生 input
  // 事件还是 IE 旧兜底（旧兜底会调不存在的 attachEvent）；jsdom 未提供的类在这里补到 window 与 globalThis。
  const eventPolyfills: Record<string, unknown> = {
    PointerEvent: window.MouseEvent,
    InputEvent: window.Event,
    CompositionEvent: window.Event,
    NodeList: window.NodeList ?? class {},
    DOMRect: window.DOMRect ?? class {},
    DOMTokenList: window.DOMTokenList ?? class {},
    ResizeObserver: class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
    IntersectionObserver: class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  }

  // window 上的 window/document 等身份属性由 jsdom 自身持有，不可重定义；仅补缺失类。
  const SKIP_WINDOW_KEYS = new Set(["window", "document", "navigator"])
  for (const key of DOM_GLOBALS) {
    const value =
      (window as unknown as Record<string, unknown>)[key] ?? eventPolyfills[key]
    if (value === undefined) continue
    if (!SKIP_WINDOW_KEYS.has(key)) {
      Object.defineProperty(window, key, {
        value,
        configurable: true,
        writable: true,
      })
    }
    Object.defineProperty(globalThis, key, {
      value,
      configurable: true,
      writable: true,
    })
  }
  // 告知 React 处于 act 测试环境（否则状态更新报 "not configured to support act"）
  ;(globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true

  // react-dom 的 IE 旧事件兜底在探测不到原生 input 事件时，会调 Element.attachEvent；
  // jsdom 无此 API，补空实现避免走旧分支时报 "attachEvent is not a function"。
  const ElementCtor = window.Element as unknown as Record<string, unknown>
  if (ElementCtor?.prototype) {
    const proto = ElementCtor.prototype as Record<string, unknown>
    if (typeof proto.attachEvent !== "function") {
      proto.attachEvent = () => {}
      proto.detachEvent = () => {}
    }
  }

  // jsdom 在 pretendToBeVisual 下会持续调度 requestAnimationFrame 循环，使事件循环始终
  // 有活跃 timer、测试进程无法退出。这里把 rAF 降级为「下一宏任务触发一次」，取消常驻循环。
  const win = window as unknown as Record<string, unknown>
  const raf: typeof requestAnimationFrame = (cb) =>
    setTimeout(() => cb(Date.now()), 0) as unknown as number
  const caf: typeof cancelAnimationFrame = (id) => clearTimeout(id)
  win.requestAnimationFrame = raf
  win.cancelAnimationFrame = caf
  globalThis.requestAnimationFrame = raf
  globalThis.cancelAnimationFrame = caf

  return dom
}

// 模块顶层装配：先于同文件及后续被测模块求值，保证 Radix 判定 document 为真
let dom: JSDOM | null = createJSDom()

/** 初始化（或复用）jsdom 全局环境；渲染测试在导入被测组件前调用。 */
export function setupJSDom() {
  if (dom) {
    dom.window.document.body.innerHTML = ""
    return dom.window
  }
  dom = createJSDom()
  return dom.window
}

/** 清空渲染容器与 RTL 挂载点；在每个用例结束后调用。 */
export function cleanupJSDom() {
  if (dom) {
    dom.window.document.body.innerHTML = ""
  }
}

/** 关闭 jsdom 实例、释放其持有起来的定时器/句柄；测试文件全部用例结束后调用，避免进程挂起。 */
export function closeJSDom() {
  if (dom) {
    dom.window.close()
    dom = null
  }
}
