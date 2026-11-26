import assert from "node:assert/strict"
import { after, afterEach, test } from "node:test"
import { Users } from "lucide-react"
import "./helpers/dom"
import { cleanup, render, within } from "@testing-library/react"
import { closeJSDom } from "./helpers/dom"

const { EmptyState, EmptyStateAction } = await import(
  "@/components/patterns/empty-state"
)
const { PageContainer } = await import("@/components/patterns/page-container")
const { PageHeader } = await import("@/components/patterns/page-header")
const { StatCard, StatCardGrid } = await import(
  "@/components/patterns/stat-card"
)
const { TableSkeleton } = await import("@/components/patterns/table-skeleton")

afterEach(() => {
  cleanup()
  document.body.innerHTML = ""
})
after(() => {
  closeJSDom()
})

// ---------- EmptyState ----------

test("EmptyState 仅传 title：渲染主文案，不出现副文案与 CTA", () => {
  const r = render(<EmptyState title="暂无数据" />)
  const view = within(r.container)
  assert.ok(view.getByText("暂无数据"))
  assert.equal(view.queryByText("没有更多内容"), null)
  assert.equal(view.queryByRole("button"), null)
})

test("EmptyState 传 description 与 action：副文案与操作按钮均渲染", () => {
  const r = render(
    <EmptyState
      title="搜索无结果"
      description="换个关键词试试"
      action={<EmptyStateAction>重新加载</EmptyStateAction>}
    />,
  )
  const view = within(r.container)
  assert.ok(view.getByText("搜索无结果"))
  assert.ok(view.getByText("换个关键词试试"))
  assert.ok(view.getByRole("button", { name: "重新加载" }))
})

// ---------- PageContainer ----------

test("PageContainer 渲染 children 并合并 className", () => {
  const r = render(
    <PageContainer className="custom-gap">
      <span>页内内容</span>
    </PageContainer>,
  )
  const view = within(r.container)
  assert.ok(view.getByText("页内内容"))
  const div = r.container.querySelector("div")
  assert.match(div?.className ?? "", /max-w-7xl/)
  assert.match(div?.className ?? "", /custom-gap/)
})

// ---------- PageHeader ----------

test("PageHeader 仅 title：h1 出现，眉标/副标题/操作区均不渲染", () => {
  const r = render(<PageHeader title="用户管理" />)
  const view = within(r.container)
  assert.ok(view.getByRole("heading", { level: 1, name: "用户管理" }))
  assert.equal(view.queryByText("系统 / 用户"), null)
  assert.equal(view.queryByText("在这里维护账号"), null)
})

test("PageHeader 全量字段：眉标、副标题、右侧操作区均渲染", () => {
  const r = render(
    <PageHeader
      eyebrow="系统 / 用户"
      title="用户管理"
      description="在这里维护账号与角色"
      actions={<button type="button">新增</button>}
    />,
  )
  const view = within(r.container)
  assert.ok(view.getByText("系统 / 用户"))
  assert.ok(view.getByText("在这里维护账号与角色"))
  assert.ok(view.getByRole("button", { name: "新增" }))
})

// ---------- StatCard ----------

test("StatCard 渲染 label 与 value，无趋势时不展示徽章", () => {
  const r = render(<StatCard label="总用户数" value="128" />)
  const view = within(r.container)
  assert.ok(view.getByText("总用户数"))
  assert.ok(view.getByText("128"))
  assert.equal(view.queryByText("+12.5%"), null)
})

test("StatCard 带 trend 与 trendLabel：展示趋势徽章；缺 trendLabel 时不展示", () => {
  const up = render(
    <StatCard label="访问量" value="3.2k" trend="up" trendLabel="+12.5%" />,
  )
  assert.ok(within(up.container).getByText("+12.5%"))
  cleanup()

  const noLabel = render(<StatCard label="访问量" value="3.2k" trend="down" />)
  assert.equal(within(noLabel.container).queryByText(/-/), null)
})

test("StatCard 渲染 description 与图标插槽", () => {
  const r = render(
    <StatCard label="订单" value="42" description="较上周持平" icon={Users} />,
  )
  const view = within(r.container)
  assert.ok(view.getByText("较上周持平"))
})

test("StatCardGrid columns=4 应用四列栅格类", () => {
  const r = render(
    <StatCardGrid columns={4}>
      <span>card</span>
    </StatCardGrid>,
  )
  const div = r.container.querySelector("div")
  assert.match(div?.className ?? "", /lg:grid-cols-4/)
})

// ---------- TableSkeleton ----------

test("TableSkeleton 默认 6 行且带表头", () => {
  const r = render(<TableSkeleton />)
  const view = within(r.container)
  assert.equal(view.queryAllByRole("row").length, 7) // 1 表头 + 6 数据行
})

test("TableSkeleton 自定义 rows 并关闭表头", () => {
  const r = render(<TableSkeleton rows={3} showHeader={false} />)
  const view = within(r.container)
  assert.equal(view.queryAllByRole("row").length, 3)
  assert.equal(view.queryByRole("columnheader"), null)
})
