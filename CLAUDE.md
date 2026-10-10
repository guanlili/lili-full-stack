# CLAUDE.md — 模板开发规范

> 本文件维护模板级的项目结构和开发流程。客户项目的业务背景、数据模型、角色权限、第三方服务和特殊约定请写入 `PROJECT_CONTEXT.md`，不要直接把客户信息固化到本文件。

## 项目上下文

开始业务开发前，先阅读根目录的 `PROJECT_CONTEXT.md`（如果存在）。其中的内容只描述当前客户项目，不应反过来改变模板级的安全、权限和数据隔离要求。

新项目初始化时，优先填写 `PROJECT_CONTEXT.md`；只有项目的技术流程本身发生变化时，才修改本文件。

## 项目结构

```
backend/app/
├── api/routes/     # FastAPI 路由（每个业务模块一个文件）
├── core/           # 配置、安全、数据库连接
├── models.py       # SQLModel 数据模型（数据库表结构）
├── crud.py         # 数据库增删改查操作
└── main.py         # 应用入口

frontend/src/
├── routes/         # TanStack Router 页面（_layout/ 下是需要登录的页面）
├── components/     # 可复用组件
├── hooks/          # 自定义 hooks（封装 useQuery/useMutation）
└── client/         # 自动生成的 API 客户端（不要手动修改）
```

## 本地开发

```bash
docker compose up --build   # 首次启动
docker compose watch        # 启用热更新（后端 --reload，前端 vite HMR）
docker compose down         # 停止
```

| 服务 | 地址 |
|------|------|
| 前端（vite dev server） | http://localhost:5173 |
| API 文档 | http://localhost:8000/docs |
| 邮件测试 | http://localhost:1080 |

查看数据库：`docker compose exec db psql -U postgres -d app`

运行后端测试（需要数据库在运行；测试自动创建并使用独立测试库 `app_test`，不碰开发库 `app`）：

```bash
cd backend
uv run bash scripts/tests-start.sh
```

测试库指向应用库时（`POSTGRES_DB_TEST` 与 `POSTGRES_DB` 相同），测试会在任何建表或删数据操作之前直接拒绝运行。

## 开发新功能的标准流程

根据变更类型执行必要步骤，不要为无关变更创建空迁移：

1. **数据库变化**：修改 `models.py`，补充 CRUD、路由和测试。
2. **数据库迁移**：运行 `docker compose exec backend alembic revision --autogenerate -m "add xxx"`，检查迁移内容后再 `alembic upgrade head`。
3. **API 契约变化**：后端接口稳定后运行 `cd frontend && npm run generate-client`。
4. **前端页面**：在 `routes/_layout/` 添加页面，在 `frontend/src/components/Sidebar/AppSidebar.tsx` 的导航项中按需添加链接。
5. **仅业务逻辑变化**：补充或更新后端 API/CRUD 测试；不需要生成迁移时不要生成迁移。

后端改动模型或接口后，必须确认前端生成客户端和相关测试已同步。生成文件不得手动编辑。

## 验证与交付

后端：

```bash
cd backend
uv run bash scripts/lint.sh
uv run bash scripts/tests-start.sh
```

前端：

```bash
cd frontend
npm run lint
npm test
npm run build
```

需要自动修复格式时使用 `npm run lint:fix`；`npm run lint` 只检查，不修改工作区。

交付前还要检查：

- 数据库迁移只包含本次需求的变化。
- `frontend/src/client/` 与后端 OpenAPI 契约一致。
- 401/403 语义、角色权限和未登录行为有对应测试或手工验证。
- 模板不预置业务 CRUD 示例；交付前确认没有临时调试代码和测试数据。
- 交付前运行 `bash scripts/check-template.sh`，确认模板文件、脚本语法和 Compose 配置完整。

## 模块开发说明

模板默认只提供认证与会话、密码找回、可配置角色与页面权限、用户管理、个人设置和内部审计。文件、通用配置、导入导出和后台任务按具体项目需求添加；历史扩展表仅保留用于升级兼容，不自动删除数据。业务模块交付统一遵循 [docs/module-development.md](docs/module-development.md)。新业务模块应根据 `PROJECT_CONTEXT.md` 从数据模型、API、测试、生成客户端和页面导航开始实现。

## 技术规范

详见 `AI_RULES.md`。客户项目的业务约定详见 `PROJECT_CONTEXT.md`。
