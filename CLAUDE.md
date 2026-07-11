# CLAUDE.md — 项目规范

> 这是 lili-full-stack 模板项目。每个基于本模板的新项目都应更新本文件，写入该项目的业务背景和数据模型。

## 项目结构

```
backend/app/
├── api/routes/     # FastAPI 路由（每个业务模块一个文件）
├── core/           # 配置、安全、数据库连接
├── models.py       # SQLModel 数据模型（数据库表结构）
├── crud.py         # 数据库增删改查操作
└── main.py         # 应用入口

frontend/src/
├── routes/         # TanStack Router 页面（_layout/ 下是需要登录的页面）
├── components/     # 可复用组件
├── hooks/          # 自定义 hooks（封装 useQuery/useMutation）
└── client/         # 自动生成的 API 客户端（不要手动修改）
```

## 本地开发

```bash
docker compose up --build   # 首次启动
docker compose watch        # 启用热更新
docker compose down         # 停止
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| API 文档 | http://localhost:8000/docs |
| 数据库管理 | http://localhost:8081 |
| 邮件测试 | http://localhost:1080 |

## 开发新功能的标准流程

1. **后端**：在 `models.py` 加数据模型 → 在 `crud.py` 加增删改查 → 在 `api/routes/` 加新路由文件 → 在 `api/main.py` 注册路由
2. **数据库迁移**：`docker compose exec backend alembic revision --autogenerate -m "add xxx"` → `alembic upgrade head`
3. **前端 API 客户端**：后端改完后重新生成 → `cd frontend && bun run generate-client`
4. **前端页面**：在 `routes/_layout/` 加新页面，在 `_layout.tsx` 加导航链接

## 示例代码说明

`backend/app/api/routes/items.py` 和 `frontend/src/routes/_layout/items.tsx` 是 CRUD 功能的完整示例，展示了标准的开发模式。开始新功能时可以参考，最终交付前删除。

## 技术规范

详见 `AI_RULES.md`。
