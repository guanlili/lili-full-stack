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
| 代码规范 | Ruff + ty（后端）/ Biome（前端）|
| 容器 | Docker Compose（nginx 内置 /api 代理，无 Traefik）|
| CI/CD | GitHub Actions：lint + 测试通过后 → server-side git pull + docker compose up |

---

## 开启新项目

### 第一步：基于本模板创建新仓库

在 GitHub 上点 **Use this template → Create a new repository**（不是 Fork）。

### 第二步：克隆并初始化

```bash
git clone git@github.com:guanlili/<新项目名>.git
cd <新项目名>
bash scripts/init-project.sh "项目显示名"
```

脚本一次性完成：生成 `.env`（`SECRET_KEY`、数据库密码、管理员密码全部随机化）、
统一改名（`PROJECT_NAME`、前端 `APP_NAME`、页面标题），并输出剩余待办清单。
本地管理员账号会打印在结果里（也记录在 `.env`）。

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

同时**决定注册方式**：自助注册默认只在本地开启（生产由可选 Secret `USERS_OPEN_REGISTRATION` 控制，默认关）。
如果项目是"管理员建账号"模式，交付前把注册入口一并删掉：`frontend/src/routes/signup.tsx` 和登录页上的注册链接。

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

# 启用热更新（后端 --reload + 前端 vite HMR，推荐日常开发用这个）
docker compose watch

# 停止
docker compose down
```

本地开发时前端跑的是 vite dev server（5173 端口，支持热更新），生产镜像才是 nginx 静态托管。

---

## 新功能开发流程

**权威版本在 [CLAUDE.md](CLAUDE.md)**（Claude Code 每次会话自动加载，人和 AI 都照它执行），此处只留概览，避免两份文档漂移：

> 后端加模型/CRUD/路由 → Alembic 迁移 → `cd frontend && npm run generate-client` 同步客户端 → 前端加页面。

编码规范（命名、类型、禁止模式）见 [AI_RULES.md](AI_RULES.md)。

---

## Claude Code 自定义指令

项目内置了 4 个自定义斜杠命令，在 Claude Code 中可直接使用：

| 指令 | 用途 |
|------|------|
| `/new-feature <名称>` | 自动创建完整功能模块（后端 model + crud + route + 前端页面） |
| `/migration <描述>` | 生成并应用 Alembic 数据库迁移 |
| `/generate-client` | 重新生成前端 API 客户端 |
| `/upgrade-deps` | 升级所有依赖包（uv + npm）|

示例：

```
/new-feature order
```

Claude Code 会按标准流程自动创建订单模块的全部后端和前端代码。

仓库还内置了团队共享的权限白名单（`.claude/settings.json`）：日常开发的高频命令
（docker compose、npm run、uv run、git 只读、gh 查看 CI 等）已预授权，克隆即用，
少弹大部分权限框；破坏性操作（`down -v`、push、commit 等）仍会请求确认。
注意边界：`uv run *` 和 `docker compose exec backend *` 实质上允许 AI 免确认执行任意代码——
这是"减少弹框"的有意取舍，团队成员应知情；要求更严格的项目可自行收窄白名单。
个人偏好写在 `.claude/settings.local.json`（已被 gitignore，不入库）。

---

## 生产部署

### 首次部署

**1. 配置 GitHub Secrets**

在新仓库 **Settings → Secrets → Actions** 添加以下 11 个必填 Secret：

| Secret | 必改 | 说明 | 示例 |
|--------|:----:|------|------|
| `SERVER_HOST` | | 服务器 IP | `42.193.108.162` |
| `SERVER_USER` | | SSH 用户名 | `root` |
| `SERVER_SSH_KEY` | | SSH 私钥（完整内容）| `-----BEGIN...` |
| `DEPLOY_PATH` | ✅ | 服务器部署路径，每个项目不同 | `/mnt/datadisk0/项目名` |
| `APP_PORT` | ✅ | 前端暴露端口，同服务器上各项目不能重复 | `8083` |
| `FRONTEND_HOST` | ✅ | 前端完整地址，与 `APP_PORT` 对应 | `http://42.193.108.162:8083` |
| `SECRET_KEY` | ✅ | JWT 签名密钥，每个项目必须唯一 | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `PROJECT_NAME` | ✅ | 项目名称（显示在邮件等处）| `我的项目` |
| `POSTGRES_PASSWORD` | | 数据库密码，建议各项目不同 | 自定义强密码 |
| `FIRST_SUPERUSER` | | 初始管理员邮箱 | `admin@example.com` |
| `FIRST_SUPERUSER_PASSWORD` | | 初始管理员密码 | 自定义 |

