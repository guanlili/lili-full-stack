# 模板更新记录

版本用于标记模板维护批次，不代表客户项目的业务版本。

## 2026.11.23 — 自审轮修复与上游同步：react-table 9 / Mailpit（#92–#94）

- 对 11 轮自研代码做三路无上下文审查（后端/前端/基建子代理 + 移动端暗色 DOM 度量），修复 26 项测试覆盖不到的缺陷。要点：**SENTRY_DSN 从未接入部署通道**（deploy.yml env 块缺失 + 生成脚本无条件清空，"自动复用"实为死配置）；强制 CSP `connect-src` 缺 Sentry ingest 域；懒 Toaster chunk 失败会卸载整棵 React 树白屏（补 .catch 降级 + ErrorBoundary + `vite:preloadError` 整页重载）；`PATCH {"email": null}` 撞 NOT NULL 500（me/admin 两路径）；审计保留期首次大删除改分批（20×5000）；审计/用户排序补 id tiebreaker；icontains 补 autoescape；注销审计移到删除 commit 后；signup 补审计；login.failed email 截断；注销对话框密码不清空；settings 加载失败永久骨架改错误态+重试；e2e 死开关 `E2E_SIGNUP_DISABLED` 换真实 `USERS_OPEN_REGISTRATION`；check-csp-hash 升级全量双向比对；backup-timer ExecStart 改生成 runner 脚本（空格路径安全）。
- **react-table 8→9**（上游 #2509 配方）：`tableFeatures({coreRowModelsFeature, coreRowModel: createCoreRowModel()})` + `useTable({features,...})`，`ColumnDef<Features, TData>` 泛形变化；`getVisibleCells` 挪进 column-visibility feature，不用列隐藏直接 `getAllCells()`。
- **mailcatcher→mailpit**（前者已停更）：本地邮件查看端口 **1080→8025**（SMTP 1025 不变），compose.override 与 CI 同步。
- 部署清理回退全局 `docker image prune`（服务器 compose 版本无项目级子命令，#93 部署尾步挂、#94 修复；本体部署与冒烟未受影响）。
- 上游 169 commits 评审，其余不抄项已记录（Sonner 主题修复与我们方案收敛、竞态修法弱于本仓、DATABASE_URL 大重构等设计分歧）。

数据库：无表结构变更。API：契约不变（email null 语义从 500 变为忽略）。兼容性：**前端依赖 major**（react-table 9 需按 template-upgrades 配方同步 columns/表格组件）；本地邮件端口变化。

## 2026.11.22 — 运维韧性：备份告警闭环 / 前端 Sentry / devledger 激活（#90/#91）

- `scripts/install-backup-timer.sh`：服务器一键安装 systemd timer（每日错峰 ≤30 分钟、`Persistent` 关机补跑），healthchecks 双向 ping（成功/失败 + timer 静默失效由对方超时告警兜底）；`--dry-run` 无 root 预览；deployment.md 以此替换手工 cron 示例。
- 备份恢复测试竞态根治：restore 空库计数改容器内 30 秒重试（此前 CI 偶发 psql 撞启动窗口需 rerun）。
- 前端 Sentry（可选）：`@sentry/react` 异步 init 不进首屏；`VITE_SENTRY_DSN` 经 compose build arg → Dockerfile ARG 注入，生产复用 `SENTRY_DSN`；ErrorComponent 懒上报。**启用需在 Secrets 配置 SENTRY_DSN**。
- devledger 激活本仓库：Project #25 建项，CLAUDE.md/issue 模板占位符替换，AI 会话记账闭环。
- 截图刷新工具：`CAPTURE_SCREENSHOTS=1 npx playwright test capture-screenshots`（CI 默认 skip），四张基线图刷新 + 新增审计页。

数据库/API：无变更。兼容性：无破坏性；Secrets 增加 `SENTRY_DSN`（可选）。

## 2026.11.22 — 前端依赖 major 批次与 e2e 竞态修复（#86）

- @types/node 25→26、@hookform/resolvers 5→7（zod 4.6 兼容）。
- **TypeScript 7 评估后回退 5.9**：`@hey-api/openapi-ts` 在 TS7 崩溃（`ts.SyntaxKind.AnyKeyword` 已移除）阻塞客户端生成链——本地 build 全绿、CI 漂移检查暴露。tsconfig 保留清理（移除已废弃 `baseUrl`、显式 `types:["node"]`）为 TS7 铺路。
- react-table 9 当时暂缓（后于 11.23 批次完成）；fastapi pyproject floor 提升（#73，lock 早已在位）。
- access.spec 冷启动竞态修复：注册跳转后表单重挂载吞掉 fill 值（单跑能过、全量必挂），fill+校验整体重试。

兼容性：无 API 变更。

## 2026.11.22 — 审计表时间索引与保留期（#85）

- 迁移 `32f63b6790af`：`ix_audit_log_created_at`（审计查看按时间倒序分页的排序键，表增长后不再全表排序）。
- `AUDIT_LOG_RETENTION_DAYS`（默认 0=永久）：配置后超管查看审计时读路径顺带清理过期行（分批删除，不占写路径、无需调度器）；env 键同步 `.env.example` 与 `generate-deploy-env.sh`。

