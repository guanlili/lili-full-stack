# Full Stack FastAPI Template (轻量版)

这是一个轻量级的全栈模板，采用 **FastAPI** (后端) 和 **React/Vite** (前端)，并使用 **Docker Compose** 进行编排。

该模板专为快速开发和部署而设计，移除了复杂的 CI/CD 和模板生成工具，保持简洁高效。

## 🛠️ 技术栈

- **后端**: [FastAPI](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/), [PostgreSQL](https://www.postgresql.org/).
- **前端**: [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/), [Shadcn UI](https://ui.shadcn.com/), [TanStack Query](https://tanstack.com/query/latest) & [Router](https://tanstack.com/router/latest).
- **基础设施**: [Docker Compose](https://docs.docker.com/compose/), [Traefik](https://traefik.io/) (反向代理).

## 🌿 Git 开发流程 (重要)

本项目的基础稳定分支为 `lightweight`。请务必基于此分支进行开发。

```bash
# 1. 切换到 lightweight 分支并获取最新代码
git checkout lightweight
git pull origin lightweight

# 2. 为你的新功能创建一个新分支
git checkout -b project/your-project-name

# 3. 开发完成后，提交 Pull Request 合并回 lightweight 或 main (视团队规范而定)
```

## ✅ 前置要求

确保你的环境已安装以下工具：
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js](https://nodejs.org/) (用于本地前端开发)
- [Python 3.10+](https://www.python.org/) & [uv](https://github.com/astral-sh/uv) (推荐用于本地后端开发)

## 🚀 快速开始 (Docker Compose) - 推荐

这是运行全栈应用（前端 + 后端 + 数据库 + 代理 + 邮件测试）最简单的方式。

1. **配置环境变量**:
   检查根目录下的 `.env` 文件。
   
   - **本地开发**: 默认值即可直接运行。
   - **生产环境**: 请修改 `SECRET_KEY`, `POSTGRES_PASSWORD`, `FIRST_SUPERUSER_PASSWORD`。
   
2. **启动服务**:
   
   ```bash
   docker compose up -d --build
   ```
   
3. **访问应用**:
   - **前端首页**: http://localhost
   - **后台登录**: http://localhost/login
     - **默认账号**: `admin@example.com`
     - **默认密码**: `changethis`
   - **API 文档 (Swagger UI)**: http://localhost/docs
   - **Traefik 面板**: http://localhost:8080

4. **停止服务**:
   
   ```bash
   docker compose down
   ```

## 💻 本地开发

如果你偏好在本地运行服务以便于调试或使用 IDE 功能：

### 1. 后端 (FastAPI)

```bash
cd backend

# 安装依赖 (使用 uv)
uv sync

# 运行数据库 (Postgres 需要先运行，例如通过 Docker 只启动 db)
# 你可以在根目录运行: docker compose up -d db

# 启动后端服务
uv run fastapi dev app/main.py
```
*后端服务运行在 http://localhost:8000*

### 2. 前端 (React + Vite)

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```
*前端服务运行在 http://localhost:5173* (已配置代理 `/api` 请求转发至后端)。

## 🔄 核心工作流

### 1. 生成前端客户端 (SDK)
当你修改了后端 API 模型或路由后，需要重新生成前端 TypeScript SDK，以确保前端代码拥有严格的类型检查。

1. 确保后端服务正在运行 (Docker 或本地 8000 端口均可)。
2. 在项目根目录运行生成脚本：
   ```bash
   ./scripts/generate-client.sh
   ```
   *这会更新 `frontend/src/client` 目录下的 API 类型和方法。*

### 2. 数据库迁移 (Migrations)
我们要使用 **Alembic** 进行数据库变更管理。

**在 Docker 容器内操作 (推荐):**
```bash
# 进入后端容器
docker compose exec backend bash

# 生成新迁移文件 (在你修改了代码中的 SQLModel 后运行)
uv run alembic revision --autogenerate -m "Add new table"

# 应用迁移到数据库
uv run alembic upgrade head
```

### 3. 添加新功能 (示例)
1. **模型**: 在 `backend/app/models.py` (或新建文件) 中添加 SQLModel。
2. **API**: 创建 `backend/app/api/routes/your_feature.py` 并在 `backend/app/api/main.py` 中注册路由。
3. **迁移**: 运行 Alembic 迁移以更新数据库结构。
4. **SDK**: 运行 `./scripts/generate-client.sh` 更新前端 SDK。
5. **UI**: 在 `frontend/src/routes/` 中创建新路由，并使用生成的 SDK 开发界面。

## 🌐 关于 Traefik (网关/反向代理)

本项目内置了 **Traefik** 作为反向代理和负载均衡器（"网关"）。它负责将流量根据规则转发给前端或后端容器。

### 1. 管理面板 (Dashboard)
在本地开发模式下，我们开启了非安全模式的面板，你可以直接访问：
👉 **http://localhost:8080/dashboard/**

在这里你可以：
- 查看 **Routers**: 当前定义的路由规则（例如 `/api` 转发给 Backend）。
- 查看 **Services**: 后端服务的健康状态。
- 调试 404/502 错误：如果请求不通，首先看这里路由是否变绿。

### 2. 多项目部署建议 (进阶)
默认情况下，本模板每个项目自带一个 Traefik（占用 80/443 端口）。这意味着你无法在同一台服务器上同时运行两个基于此模板的项目。

**生产环境推荐架构**：
如果你有一台服务器需要部署多个项目，建议采用 **全局 Traefik** 模式：
1. 在服务器上单独启动一个 Traefik 容器，占用 80/443 端口，作为唯一的流量入口。
2. 创建一个共享 Docker 网络（如 `web-gateway`）。
3. 修改本项目的 `docker-compose.yml`：
   - **移除**本项目自带的 `traefik` 服务。
   - 将 `frontend` 和 `backend` 服务加入 `web-gateway` 网络。
   - 修改 `labels`，使用 `Host()` 规则（如 `Host('myapp.example.com')`）来区分不同项目。

## 🚢 部署与运维

本模板采用 "Docker 优先" 的设计理念。

### 部署步骤
1. **服务器准备**: 准备一台安装了 Docker & Docker Compose 的服务器 (推荐 Ubuntu/Debian)。
2. **克隆代码**: 将本项目 (`lightweight` 分支) 克隆到服务器。
3. **环境配置**:
   
   - 创建或更新 `.env` 文件。
   - **严重警告**: 必须修改 `POSTGRES_PASSWORD`, `FIRST_SUPERUSER_PASSWORD` 和 `SECRET_KEY` 为强密码。
   - 将 `DOMAIN` 设置为你的实际域名。
4. **运行**:
   ```bash
   docker compose up -d --build
   ```

### 日志与排错

```bash
# 查看所有日志
docker compose logs -f


# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```
