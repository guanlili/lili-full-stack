# lili-full-stack

guanlili 的个人全栈项目模板。基于 [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) 精简定制，面向 AI 驱动的外包项目快速交付。

> **AI 助手请注意**：本仓库是模板仓库，不是具体项目。具体项目的业务背景请看该项目自己的 `CLAUDE.md`。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + SQLModel + PostgreSQL |
| 包管理 | uv（后端）/ npm（前端）|
| 认证 | JWT + 邮件找回密码 |
| 数据库迁移 | Alembic |
| 前端框架 | React 19 + TypeScript + Vite |
| 样式 | TailwindCSS v4 + Radix UI + Lucide React |
| 数据请求 | TanStack Query + TanStack Router |
| 代码规范 | Ruff + MyPy（后端）/ Biome（前端）|
| 容器 | Docker Compose（nginx 内置 /api 代理，无 Traefik）|
| CI/CD | GitHub Actions → server-side git pull + docker compose up |

---

## 开启新项目

### 第一步：基于本模板创建新仓库

在 GitHub 上点 **Use this template → Create a new repository**（不是 Fork）。

### 第二步：克隆并初始化

```bash
git clone git@github.com:guanlili/<新项目名>.git
cd <新项目名>
cp .env.example .env
```

编辑 `.env`，至少修改：
- `PROJECT_NAME` — 项目名
- `SECRET_KEY` — 随机字符串（生产必改）
- `POSTGRES_PASSWORD` — 数据库密码
- `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` — 管理员账号

### 第三步：更新项目文档

- `CLAUDE.md` — 写入该项目的业务背景、数据模型、特殊约定（AI 开发时会读这个）
- `AI_RULES.md` — 追加项目特定的技术规范（如有）
- `README.md` — 改为项目自己的说明

### 第四步：删除示例代码

模板自带一个 Items（条目）CRUD 示例，展示了标准开发模式，开发完后删除：

- `backend/app/api/routes/items.py`
- `backend/app/models.py` 中的 `Item` / `ItemCreate` / `ItemUpdate` / `ItemPublic` 模型
- `backend/app/crud.py` 中 Item 相关的函数
- `frontend/src/routes/_layout/items.tsx`
- 导航组件中 Items 的链接

### 第五步：首次启动

```bash
docker compose up --build
```

| 服务 | 本地地址 |
|------|----------|
| 前端 | http://localhost:5173 |
| 后端 API 文档 | http://localhost:8000/docs |
| 邮件测试（Mailcatcher） | http://localhost:1080 |

默认管理员账号见 `.env` 中的 `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`。

---

## 本地开发

```bash
# 启动所有服务（自动加载 compose.override.yml）
docker compose up --build

# 启用热更新（后端代码改动自动生效）
docker compose watch

# 停止
docker compose down
```

---

## 新功能开发流程

每个新功能模块（如订单、产品、报告）都遵循以下标准流程：

### 1. 后端

```
backend/app/models.py     ← 加数据模型（SQLModel 类）
backend/app/crud.py       ← 加增删改查函数
backend/app/api/routes/   ← 新建路由文件（参考 items.py）
backend/app/api/main.py   ← 注册新路由
```

### 2. 数据库迁移

```bash
docker compose exec backend alembic revision --autogenerate -m "add xxx table"
docker compose exec backend alembic upgrade head
```

### 3. 同步前端 API 客户端

后端接口有任何变动后必须执行：

```bash
cd frontend && npm run generate-client
```

`frontend/src/client/` 是自动生成的，**不要手动修改**。

### 4. 前端

```
frontend/src/routes/_layout/   ← 新建页面（参考 items.tsx）
frontend/src/hooks/            ← 封装 useQuery / useMutation
frontend/src/components/       ← 可复用组件
```

---

## Claude Code 自定义指令

项目内置了 4 个自定义斜杠命令，在 Claude Code 中可直接使用：

