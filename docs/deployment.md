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

生产数据位于 Docker volume 中。上线后配置定时备份：

```bash
# crontab -e：每天凌晨 3 点备份，保留最近 7 天
0 3 * * * docker compose -f 部署路径/compose.yml exec -T db pg_dump -U postgres app | gzip > /备份目录/db-$(date +\%w).sql.gz
```

恢复：

```bash
gunzip -c 备份文件.sql.gz | docker compose exec -T db psql -U postgres app
```

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
