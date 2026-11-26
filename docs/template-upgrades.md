# 将模板改进同步到客户项目

## 记录模板基线

初始化项目时，在 `PROJECT_CONTEXT.md` 记录模板仓库、采用的 commit 和模板版本（见 `CHANGELOG.md`）。每次同步完成后更新基线。客户业务版本与模板版本分别维护。

## 同步流程

1. 确保客户项目已有可恢复的提交，建立升级分支，检查当前业务改动和模板更新记录。
2. 添加模板为只读参考 remote，fetch 后查看基线与目标版本之间的 diff。GitHub Template 创建的仓库不一定有共同祖先，不能假设可以直接 merge。
3. 按功能挑选 diff 并适配现有代码。只有确认提交范围完全适合客户项目时才 cherry-pick；不要整目录覆盖 `backend/`、`frontend/`、`docs/` 或部署配置。
4. 保留客户 `PROJECT_CONTEXT.md`、业务模型、权限规则、域名和部署差异。密钥与生产环境文件不参与同步。
5. 阅读每批更新的数据库/API兼容性说明；需要时生成迁移和客户端，并执行客户业务验收与模板回归。
6. 通过 PR 评审和 CI 后发布，记录采用版本及未采用的改进。

## 2026.11.26 批次（安全加固 / 骨架收口 / 测试加厚）

| 改进 | 主要文件 | 同步注意事项 |
|------|----------|--------------|
| 上传骨架剥离 | 模型 `asset.py`、迁移 `0007`、`compose.yml`、`backup_restore.py` | 客户若已自行实现文件上传，保留自身实现，不要整段套用剥离 diff；`0007` drop `file_asset` 前确认无业务依赖；备份脚本已改为纯 PostgreSQL 快照，附件打包/校验/恢复逻辑需在客户侧自行保留 |
| RefreshToken 外键级联 | 模型 `auth.py`、迁移 `0008` | 跑迁移前先确认无 `user_id` 指向已删除用户的孤儿刷新令牌，否则加外键约束会失败；删号时刷新令牌随用户级联清理，作为应用层吊销的双保险 |
| pre-commit 本地快检 | `.pre-commit-config.yaml` | 本地 `pre-commit install` 启用；钩子复用项目既有 ruff / biome 工具链，不引入新的独立二进制 |
| 安全加固 | 中间件、CORS、安全头 | 写操作 Origin 校验、CORS 允许方法/请求头收紧、后端安全头兜底；客户自定义前端域名/Origin 需加入 `BACKEND_CORS_ORIGINS` 白名单 |
| 测试加厚 | `backend/tests/`、`frontend/tests/` | 纯测试代码，cherry-pick 即可，无运行时行为变化；前端 RTL 依赖既有 jsdom 装配 helper |

数据库：迁移 `0007` 清理 `file_asset`、`0008` 为 refresh token 补外键级联（head `0008`）。API 契约不变，无需重新生成客户端。

## 2026.11.23 批次（指令层同步 / 合并门禁 / 供应链）

**仓库设置不随模板复制，每个客户仓库都要手动开一次：**

| 设置 | 位置 | 建议值 |
|------|------|--------|
| master 分支保护 | Settings → Branches → master | Require a pull request before merging（不要求批准）；Require status checks 勾选三个 CI job；Include administrators |
| Dependabot alerts、Dependabot security updates | Settings → Code security | 开启 |
| Code scanning（默认配置） | Settings → Code security | 语言选 Actions、JavaScript/TypeScript、Python |

| 改进 | 主要文件 | 同步注意事项 |
|------|----------|--------------|
| 指令文档 | `CLAUDE.md`、`AGENTS.md`、`docs/module-development.md`、`.claude/commands/new-feature.md` | 客户项目改写过这些文件时，把「模板约定」一节和验证步骤逐条并进去，不要整文件覆盖 |
| 依赖安全审计 job | `.github/workflows/deploy.yml` | 仅 PR 运行、不进 deploy 的 needs；有意不设为必需检查（原因见 CHANGELOG） |
| dependabot 全组限 major | `.github/dependabot.yml` | postgres 等大版本升级改为单独 PR，合并前规划备份与 `pg_upgrade` |
| CI 数据库镜像一致性校验 | `.github/workflows/deploy.yml` | 改 `compose.yml` 的数据库版本时，必须同步 `deploy.yml` 里两处 `image: postgres:*` |

