/**
 * 业务模式组件（patterns）：由原子组件组合而成的高频页面区块样板。
 * 新写业务页面优先从这里组合，禁止手写裸标题、裸空态与裸骨架。
 */

export { EmptyState, EmptyStateAction } from "./empty-state"
export { PageContainer } from "./page-container"
export { PageHeader } from "./page-header"
export { StatCard, StatCardGrid } from "./stat-card"
export { TableSkeleton } from "./table-skeleton"
