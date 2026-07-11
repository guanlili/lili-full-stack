# lili-full-stack

guanlili 的个人全栈项目模板。基于 [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) 精简定制，去掉 Traefik / Copier / Playwright，面向 AI 驱动的外包项目快速交付。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLModel + PostgreSQL + Alembic |
| 包管理 | uv（后端）/ bun（前端） |
| 认证 | JWT + 邮件找回密码 |
| 前端 | React 19 + TypeScript + Vite + TailwindCSS v4 |
| UI | Radix UI + Lucide React |
| 数据请求 | TanStack Query + TanStack Router |
| 容器 | Docker Compose（nginx 内置 /api 代理，无 Traefik） |
| CI/CD | GitHub Actions → server-side git pull + docker compose up |

## 开始新项目

### 第一步：基于本模板创建新仓库

在 GitHub 上点 **Use this template → Create a new repository**，或直接 fork。

### 第二步：克隆到本地

```bash
git clone git@github.com:guanlili/<新项目名>.git
cd <新项目名>
```

### 第三步：修改项目配置

1. **`.env`** — 改 `PROJECT_NAME`、数据库密码、`SECRET_KEY`、`FIRST_SUPERUSER` 等
2. **`AI_RULES.md`** — 追加项目特定的业务规则和数据模型说明
3. **`backend/app/models.py`** — 删除示例 `Item` 模型，加自己的业务模型
4. **`backend/app/api/routes/items.py`** — 删除示例接口，加自己的业务接口

### 第四步：本地启动

```bash
# 首次启动（自动加载 compose.override.yml 的开发配置）
docker compose up --build

# 后续开发可以开启热更新
docker compose watch
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API 文档 | http://localhost:8000/docs |
| 数据库管理 | http://localhost:8081 |
| 邮件测试 | http://localhost:1080 |

默认管理员账号见 `.env` 中的 `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`。

## 生产部署

### 手动首次部署

```bash
# 在服务器上
git clone git@github.com:guanlili/<项目名>.git /path/to/app
cd /path/to/app
# 编辑 .env，填写生产配置（数据库密码、域名等）
vim .env
docker compose up -d --build
```

### 自动部署（GitHub Actions）

push 到 `master` 自动触发部署。需要在 GitHub repo **Settings → Secrets and variables → Actions** 中配置：

| Secret | 说明 |
|--------|------|
| `SERVER_HOST` | 服务器 IP |
| `SERVER_USER` | SSH 用户名（一般是 root） |
| `SERVER_SSH_KEY` | SSH 私钥 |
| `DEPLOY_PATH` | 服务器上的项目路径 |

## 与上游的主要区别

| 项目 | 上游 | 本模板 |
|------|------|--------|
| 反向代理 | Traefik | nginx proxy_pass（内置于前端镜像） |
| CI/CD | staging + production 双套 workflow | 单一 deploy.yml |
| Playwright e2e 测试 | 包含 | 已移除 |
| Copier 模板系统 | 包含 | 已移除 |
| AI 开发规范 | 无 | AI_RULES.md |