本批无数据库迁移；API 契约不变。

## 2026.11.22 – 2026.11.23 批次（索引保留期 / 依赖 major / 运维韧性 / 自审+上游同步）

| 改进 | 主要文件 | 同步注意事项 |
|------|----------|--------------|
| 审计索引 + 保留期 | 迁移 `32f63b6790af`、`audit.py`、`config.py` | 跑迁移；`AUDIT_LOG_RETENTION_DAYS` 按合规要求配置（0=永久） |
| **react-table 8→9（破坏性）** | `columns.tsx`、`UsersPanel.tsx`、package.json | `tableFeatures({coreRowModelsFeature, coreRowModel: createCoreRowModel()})` 导出供 columns 泛型引用；`useTable({features,...})` 替代 `useReactTable`；无列隐藏需求用 `row.getAllCells()` |
| mailcatcher→mailpit | `compose.override.yml`、CI、README | 本地邮件 UI 端口 **1080→8025**（SMTP 1025 不变）；本地脚本/书签同步 |
| 前端错误监控（可选，自建 GlitchTip） | `main.tsx`、`ErrorComponent`、`lib/reportError.ts`、Dockerfile/compose | `VITE_SENTRY_DSN` 构建链路三点接线；Secrets 配 `SENTRY_DSN` 后生效；CSP `connect-src` 放行 `GLITCHTIP_ORIGIN`（envsubst 注入），不用 Sentry 云 |
| 备份告警闭环 | `scripts/install-backup-timer.sh`、`backup_restore.py` | 服务器执行安装脚本（dry-run 先预览）；restore 计数重试为静默增强 |
| email-null 防御、审计分批/tiebreaker/autoescape、Toaster 白屏兜底等自审修复 | 后端 `users/crud/audit`、前端 `main/ErrorComponent/toast` | 按文件 cherry-pick 即可；`DELETE /users/me` 审计时序变化不影响契约 |
| e2e 守卫 | `e2e/*.spec.ts` | skip 开关从 `E2E_SIGNUP_DISABLED` 改为读根 `.env` 的 `USERS_OPEN_REGISTRATION` |

自审修复中记录不做的项：审计双连接池占用（高并发项目调大 `DB_POOL_SIZE`/`DB_MAX_OVERFLOW`）；email 大小写变体唯一性（存量行为，需要时单独做函数索引迁移）。

## 2026.11.22 批次（运维与安全收尾）

| 改进 | 主要文件 | 同步注意事项 |
|------|----------|--------------|
| CSP 强制 + 哈希漂移守卫 | `frontend/nginx.conf`、`frontend/scripts/check-csp-hash.sh`、`.github/workflows/deploy.yml` | hash 基于构建产物字节；客户项目改过 index.html 主题脚本须重算（运行守卫脚本即得），CI 接入同款步骤 |
| 审计独立事务 | `backend/app/core/audit.py` | 直接整文件替换即可；调用方签名不变 |
| 连接池可配 + 优雅关闭 | `backend/app/core/db.py`、`config.py`、`main.py` | 已自定义池参数的项目按新配置项核对；lifespan 与已有启动逻辑合并时注意保留 dispose |
| 日志统一 | `backend/app/core/logging.py`、`main.py`、prestart 系列脚本 | 客户项目自有 basicConfig 可保留（幂等），建议统一到 configure_logging |
| 审计查看界面 | `backend/app/api/routes/audit.py`、`core/permissions.py`、`frontend/src/routes/_layout/admin/`、`AuditPanel`、`useAuditLogs`、`lib/toast.ts` | API 新增需 `npm run generate-client`；同步 `routeTree.gen.ts`；sonner 懒加载要求 toast 调用统一走 `lib/toast`（直接 import "sonner" 的调用会绕过队列） |

本批无数据库迁移；审计查看为新增 API。

## 2026.11.14 – 2026.11.21 批次（e2e 回归 / Refresh Cookie / P0-P2 维护）

详见 `CHANGELOG.md` 对应日期条目。同步要点：