> `BACKEND_CORS_ORIGINS` 自动与 `FRONTEND_HOST` 保持一致，无需单独配置。

另有 2 个**可选** Secret（不设置则用默认值）：

| Secret | 默认 | 说明 |
|--------|------|------|
| `USERS_OPEN_REGISTRATION` | `false` | 是否开放自助注册。生产默认关闭（管理员在后台建账号）；产品需要用户自行注册时设为 `true` |
| `WORKERS` | `1` | 后端 worker 进程数，大流量项目可调至 CPU 核数×2+1 |

**2. 服务器上 clone 一次**

```bash
git clone git@github.com:guanlili/<项目名>.git $DEPLOY_PATH
```

只需做一次。之后 push 到 `master` 即自动触发：**CI（后端 lint + 测试、前端 lint + 构建、前后端客户端一致性）→ 全部通过才部署** → checkout 到该次 CI 验证过的 commit → 从 Secrets 写入 `.env` → 构建镜像 → 跑 Alembic 迁移 → 重启容器 → 健康检查验证 → 清理旧镜像。

> `.env` 每次部署都由 workflow 从 Secrets 重新生成，GitHub Secrets 是唯一配置源。**`.env` 永远不要提交到 git**（已被 `.gitignore` 忽略）。

### HTTP / HTTPS 策略

按项目性质二选一，**立项时就确定**：

| 项目性质 | 方案 |
|---------|------|
| 内网工具、临时演示 | `http://IP:端口`（模板默认），够用，不折腾 |
| 正式上线、面向真实用户 | **必须 HTTPS**，按下面三步走 |

HTTP 明文意味着 JWT token 和登录密码裸奔公网、浏览器标"不安全"、剪贴板/摄像头等 API 不可用——演示可以接受，正式上线不行。

**正式上线三步（前置条件：已备案域名）：**

1. **域名解析**：加一条 A 记录 `项目名.你的域名.com → 服务器 IP`。国内服务器要求域名已 ICP 备案——**备案需 1~3 周，立项时就启动**；子域名跟随主域名备案，不用重复办。优先用客户自己已备案的域名（备案主体在客户侧，域名归属也更合理）。
2. **服务器级 Caddy**（整台服务器装一次，所有项目共享；TLS 必须在服务器层做，因为 443 端口只有一个）：
   ```
   # apt install caddy 后编辑 /etc/caddy/Caddyfile，每个项目加 3 行：
   项目名.你的域名.com {
       reverse_proxy localhost:8083   # 对应该项目的 APP_PORT
   }
   ```
   `systemctl reload caddy` 生效，证书自动申请续期。安全组需放行 80/443。
3. **改 Secret**：`FRONTEND_HOST` 改为 `https://项目名.你的域名.com`，push 触发重新部署即可（CORS 自动跟随，代码零改动）。

### 数据库备份

生产数据只存在 Docker volume 里，服务器磁盘损坏即全部丢失。上线后在服务器配置定时备份：

```bash
# crontab -e，每天凌晨 3 点备份，保留最近 7 天
0 3 * * * docker compose -f 部署路径/compose.yml exec -T db pg_dump -U postgres app | gzip > /备份目录/db-$(date +\%w).sql.gz
```

恢复：`gunzip -c 备份文件.sql.gz | docker compose exec -T db psql -U postgres app`

### 回滚

CI 挡得住挂掉的构建，挡不住"测试全绿但业务逻辑错了"的版本。上线后发现坏版本：

**常规回滚（推荐）**——revert 后走正常流水线，有 CI 门槛兜底：

```bash
git revert <坏提交>   # 或 git revert <坏起点>..<坏终点> 批量撤销
git push              # 自动触发 CI → 部署 → 健康检查
```

