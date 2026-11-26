# 生产部署

本文档描述模板默认的 GitHub Actions + Docker Compose 部署方式。若客户项目使用其他平台，应在 `PROJECT_CONTEXT.md` 中记录差异。

## 首次部署

### GitHub Secrets

在新仓库 **Settings → Secrets → Actions** 配置：

| Secret | 必填 | 说明 |
|--------|:----:|------|
| `SERVER_HOST` | ✅ | 服务器 IP |
| `SERVER_USER` | ✅ | SSH 用户名 |
| `SERVER_SSH_KEY` | ✅ | SSH 私钥 |
| `DEPLOY_PATH` | ✅ | 服务器部署路径 |
| `COMPOSE_PROJECT_NAME` | ✅ | 同服务器各项目不能重复 |
| `APP_PORT` | ✅ | 前端暴露端口 |
| `FRONTEND_HOST` | ✅ | 前端完整地址 |
| `SECRET_KEY` | ✅ | 每个项目唯一的随机 JWT 密钥 |
| `PROJECT_NAME` | ✅ | 项目显示名称 |
| `POSTGRES_PASSWORD` | ✅ | 数据库密码 |
| `FIRST_SUPERUSER` | ✅ | 初始管理员邮箱 |
| `FIRST_SUPERUSER_PASSWORD` | ✅ | 初始管理员密码 |

`BACKEND_CORS_ORIGINS` 会自动跟随 `FRONTEND_HOST`，无需单独配置。

可选配置：

| Secret | 默认 | 说明 |
|--------|------|------|
| `USERS_OPEN_REGISTRATION` | `false` | 是否开放自助注册 |
| `WORKERS` | `1` | 后端 worker 数量 |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_TLS` / `SMTP_SSL` | 空 / `587` / `True` / `False` | SMTP 配置；`SMTP_HOST` 为空时邮件功能关闭 |
| `SMTP_USER` / `SMTP_PASSWORD` | 空 | SMTP 认证 |
| `EMAILS_FROM_EMAIL` | `info@example.com` | 发件人地址 |
| `SENTRY_DSN` | 空 | 自建 GlitchTip 上报 DSN（与 Sentry 协议兼容，不用 Sentry 云）；留空关闭后端上报 |
| `GLITCHTIP_ORIGIN` | 空 | GlitchTip 上报源 origin（scheme+host，不带路径），注入前端 nginx CSP `connect-src`；留空则 CSP 只放行 self |

需要“忘记密码”自助找回时，必须配置完整 SMTP。未配置 SMTP 时，找回密码接口不会实际发送邮件。

### 服务器初始化

```bash
git clone git@github.com:guanlili/<项目名>.git $DEPLOY_PATH
```

之后 push 到 `master` 会触发：

```text
CI（后端 lint + 测试、前端 lint + 构建、客户端一致性、Playwright e2e）
→ 服务器 checkout 到 CI 验证过的 commit
→ 从 Secrets 生成 .env
→ 现场构建镜像（Python/npm 依赖经国内镜像源下载）、运行 Alembic 迁移
→ 重启容器、执行 readiness 检查
→ 清理旧镜像（dangling + 非本次 sha 的旧 tag）
```

master 受分支保护：变更必须经 PR 合并，且上图中三个 CI job（后端、前端、e2e）是必需检查。PR 另外会跑「依赖安全审计」（`npm audit` 与 `pip-audit`），它不参与部署门禁——红了先升级依赖再合并。

> 大陆服务器依赖下载要点：
> - npm 走 `NPM_REGISTRY`（Secret，如 npmmirror），lockfile 的 integrity 校验不受 registry 影响；
> - Python 依赖有特殊处理：`uv sync --frozen` 按 lock 里记录的 `files.pythonhosted.org` 直链下载、
>   忽略 index 配置（[astral/uv#19625](https://github.com/astral-sh/uv/issues/19625)），
>   直连速率可低至 KB/s 级。因此 `backend/Dockerfile` 在 `UV_INDEX_URL` 指向镜像源时
>   会把 lock 中的直链域名重写为镜像的同构路径（tuna/腾讯云镜像均满足 `{mirror}/simple`
>   与 `{mirror}/packages` 同根）。实测腾讯云内网镜像可达 10MB/s，全量依赖构建约 1 分钟。

部署只来自 `master` 的 push 或手动触发。部署任务共用生产并发锁；过期提交会被跳过，只有当前提交自己的 CI 通过后才会部署。

部署脚本会在重启容器前校验部署目标：已有 `.env` 的 `COMPOSE_PROJECT_NAME` 必须与本次配置一致；首次成功部署后会在部署目录写入被 Git 忽略的 `.deploy-target`，后续还会校验仓库和部署路径。这样可以在服务器上存在多个项目时，尽早阻止 `DEPLOY_PATH` 配错。

模板默认提供认证与会话（Refresh Token 轮换和会话全部撤销）、可配置角色与页面权限、用户管理、个人设置、内部审计、请求 ID 和 GlitchTip 错误追踪。文件、系统配置、导入导出和后台任务不作为默认功能；模板不挂载附件 volume，历史遗留的文件表由迁移清理。密码、Token、私钥等敏感值必须放在环境变量或部署平台 Secrets 中。

部署配置由 `scripts/generate-deploy-env.sh` 生成，包含必填校验、特殊字符转义、临时文件原子替换和 600 权限保护。

本地回归检查：

```bash
python3 scripts/test_deploy.py
```

该检查需要 Docker Compose CLI，但不会启动容器。

> `.env` 每次部署都由 workflow 从 Secrets 重新生成。GitHub Secrets 是生产配置的唯一来源，`.env` 永远不要提交到 git。

## HTTP / HTTPS 策略

| 项目性质 | 方案 |
|---------|------|
| 内网工具、临时演示（不用安全上下文 API） | `http://IP:端口` |
| 使用麦克风、摄像头、剪贴板、地理定位或通知 | 必须 HTTPS；`localhost` 例外 |
| 正式上线、面向真实用户 | 必须 HTTPS |

