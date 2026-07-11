# lili-full-stack

个人全栈项目模板，基于 [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) 精简定制。

## 技术栈

**后端**
- FastAPI + SQLModel + PostgreSQL
- uv 包管理，Ruff linting，MyPy 类型检查
- JWT 认证，Alembic 数据库迁移

**前端**
- React 19 + TypeScript + Vite
- TailwindCSS v4 + Radix UI + Lucide React
- TanStack Query + TanStack Router
- Biome linting

**基础设施**
- Docker Compose（无 Traefik，nginx proxy_pass 代理 /api）
- GitHub Actions 自动部署（server-side git pull + docker compose up）

## 与上游的主要区别

| 项目 | 上游 | 本模板 |
|------|------|--------|
| 反向代理 | Traefik（复杂 label 配置） | nginx proxy_pass（内置前端镜像） |
| 本地开发 | compose.override.yml + Traefik | compose.override.yml，直接端口映射 |
| CI/CD | deploy-staging + deploy-production | 单一 deploy.yml |
| Playwright e2e | 包含 | 已移除 |
| Copier 模板系统 | 包含 | 已移除 |
| AI 规范文档 | 无 | AI_RULES.md |

## 快速开始

### 本地开发

```bash
# 复制并编辑环境变量
cp .env.example .env  # 编辑数据库密码、secret key 等

# 启动（自动加载 compose.override.yml）
docker compose up --build

# 或启用热更新
docker compose watch
```

访问：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/docs
- Adminer：http://localhost:8081
- Mailcatcher：http://localhost:1080

### 生产部署

```bash
# 服务器上
git clone <repo> /path/to/app
cd /path/to/app
cp .env.example .env  # 填写生产配置
docker compose up -d --build
```

GitHub Actions 自动部署需要在 repo Settings → Secrets 中配置：
- `SERVER_HOST` — 服务器 IP
- `SERVER_USER` — SSH 用户名
- `SERVER_SSH_KEY` — SSH 私钥
- `DEPLOY_PATH` — 服务器上的项目路径

## 开始新项目

1. 在 GitHub 上 fork 或 "Use this template"
2. 克隆到本地
3. 修改 `.env`、`AI_RULES.md` 中的项目特定信息
4. 删除不需要的示例代码（`backend/app/models.py` 中的 Item 模型等）
5. 开始开发
