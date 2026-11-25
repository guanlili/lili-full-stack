import axios from "axios"

/**
 * 后端校验错误条目（Pydantic 422 detail 数组元素），与生成类型保持结构一致。
 */
type ValidationErrorItem = {
  loc?: Array<string | number>
  msg?: string
  type?: string
}

/** 字段名中常见的英文 key 到中文的粗略映射；未命中时回退字段名本身。 */
const FIELD_LABELS: Record<string, string> = {
  email: "邮箱",
  password: "密码",
  full_name: "姓名",
  username: "用户名",
  name: "名称",
  role: "角色",
  status: "状态",
  search: "搜索关键词",
  page: "页码",
  page_size: "每页条数",
}

function formatField(loc: Array<string | number> | undefined): string {
  if (!loc || loc.length === 0) return ""
  // loc 形如 ["body", "email"]；去掉 body/query/path 这类请求位置前缀
  const parts = loc.filter(
    (segment) =>
      typeof segment === "string" &&
      !["body", "query", "path"].includes(segment),
  )
  const field = parts[parts.length - 1]
  if (typeof field !== "string") return ""
  return FIELD_LABELS[field] ?? field
}

/** 把 422 的 detail 数组收敛为一两条友好中文提示，避免原始英文校验数组透出。 */
function formatValidationDetail(detail: unknown): string {
  if (!Array.isArray(detail) || detail.length === 0) {
    return "提交的信息有误，请检查后重试"
  }
  const messages = detail
    .slice(0, 3)
    .map((item) => {
      const error = item as ValidationErrorItem
      const field = formatField(error.loc)
      const msg = error.msg?.trim()
      if (!msg) return ""
      return field ? `${field}：${msg}` : msg
    })
    .filter(Boolean)
  if (messages.length === 0) return "提交的信息有误，请检查后重试"
  const extra = detail.length - messages.length
  return extra > 0
    ? `${messages.join("；")} 等 ${detail.length} 处问题`
    : messages.join("；")
}

/**
 * 把后端 HTTP 错误收敛为人类可读的中文提示。
 * 非 Axios 错误（网络中断、取消等）返回通用提示。
 */
export function describeApiError(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return "网络异常，请检查连接后重试"
  }
  const status = error.response?.status
  const detail = (error.response?.data as { detail?: unknown } | undefined)
    ?.detail

  switch (status) {
    case 401:
      return "登录已过期，请重新登录"
    case 403:
      return "没有权限执行此操作"
    case 422:
      return formatValidationDetail(detail)
    case 500:
      return "服务器开了小差，请稍后重试"
    case 502:
    case 503:
    case 504:
      return "服务暂时不可用，请稍后重试"
    default:
      return "请求失败，请稍后重试"
  }
}