数据库：**新增迁移**（索引 only，upgrade/downgrade 对称）。API：不变。

## 2026.11.22 — 审计日志查看界面与前端打磨（#82/#83）

- 新增超管专用审计查看：`GET /api/v1/audit-logs`（分页 + 动作模糊/操作者/资源类型过滤，时间倒序，附操作者邮箱——账号删除后显示"已删除用户"）；前端 `/admin/audit` 页面（防抖过滤、分页、加载/错误态），注册进 PAGES（`audit.view`，admin_only）后侧边栏自动可见。内部审计从"只写不读"补齐为可运营。
- sonner 懒加载：Toaster 由 main.tsx lazy 挂载，41KB 运行时移出首屏 modulepreload；`lib/toast` 队列兜底保证挂载前的 toast 不丢（含单测），`useCustomToast`/queryClient 全部改走队列。
- AddUser/EditUser 密码框统一换 `PasswordInput`（明文切换）；settings 加载骨架屏；roles 页 `key` hack 改 useEffect 同步。
- 路由结构：`routes/_layout/admin/` 改目录式布局（index + audit 平级），修复点号命名下 `/admin/audit` 被嵌为 `/admin` 子路由而无处渲染的问题。

数据库：无表结构变更。API：**新增** `GET /api/v1/audit-logs`（超管），需重新生成客户端。兼容性：无破坏性变更。

## 2026.11.22 — 运维与安全收尾

- CSP 从 Report-Only 转强制：唯一放行的内联脚本是 index.html 主题防闪白脚本，以构建产物字节计算 sha256 写入 nginx；新增 `frontend/scripts/check-csp-hash.sh` 并接入 CI，改主题脚本未同步 hash 时构建拦截。
- 审计写入改独立事务：`record_audit` 用调用方 Session 的同一 bind 新开连接提交，审计失败不再回滚业务写入（也修复了失败路径误 rollback 调用方事务的隐患）。
- 数据库连接池参数可配（`DB_POOL_SIZE` / `DB_MAX_OVERFLOW` / `DB_POOL_RECYCLE`，默认 5/10/1800）；FastAPI lifespan 关停时 `engine.dispose()` 归还连接。
- 日志统一入口 `configure_logging()`（时间戳/级别/logger 名格式），移除 5 处散落的 `logging.basicConfig`；独立脚本（prestart 系列）调用同一入口。

数据库：无表结构变更，无需迁移。API：请求/响应契约不变，无需重新生成客户端。兼容性：自定义过连接池的项目按新配置项核对；审计行为变化仅在异常路径。

## 2026.11.21 — 模板三批维护：初始化修复 / P1 安全语义 / P2 清债

- 初始化修复（#74/#75）：`init_project.py` 补 `subprocess` import；未装 devledger 的机器上 `pm_script=None` 直接 isfile 会 TypeError，均已修复；`main()` 增加真实入口冒烟回归堵住 CI 只测 `initialize()` 的盲区。
- P1 安全语义（#76/#77）：
  - refresh cookie 的 `Path` 放宽到 `/login` 前缀（原来限定 `/login/refresh` 时 logout 收不到 cookie）；logout 按哈希吊销服务端 refresh token 并写 `session.logout` 审计；
  - 改绑邮箱（`UserUpdateMe.current_password`）与自助注销（`UserDeleteMe` body）强制密码复核，补 `user.self_updated` / `user.self_deleted` 审计（注销审计先于删行落库）；
  - 非 local 环境不挂载 `/docs` `/redoc` `/openapi.json`；nginx 增加 CSP（先 Report-Only）；
  - e2e 从 6 用例扩到 14（新增 admin-users / roles / 密码找回 / settings 四主线）；playwright 后端 webServer 关限流防全量套件触发 429。
- P2 清债（#78/#79）：`/login/refresh`（30/min）与 `/users/signup`（5/min）补限流；`read_roles` 聚合查询消 N+1；播种对齐 PAGES 注册表（移除 `users.read` 等"安慰剂"权限与装饰性 admin 角色）；`read_users` 分页边界（skip≥0、1≤limit≤200）；CI 加固（GITHUB_TOKEN 最小权限、job 超时、Chromium 缓存、e2e 失败 artifact、服务器镜像按 sha 清理旧 tag）；README/deployment.md 文档漂移 6 处修正；删除零引用死代码（前端 6 文件约 640 行 + `AuditLogPublic` 死 schema）；`logoutAll` 兜底、错误页翻译文案。

数据库：无表结构变更。API：**有契约变更**——`UserUpdateMe` 新增可选 `current_password`、`DELETE /users/me` 新增必填 body、`GET /users` 分页参数加边界校验，需重新生成客户端并同步前端调用。兼容性：旧前端调用改邮箱/注销接口会收到 400/422；生产环境 `/docs` 不再可访问。

## 2026.11.19 — Refresh Token 改 HttpOnly Cookie（#68）

