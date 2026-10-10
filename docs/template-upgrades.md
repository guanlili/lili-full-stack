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

## 2026.10.10 批次

| 改进 | 主要文件 | 同步注意事项 |
|------|----------|--------------|
| 会话事务/并发 | `backend/app/crud.py`、`api/routes/login.py`、`api/routes/users.py`、`models.py` | 密码更新统一撤销 Refresh Token；保留业务事务扩展 |
| 前端刷新 | `frontend/src/lib/session*.ts`、`hooks/useAuth.ts`、`main.tsx` | 配套同步，避免只有短 Token 而没有自动刷新；保留项目自己的错误反馈 |
| Access Token 默认值 | `backend/app/core/config.py` | 新签发 Token 默认 15 分钟；已签发 Token 保持原到期时间；已有环境配置可能覆盖默认值 |
| 导出体验 | `hooks/useUserExport.ts`、`components/Admin/PlatformTools.tsx` | 适配项目实际管理页面；CSV 下载复用生成客户端 |
| 联合备份 | `scripts/backup_restore.py`、`scripts/test_backup_restore.py` | 当前针对平铺本地附件目录；其他文件存储需适配 |
| CI/维护互斥 | `.github/workflows/deploy.yml`、`.gitignore` | 服务器需要 `flock`；备份与部署必须使用同一部署目录 |
| 开发规范 | `docs/module-development.md`、`.claude/commands/new-feature.md` | 保留客户额外规范 |

本批无新增数据库迁移和 API 契约变更。`models.py` 的角色名、权限编码唯一性声明与既有 `0002` 唯一索引对齐；历史上绕过 Alembic 建库的项目需要先检查重复值与索引，再生成适用的修复迁移。刷新采用锁机制，不改变表结构。支持 Web Locks 的浏览器可跨标签页协调；不支持时退回单标签页共享刷新。Token 仍存储在 localStorage，这批更新没有改成 Cookie 会话。

最低验证：后端 lint/独立库测试、前端 `npm run lint` / `npm test` / `npm run build`、`bash scripts/check-template.sh`、`python3 scripts/test_deploy.py`、`python3 scripts/test_backup_restore.py --integration`。恢复演练只使用临时 `app_test` 数据库。