**紧急回滚（生产事故，等不了 CI 的几分钟）**——直接在服务器上退：

```bash
ssh 服务器 "cd 部署路径 && git reset --hard <上一个好提交> && docker compose -f compose.yml up -d --build"
```

> 紧急回滚只是止血：master 上坏提交还在，下次 push 会把它重新部署上去。
> 止血后必须回到常规流程 revert + push，让远端历史与线上一致。

**数据库迁移注意**：回滚代码不会回滚 Alembic 迁移。坏版本若只是**加**了表/列，旧代码通常兼容，直接回滚代码即可；若做了破坏性变更（删列、改类型），优先前向修复（fix + push）而不是 `alembic downgrade`——降级操作有数据丢失风险，动手前先做一次备份。

---

## 模板维护

本仓库是模板，会定期更新，现有项目不会受影响。

### 维护节奏

| 时机 | 操作 |
|------|------|
| 做项目时踩了坑 | 回来更新 `AI_RULES.md` 或 `CLAUDE.md` |
| 每季度 | 运行 `/upgrade-deps` 升级依赖 |
| 发现更好的开发模式 | 更新 `.claude/commands/` 中的指令 |

### 从模板同步改进到现有项目

模板和具体项目是独立仓库，没有 git 关联。需要手动同步时，把改进的文件（`CLAUDE.md`、`AI_RULES.md`、`compose.yml`、`.claude/commands/`）复制过去即可。

---

## 项目结构

```
lili-full-stack/
├── .claude/
│   └── commands/          # Claude Code 自定义斜杠命令
├── scripts/
│   └── init-project.sh    # 新项目一键初始化（改名 + 密钥随机化）
├── .env.example           # 环境变量模板（复制为 .env 使用）
├── .env                   # 实际配置（gitignore 忽略，永不提交；生产由 Secrets 生成）
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
    ├── scripts/           # generate-client.sh / regen-lockfile.sh
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
| CI/CD | staging + production 双套 | 单一 workflow：CI（lint+测试）通过后部署 |
| Playwright e2e 测试 | 包含 | 已移除 |
| Copier 模板系统 | 包含 | 已移除 |
| AI 开发规范 | 无 | AI_RULES.md + CLAUDE.md + .claude/commands/ |

---

## 设计取舍（有意不做的东西）

> 本节记录模板**刻意省略**的实践及原因。补齐它们之前请先读这里——多数"缺失"是权衡后的决定，不是疏漏。

| 不做什么 | 为什么 |
|---------|--------|
| 前端单元测试（vitest） | 模板阶段收益低。前端质量门槛 = tsc 类型检查 + biome + 后端 API 测试兜底；具体项目有复杂前端逻辑时再按需引入 |
| dependabot / renovate | 小团队没精力处理持续的升级 PR 噪音。用季度 `/upgrade-deps` 集中升级 + 验证代替 |
| pre-commit 钩子 | CI 是唯一质量门槛。本地钩子对 AI 驱动的开发是摩擦（AI 每次提交都会被格式化钩子打断），且和 CI 重复 |
| staging 环境 | 单服务器多项目、快速交付定位。staging 的维护成本大于收益；重要变更靠 CI 门槛 + 部署后健康检查兜底 |
| JWT refresh token | 8 天 access token + localStorage 是简单性取舍，适合工具型产品。对安全有更高要求的项目再升级会话机制 |
| 登录接口限流 | 不在代码层加依赖。正式上线的项目在 Caddy 层做 `rate_limit`（见 HTTPS 章节），内网/演示项目不需要 |
| 重置密码 token 一次性失效 | token 48 小时内可重复使用（改完密码不作废）。工具型项目风险低；高安全要求的项目可把 token 绑定当前密码 hash（密码一改即失效） |
| 生产环境隐藏 `/docs`、`/redoc` | API 文档公开对内网工具是便利。正式上线面向公网的项目建议关闭（`ENVIRONMENT=production` 时设 `docs_url=None`）或在 Caddy 层加 basic auth |
| Kubernetes / 多机编排 | 单服务器 docker compose 覆盖当前所有项目规模。规模到了再迁移，不预支复杂度 |
