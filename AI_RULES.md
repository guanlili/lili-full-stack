# AI Development Guidelines & Coding Standards

本文件只维护编码、安全、权限和部署规则。具体技术版本以 `backend/pyproject.toml`、`frontend/package.json` 和 `.python-version` 为准。

## 技术边界

- 后端：FastAPI + SQLModel + PostgreSQL，使用 uv、Ruff 和 ty。
- 前端：React + Vite + TypeScript，使用 TanStack Query/Router、TailwindCSS、Radix UI 和 Biome。
- 数据库变更使用 Alembic；前端 API 客户端由 OpenAPI 自动生成。

## 编码规范

### 通用

- Python 使用 `snake_case`，类使用 `PascalCase`。
- TypeScript 变量和函数使用 `camelCase`，组件和类型使用 `PascalCase`。
- 复杂逻辑写简洁注释，不要注释显而易见的代码。
- 保持组件小而专一；优先一文件一个组件。

### 后端

- 所有函数使用类型标注；API 请求和响应使用 Pydantic/SQLModel 模型。
- 路由和数据库操作默认使用同步 `def` 与同步 SQLModel `Session`，不要混用异步数据库会话。
- readiness probe 可以使用专用异步 psycopg 连接，以支持完整网络操作取消。
- 使用 `HTTPException` 返回 API 错误，不返回原始错误字典。
- 使用 `logging`，生产代码禁止 `print()`。
- 在 API 边界校验输入。

### 前端

- 使用函数组件和 Hooks。
- TypeScript 禁止 `any`，为数据和组件定义明确类型。
- 使用 Tailwind 工具类；只有动态值才使用 inline style。
- API 请求通过封装 `useQuery`/`useMutation` 的 hooks 完成。
- 尽量使用 `@/` 绝对导入。
- 禁止直接操作 DOM，除非确实需要并通过 ref 完成。

## 权限和错误语义

- 401 仅用于 Token 无效或过期；前端收到 401 会自动登出并清理缓存。
- 403 用于已登录但权限不足；不得用 401 表示普通权限不足。

## 前后端联动

- 修改 API 请求/响应契约后，运行 `cd frontend && npm run generate-client`。
- 前端不得手写 API URL，也不得手动修改 `frontend/src/client/` 中的生成文件。
- 修改数据库模型或字段后必须生成并检查 Alembic 迁移，不得直接改数据库。
- CI 会校验 `frontend/src/client/` 与后端 OpenAPI 是否一致。
- 后端测试使用独立测试库 `app_test`，禁止连接开发库或生产库。

## 部署规则

- `compose.yml` 用于生产，`compose.override.yml` 用于本地开发。
- 不提交 `.env`、Token、密码、私钥或其他密钥。
- 生产 `.env` 由 GitHub Secrets 生成，GitHub Secrets 是生产配置的唯一来源。
- `master` 只有通过 CI（lint、测试、构建和客户端一致性）后才能部署。
- 正式面向公网的项目必须使用 HTTPS；内网工具可使用模板默认的 HTTP 方案。
- 完整的 Secrets、HTTPS、备份和回滚流程见 [docs/deployment.md](docs/deployment.md)。

## 禁止模式

- 禁止循环导入。
- 禁止 magic numbers，使用命名常量。
- 禁止为只改业务逻辑的需求创建无意义迁移。