| 指令 | 用途 |
|------|------|
| `/project:new-feature <名称>` | 自动创建完整功能模块（后端 model + crud + route + 前端页面） |
| `/project:migration <描述>` | 生成并应用 Alembic 数据库迁移 |
| `/project:generate-client` | 重新生成前端 API 客户端 |
| `/project:upgrade-deps` | 升级所有依赖包（uv + bun）|

示例：

```
/project:new-feature order
```

Claude Code 会按标准流程自动创建订单模块的全部后端和前端代码。

---

## 生产部署

### 首次部署

**1. 配置 GitHub Secrets**

在新仓库 **Settings → Secrets → Actions** 添加：

| Secret | 说明 |
|--------|------|
| `SERVER_HOST` | 服务器 IP |
| `SERVER_USER` | SSH 用户名（通常 `root`）|
| `SERVER_SSH_KEY` | SSH 私钥 |
| `DEPLOY_PATH` | 服务器上的项目路径，如 `/mnt/datadisk0/项目名` |

**2. 更新 workflow 里的端口和地址**

`.github/workflows/deploy.yml` 中的 `.env` 创建步骤，修改：
- `APP_PORT` — 该项目占用的端口（避免与其他项目冲突）
- `FRONTEND_HOST` / `BACKEND_CORS_ORIGINS` — 换成对应的 IP:PORT 或域名

**3. 服务器上 clone 一次**

```bash
git clone git@github.com:guanlili/<项目名>.git /mnt/datadisk0/项目名
```

只需做一次。之后 push 到 `master` 即自动触发部署：拉代码 → 自动创建/更新 `.env` → 构建镜像 → 跑 Alembic 迁移 → 重启容器。

> `.env` 由 workflow 自动生成，无需手动 SSH 创建。如需覆盖某个值，直接 SSH 编辑服务器上的 `.env` 即可（workflow 不会覆盖已存在的文件，只修补 `SECRET_KEY` 等默认占位值）。

---

## 模板维护

本仓库是模板，会定期更新，现有项目不会受影响。

### 维护节奏

| 时机 | 操作 |
|------|------|
| 做项目时踩了坑 | 回来更新 `AI_RULES.md` 或 `CLAUDE.md` |
| 每季度 | 运行 `/project:upgrade-deps` 升级依赖 |
| 发现更好的开发模式 | 更新 `.claude/commands/` 中的指令 |

### 从模板同步改进到现有项目

模板和具体项目是独立仓库，没有 git 关联。需要手动同步时，把改进的文件（`CLAUDE.md`、`AI_RULES.md`、`compose.yml`、`.claude/commands/`）复制过去即可。

---

## 项目结构

```
lili-full-stack/
├── .claude/
│   └── commands/          # Claude Code 自定义斜杠命令
├── .env.example           # 环境变量模板（复制为 .env 使用）
├── .env                   # 实际配置（私有仓库，可直接提交）
├── AI_RULES.md            # AI 开发规范（技术约定）
├── CLAUDE.md              # 项目上下文（Claude Code 启动时自动读取）
├── compose.yml            # 生产 Docker Compose
├── compose.override.yml   # 本地开发覆盖配置
├── backend/
│   └── app/
│       ├── api/routes/    # FastAPI 路由
│       ├── core/          # 配置、认证、数据库
│       ├── alembic/       # 数据库迁移文件
│       ├── models.py      # SQLModel 数据模型
│       └── crud.py        # 数据库操作
└── frontend/
    └── src/
        ├── routes/        # 页面（_layout/ 下需要登录）
        ├── components/    # 组件
        ├── hooks/         # 自定义 hooks
        └── client/        # 自动生成的 API 客户端（勿手动修改）
```

---

## 与上游的主要区别

| 项目 | 上游 fastapi/full-stack-fastapi-template | 本模板 |
|------|------------------------------------------|--------|
| 反向代理 | Traefik（复杂 label 配置） | nginx proxy_pass（内置前端镜像） |
| CI/CD | staging + production 双套 | 单一 deploy.yml |
| Playwright e2e 测试 | 包含 | 已移除 |
| Copier 模板系统 | 包含 | 已移除 |
| AI 开发规范 | 无 | AI_RULES.md + CLAUDE.md + .claude/commands/ |