普通 HTTP 会让 JWT 和登录密码暴露在公网，也会导致浏览器禁用部分安全上下文 API。

### 正式上线

1. 添加 DNS A 记录，例如 `项目名.你的域名.com → 服务器 IP`。国内服务器应尽早启动 ICP 备案。
2. 在服务器级 Caddy 配置反向代理（HSTS 在 TLS 终止层加；容器内 nginx 是明文 HTTP，加了也会被浏览器忽略）：

   ```text
   项目名.你的域名.com {
       header Strict-Transport-Security "max-age=31536000"
       reverse_proxy localhost:8083
   }
   ```

   `systemctl reload caddy` 后生效，证书会自动申请和续期。
3. 将 `FRONTEND_HOST` 改为 `https://项目名.你的域名.com`，重新部署。

## 数据库备份

生产数据以 PostgreSQL 为准。模板提供数据库快照、SHA-256 校验和空环境恢复工具。备份包含客户数据，应放在权限受限的目录并同步到异机加密存储；校验和用于发现损坏，不提供防篡改认证。

### 备份

```bash
python3 scripts/backup_restore.py backup /srv/backups/项目名 --project-dir /srv/项目部署目录
```

脚本与部署任务通过 `.maintenance.lock` 互斥；服务器需要 `flock`（Linux 通常由 util-linux 提供）。备份会短暂停止正在运行的 frontend/backend；无论备份成功与否，都会尝试恢复原来运行的服务。数据库保持运行，不能有绕过应用的其他写入者。请安排维护窗口；进程内后台任务可能被中断。

每次产生独立快照目录，包含 `database.dump` 和 `manifest.json`。失败时脚本会删除本次创建的快照目录，保留历史成功快照；未生成完整 manifest 或校验失败的目录不可恢复。应按保留期限定期清理过期快照，异常断电或进程被强制终止留下的半成品也需清理。文件不包含生产 `.env`，灾难恢复时仍需从 GitHub Secrets 配置新环境。

定时备份与失败告警（systemd 服务器一键安装；timer 每日 03:00 错峰执行、关机错过补跑）：

```bash
# 先 dry-run 预览将安装的 unit（不需要 root）
bash scripts/install-backup-timer.sh --backups-dir /srv/backups/项目名 --healthchecks-url https://hc-ping.com/<uuid> --dry-run
# 确认后安装
sudo bash scripts/install-backup-timer.sh --backups-dir /srv/backups/项目名 --healthchecks-url https://hc-ping.com/<uuid>
# 手动触发一次验证链路
sudo systemctl start backup-<compose项目名>.service && journalctl -u backup-<compose项目名>.service -e
```

