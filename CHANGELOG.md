# 模板更新记录

版本用于标记模板维护批次，不代表客户项目的业务版本。

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
