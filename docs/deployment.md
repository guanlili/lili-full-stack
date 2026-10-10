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

需要“忘记密码”自助找回时，必须配置完整 SMTP。未配置 SMTP 时，找回密码接口不会实际发送邮件。

### 服务器初始化

```bash
git clone git@github.com:guanlili/<项目名>.git $DEPLOY_PATH
```

之后 push 到 `master` 会触发：

```text
CI（后端 lint + 测试、前端 lint + 构建、客户端一致性）
→ checkout 到 CI 验证过的 commit
→ 从 Secrets 生成 .env
→ 构建镜像、运行 Alembic 迁移
→ 重启容器、执行 readiness 检查
→ 清理旧镜像
```

部署只来自 `master` 的 push 或手动触发。部署任务共用生产并发锁；过期提交会被跳过，只有当前提交自己的 CI 通过后才会部署。

部署脚本会在重启容器前校验部署目标：已有 `.env` 的 `COMPOSE_PROJECT_NAME` 必须与本次配置一致；首次成功部署后会在部署目录写入被 Git 忽略的 `.deploy-target`，后续还会校验仓库和部署路径。这样可以在服务器上存在多个项目时，尽早阻止 `DEPLOY_PATH` 配错。

模板默认提供认证与会话（Refresh Token 轮换和会话全部撤销）、可配置角色与页面权限、用户管理、个人设置、内部审计、请求 ID 和 Sentry 错误追踪。文件、系统配置、导入导出和后台任务不再作为默认功能。历史数据库表和附件 volume 保留用于升级与备份兼容，精简不会删除已有数据。密码、Token、私钥等敏感值必须放在环境变量或部署平台 Secrets 中。

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
2. 在服务器级 Caddy 配置反向代理：

   ```text
   项目名.你的域名.com {
       reverse_proxy localhost:8083
   }
   ```

   `systemctl reload caddy` 后生效，证书会自动申请和续期。
3. 将 `FRONTEND_HOST` 改为 `https://项目名.你的域名.com`，重新部署。

## 数据库备份

生产数据分为 PostgreSQL 和附件 volume `app-uploads`，必须一起备份。模板提供联合备份、SHA-256 校验和空环境恢复工具。备份包含客户数据，应放在权限受限的目录并同步到异机加密存储；校验和用于发现损坏，不提供防篡改认证。

### 联合备份

```bash
python3 scripts/backup_restore.py backup /srv/backups/项目名 --project-dir /srv/项目部署目录
```

脚本与部署任务通过 `.maintenance.lock` 互斥；服务器需要 `flock`（Linux 通常由 util-linux 提供）。备份会短暂停止正在运行的 frontend/backend，保持数据库与附件一致；无论备份成功与否，都会尝试恢复原来运行的服务。数据库保持运行，不能有绕过应用的其他写入者。请安排维护窗口；进程内后台任务可能被中断。

每次产生独立快照目录，包含 `database.dump`、`uploads.tar` 和 `manifest.json`。失败时脚本会删除本次创建的快照目录，保留历史成功快照；未生成完整 manifest 或校验失败的目录不可恢复。应按保留期限定期清理过期快照，异常断电或进程被强制终止留下的半成品也需清理。文件不包含生产 `.env`，灾难恢复时仍需从 GitHub Secrets 配置新环境。

定时任务示例（替换项目路径；按磁盘容量与数据保留要求设置异机存储生命周期）：

```cron
0 3 * * * /usr/bin/python3 /srv/项目部署目录/scripts/backup_restore.py backup /srv/backups/项目名 --project-dir /srv/项目部署目录 >> /srv/backups/项目名/backup.log 2>&1
```

安装定时任务前先创建备份目录并限制权限；配置备份失败告警。应定期在隔离环境恢复最新快照，不能只检查文件存在。

### 校验与恢复

```bash
python3 scripts/backup_restore.py verify /srv/backups/项目名/快照目录
```

恢复目标必须是独立新环境或已人工确认的空数据库与空附件卷。准备对应版本代码、生产配置和 backend 镜像，**不要先启动 prestart**，它会建表导致空库检查失败：

```bash
cd /srv/恢复环境
# compose.yml 必须使用独立 COMPOSE_PROJECT_NAME，避免指向现有项目卷。
docker compose -f compose.yml build backend
python3 scripts/backup_restore.py restore /srv/backups/项目名/快照目录 --project-dir /srv/恢复环境 --confirm-restore
docker compose -f compose.yml up -d
```

工具会先验证校验和和附件路径，再检查应用已停止、数据库为空、附件卷为空；数据库在事务中恢复。恢复失败时不要启动应用，应检查目标并重新准备空环境后重试。数据库与文件系统无法跨存储原子提交，附件恢复失败时可能留下已恢复的数据库。

启动后检查 readiness、登录、关键业务记录与附件下载。新版本代码需要通过 prestart 正常应用后续迁移；备份格式或 PostgreSQL 大版本变化时先在隔离环境验证兼容性。

本地与 CI 的隔离恢复演练：

```bash
python3 scripts/test_backup_restore.py --integration
```

演练自动创建两个临时 Compose 项目，只使用 `app_test` 数据库；比较恢复后的记录与附件字节，验证拒绝覆盖非空库，并清理临时容器与卷。

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