告警为 healthchecks 类死人开关：备份成功 ping 基础 URL、失败 ping `/fail`；timer 本身静默失效时由对方"超时未 ping"告警兜底。无 systemd 的服务器退回手写 cron（命令见 `install-backup-timer.sh` 生成的 ExecStart）。按磁盘容量与数据保留要求设置异机存储生命周期；应定期在隔离环境恢复最新快照，不能只检查文件存在。

### 校验与恢复

```bash
python3 scripts/backup_restore.py verify /srv/backups/项目名/快照目录
```

恢复目标必须是独立新环境或已人工确认的空数据库。准备对应版本代码、生产配置和 backend 镜像，**不要先启动 prestart**，它会建表导致空库检查失败：

```bash
cd /srv/恢复环境
# compose.yml 必须使用独立 COMPOSE_PROJECT_NAME，避免指向现有项目卷。
docker compose -f compose.yml build backend
python3 scripts/backup_restore.py restore /srv/backups/项目名/快照目录 --project-dir /srv/恢复环境 --confirm-restore
docker compose -f compose.yml up -d
```

工具会先验证校验和，再检查应用已停止、数据库为空；数据库在事务中恢复。恢复失败时不要启动应用，应检查目标并重新准备空环境后重试。

启动后检查 readiness、登录与关键业务记录。新版本代码需要通过 prestart 正常应用后续迁移；备份格式或 PostgreSQL 大版本变化时先在隔离环境验证兼容性。

本地与 CI 的隔离恢复演练：

```bash
python3 scripts/test_backup_restore.py --integration
```

演练自动创建两个临时 Compose 项目，只使用 `app_test` 数据库；比较恢复后的记录，验证拒绝覆盖非空库，并清理临时容器与卷。

### 保留策略与异地副本

- **本地快照保留**：建议保留最近 **7 天**每日快照（`/srv/backups/项目名/`），超期由清理任务删除；合规要求更长留存时按月另存归档快照。清理脚本只删完整 manifest 且校验通过的历史快照，半成品目录需人工确认后删除。
- **异地副本**：本地快照必须同步到独立存储（推荐阿里云 OSS，企业认证账号；不新增腾讯云 COS）。在服务器定时把当日快照目录加密后 `ossutil cp` 到独立 bucket，按生命周期策略保留 **30 天**；OSS 与生产机不在同一可用区，单机房故障不丢备份。备份含客户数据，上传前加密、bucket 拒绝公网读写。
- **恢复演练周期**：**每季度至少一次**在隔离环境用最新快照执行完整恢复（数据库），核对记录条数、登录与关键业务可用；恢复演练记录留档。仅校验快照文件存在不等于可恢复。
- **.env 与密钥**：备份不含生产 `.env` 与 `SECRET_KEY`，灾难恢复时从 GitHub Secrets 重新配置；密钥与备份分处保存。

### 镜像与多环境

模板默认在服务器现场 `compose up --build` 构建镜像（`BACKEND_IMAGE` / `FRONTEND_IMAGE` 仅作标签名，不推送外部 registry）。

| 场景 | 建议 |
|------|------|
| 单机小项目、内网演示 | 保持现场构建，简单直接；无需 registry |
| 多机部署、CI 产物复用到生产 | 推送到私有 registry（如 GHCR 或阿里云 ACR）：CI 构建并打 `sha` 标签推送，服务器只 `pull` 同版本镜像，避免现场构建受网络/缓存影响 |
| 预发（staging） | 用独立 `COMPOSE_PROJECT_NAME`、独立数据库与域名，从非保护分支部署；预发与生产共用一套 Compose 编排，仅 `.env` 与镜像标签不同。生产只从 `master` 部署 |

切换到 registry 模式时，在 Secrets 提供 registry 地址与登录凭据，CI 增加 `docker build/push` 步骤，服务器 compose 用 `image:` 拉取而不 `--build`。

## 回滚

推荐通过新提交回滚：

```bash
git revert <坏提交>
git push
```

紧急事故可以临时回到已知正常提交：

```bash
ssh 服务器 "cd 部署路径 && git reset --hard <上一个好提交> && docker compose -f compose.yml up -d --build"
```

紧急回滚后仍需在仓库中执行 `git revert`，让远端历史与线上版本一致。

代码回滚不会自动回滚 Alembic 迁移。对于删除列、修改类型等破坏性迁移，优先做前向修复，不要直接执行 `alembic downgrade`；操作前先备份数据库。