- refresh token 只经 HttpOnly Cookie 下发（`Path` 限定刷新端点、`SameSite=Lax`），响应体不再携带；access token 保留 15 分钟短命走 Authorization header，前端拦截器防回放机制零改动。
- 新增 `/login/logout` 清 cookie、`/login/logout-all` 吊销全部会话；XSS 无法窃取长命凭据。

数据库：`refresh_token` 表增加哈希列与吊销时间（随迁移交付）。API：登录响应体不再返回 `refresh_token` 字段。兼容性：**破坏性变更**，前端必须同步升级（配套的会话刷新拦截器一并发布）。

## 2026.11.14 — Playwright e2e 回归（#67）

- 恢复 Playwright e2e：登录/注册/权限重定向/登出 6 用例，webServer 起 uvicorn+vite 全真栈；CI e2e job 纳入部署门槛。浏览器把 localhost 解析为 ::1，e2e 全链路统一 127.0.0.1。

数据库/API：无变更。

## 2026.11.11 — README 项目化标准与 devledger 路径修复

- 修复 `init_project.py` 检测 devledger 只认 `~/devledger` 旧路径的问题：改为 `~/.agents/skills/devledger`（标准安装路径）优先、旧路径兜底，安装提示同步更新；此前走标准安装的机器上自动接入静默失效。
- `CLAUDE.md` 中三处 `~/devledger` 引用统一为 `~/.agents/skills/devledger`。
- 新增 `docs/readme-template.md`：项目 README 骨架（一句定位 / 📌 项目信息表必填：对接人可多行 / 截图 / 双路径本地开发 / 阶段叙事版本史），「开启新项目」第三步引用。
- 新增 Claude 命令 `/init-project`：AI 一轮提问收集项目名/对接人/端口等 → 一次成参执行初始化 → 自动完成 PROJECT_CONTEXT 填写、README 项目化、AGENTS.md 对接人行与冒烟验证，用户主动输入降到「回答一轮问题」。
- `check-template.sh` 新增 README 项目化检查：新项目 README 仍是模板原文（含「本仓库是模板仓库」标记）则交付检查失败，模板本体按 remote 豁免。
- README 补强：项目信息表（维护/定位/基座/项目管理 devledger/许可）、开箱基线小节、界面截图、冒烟检查、与 CI 同口径的测试命令、交付三件套；修复重复段落。

兼容性：已有项目无需动作；若本机 devledger 装在 `~/devledger` 继续可用，建议逐步迁移到标准路径。

## 2026.10.16 — 认证加固

- JWT 增加 `typ` 类型声明：密码重置链接不能当 Access Token 使用，Access Token 也不能用于重置密码。缺少 `typ`/`ver` 或 `sub` 不是 UUID 的令牌统一返回 401（此前部分情况返回 500）。
- 密码重置链接绑定 `token_version`，成功重置、修改密码或“退出所有设备”后旧链接立即失效；同一链接并发提交只会成功一次。
- 修复默认中文项目名下 `password-recovery-html-content` 接口必定 500 的问题（非法响应头）。
- 请求日志记录路由模板（如 `/password-recovery/{email}`），邮箱等路径参数不再写入应用日志；客户端传入的 `X-Request-ID` 只接受 64 位以内的安全字符，否则重新生成。
- 管理员不能通过用户编辑接口取消自己的管理员身份或停用自己，避免误操作锁死后台。
- 登录/刷新时清理该用户已过期的 Refresh Token；删除用户时一并删除其 Refresh Token。
- 数据库连接池启用 `pool_pre_ping`，数据库重启后不再让第一个复用旧连接的请求失败。
- Sentry 改用 `traces_sample_rate`（10% 采样），替换已弃用的 `enable_tracing`（原为 100% 采样）。

数据库：无表结构变更，无需迁移。API：请求/响应契约不变，无需重新生成客户端。兼容性：升级前签发的 Access Token 因缺少 `typ` 会被拒绝，前端会用 Refresh Token 自动换新，用户无感；升级前发出的重置密码邮件链接失效，需要重新申请。

## 2026.10.10 — 会话与交付完善

- 密码更新与 Refresh Token 撤销在同一事务提交；刷新时按用户、Token 顺序加锁，阻止并发重复消费。
- 前端共享刷新、原请求重试和会话切换保护；支持 Web Locks 的浏览器在标签页间串行刷新。刷新凭证失效时清理会话，临时网络/服务端错误保留会话。
- 默认 Access Token 从 8 天调整为 15 分钟，Refresh Token 保持 30 天。自定义过期时间的客户项目应核对实际配置。
- 用户导出提供 CSV 下载、终态停止轮询和失败提示。
- 数据库与附件联合备份、校验、空环境恢复，以及部署/维护共用文件锁。CI 运行隔离恢复演练、迁移漂移检查与前端会话测试。
- 新增业务模块交付清单和模板同步说明。

数据库：角色名、权限编码的 ORM 唯一性声明与既有 `0002` 迁移对齐；自动生成迁移检查无数据库操作，不提交空迁移。API：请求/响应契约不变，无需重新生成客户端。

同步步骤与验证见 [模板升级说明](docs/template-upgrades.md)。