- **Refresh Token HttpOnly Cookie（11.19，破坏性）**：后端 `login.py`、`core/sessions.py`、迁移与前端 `lib/session*`、`hooks/useAuth.ts` 必须同一批同步；只同步一侧会导致登录后无法刷新。
- **P1 安全语义（11.21）**：改邮箱/注销的密码复核是 API 契约变更，需 `npm run generate-client` 并同步前端表单；`UserDeleteMe` 经 DELETE body 传输。
- **P2 清债（11.21）**：播种对齐后，已有项目数据库中的旧"安慰剂"权限行可保留不动（不影响运行）；限流与分页边界为纯后端替换。
- e2e 扩到 14 用例且 webServer 需 `RATE_LIMIT_ENABLED=false`（全量套件同 IP 会触发 429），同步 `playwright.config.ts`。

## 2026.10.16 批次

| 改进 | 主要文件 | 同步注意事项 |
|------|----------|--------------|
| JWT 类型与重置链接一次性 | `backend/app/core/security.py`、`api/deps.py`、`utils.py`、`api/routes/login.py`、`models.py` | 三处签发/校验需一起同步；项目自建的其他 JWT 也应带上独立的 `typ` |
| 请求日志与 Request ID | `backend/app/main.py` | 依赖日志中原始路径的排查脚本改为匹配路由模板 |
| 管理员自我保护、Token 清理 | `backend/app/api/routes/users.py`、`core/sessions.py` | 项目若有其他删除用户的入口，同样调用 `delete_user_refresh_tokens` |
| 连接池、GlitchTip 采样 | `backend/app/core/db.py`、`main.py` | 需要全量追踪的项目调整 `SENTRY_TRACES_SAMPLE_RATE` |

本批无数据库迁移和 API 契约变更。升级后旧 Access Token 由前端自动刷新替换，旧重置密码链接需要重新申请。

## 2026.10.10 批次

| 改进 | 主要文件 | 同步注意事项 |
|------|----------|--------------|
| 会话事务/并发 | `backend/app/crud.py`、`api/routes/login.py`、`api/routes/users.py`、`models.py` | 密码更新统一撤销 Refresh Token；保留业务事务扩展 |
| 前端刷新 | `frontend/src/lib/session*.ts`、`hooks/useAuth.ts`、`main.tsx` | 配套同步，避免只有短 Token 而没有自动刷新；保留项目自己的错误反馈 |
| Access Token 默认值 | `backend/app/core/config.py` | 新签发 Token 默认 15 分钟；已签发 Token 保持原到期时间；已有环境配置可能覆盖默认值 |
| 数据库备份 | `scripts/backup_restore.py`、`scripts/test_backup_restore.py` | 纯 PostgreSQL 快照；接入其他文件存储需自行扩展 |
| CI/维护互斥 | `.github/workflows/deploy.yml`、`.gitignore` | 服务器需要 `flock`；备份与部署必须使用同一部署目录 |
| 开发规范 | `docs/module-development.md`、`.claude/commands/new-feature.md` | 保留客户额外规范 |

本批无新增数据库迁移和 API 契约变更。`models.py` 的角色名、权限编码唯一性声明与既有 `0002` 唯一索引对齐；历史上绕过 Alembic 建库的项目需要先检查重复值与索引，再生成适用的修复迁移。刷新采用锁机制，不改变表结构。支持 Web Locks 的浏览器可跨标签页协调；不支持时退回单标签页共享刷新。Token 仍存储在 localStorage，这批更新没有改成 Cookie 会话。

最低验证：后端 lint/独立库测试、前端 `npm run lint` / `npm test` / `npm run build`、`bash scripts/check-template.sh`、`python3 scripts/test_deploy.py`、`python3 scripts/test_backup_restore.py --integration`。恢复演练只使用临时 `app_test` 数据库。

## 最小模板功能收敛

当前版本移除了通用配置、文件、CSV 导入导出和后台任务接口，以及对应默认界面与客户端。已有客户项目若使用这些能力，应保留自身实现，不直接删除。遗留的文件表由迁移 `0007` 清理，模板不再挂载附件 volume；认证、可配置角色权限和内部审计继续保留。

角色权限复用既有 role/permission 关联表，无表结构变更。部署前置初始化会补充缺失的权限项和默认访客角色，不覆盖已配置的权限。未分配角色的普通账号使用访客策略，显式分配的多个角色取权限并集。