## 部署冒烟检查

部署流水线在就绪检查后，经服务器本机 nginx 执行 `scripts/smoke_test.py`：检查登录页应用入口、数据库就绪，以及未登录访问当前用户、访问权限和角色接口必须返回 401。任何失败都会使部署任务失败，且不会写入本次成功部署标记；不会自动回滚数据库或代码。

需要完整认证检查时，管理员提前建立两个**专用冒烟账号**，在 GitHub Secrets 配置：

- `SMOKE_ADMIN_EMAIL`、`SMOKE_ADMIN_PASSWORD`：专用管理员账号。
- `SMOKE_VISITOR_EMAIL`、`SMOKE_VISITOR_PASSWORD`：非管理员账号，使用默认访客角色或明确配置的访客角色。

把仓库 Actions Variable `SMOKE_REQUIRE_AUTH` 设为 `true`，可强制要求两组账号齐全。默认不配置时会明确输出跳过认证检查，不会把基础检查标成完整验收；账号只配一半时检查失败。

认证检查覆盖登录、当前用户、角色管理的管理员/访客差异、用户列表的实际页面权限以及刷新后的访问。脚本不会创建用户、修改角色或业务数据，但会创建和轮换登录会话，最后注销该专用账号的全部会话，因此不要复用日常操作账号。认证信息通过掩码后的 base64 JSON 和标准输入传输，不写入生产 `.env` 或日志。base64 是传输编码，不是加密。

本地可用环境变量传入专用测试账号后运行：

```bash
python3 scripts/smoke_test.py http://localhost:80 --require-auth
```

此检查验证 HTTP/API 行为，不替代浏览器交互、前端 JavaScript 执行与视觉验收。认证流程在 CI 中还会通过独立 `app_test` 的真实 API 测试，测试账号不进入生产。

## 上线端到端验收 Checklist

首次部署或重大版本上线后，逐项核对；全部通过再对外交付。

**配置与安全**

- [ ] `SECRET_KEY` 为每项目唯一随机值，未用默认/演示密钥
- [ ] `POSTGRES_PASSWORD` 为强密码，未用 `changethis`
- [ ] 生产 `ENVIRONMENT=production`；`USERS_OPEN_REGISTRATION` 按需要关闭
- [ ] 面向真实用户的站点已 HTTPS，Caddy 层加了 HSTS；HTTP 明文不承载登录
- [ ] 错误监控已接自建 GlitchTip（`SENTRY_DSN` / `VITE_SENTRY_DSN`），`GLITCHTIP_ORIGIN` 与实例对外地址一致，CSP `connect-src` 放行该域；未配置上报时 CSP 仅 `self`
- [ ] 无 `.env`、本地密钥、`node_modules`、`__pycache__`、覆盖率 HTML 被提交进仓库

**服务与数据**

- [ ] `/api/v1/utils/ready-check/` 返回 Ready；`/docs` 按需要在生产关闭或加访问控制
- [ ] 管理员账号可登录、可进入 dashboard；访客账号权限与设计一致
- [ ] 关键业务记录可读写；刷新会话、登出、全部登出均正常
- [ ] 审计日志有记录（登录成功/失败、会话撤销、密码重置等）
- [ ] 备份任务已安装并成功跑过一次；快照可 `verify` 校验通过
- [ ] 异地副本已同步到 OSS（或独立存储），保留策略生效

**发布与回滚**

- [ ] CI 全绿（后端 lint/测试/覆盖率、前端 lint/测试/构建/客户端一致性、e2e、依赖审计、CodeQL）
- [ ] 本次部署 commit 与 CI 验证过的版本一致；旧镜像/临时容器已清理
- [ ] 已明确回滚方式（`git revert`）与最近一次可用备份位置

## 本地从零启动 Checklist（新坑）

`init_project.py` 生成骨架后，本地首次拉起前确认：

- [ ] `.env` 由 `.env.example` 复制，必填项（`SECRET_KEY`、`FIRST_SUPERUSER_PASSWORD`、`POSTGRES_PASSWORD`）已填
- [ ] `docker compose up --build` 后 prestart 迁移成功、backend healthy、frontend 可访问
- [ ] 用管理员账号登录；API 文档与冒烟检查通过
- [ ] 若摘除了示例 Job/private 路由，`alembic check` 无未生成迁移、`npm run generate-client` 后 `src/client/` 无 diff

