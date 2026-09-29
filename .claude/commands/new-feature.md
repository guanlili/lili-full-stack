# 新建功能模块

根据当前项目的 `PROJECT_CONTEXT.md` 和现有代码，设计并实现一个完整功能模块。

## 参数

$ARGUMENTS — 功能名称或需求描述，例如 `订单管理`、`客户可以导出报表`。

## 执行原则

不要假设项目一定使用某个示例实体、字段或页面。先检查现有模型、路由、权限、前端导航和测试，再决定新增或复用哪些代码。

## 执行步骤

1. **确认需求边界**：明确用户角色、核心流程、权限、数据关系和验收条件；需求不明确时先列出假设。
2. **设计数据模型**：如有数据库变化，更新 `backend/app/models.py`，同时补充对应的 Pydantic 请求/响应模型。
3. **实现后端**：在 `backend/app/crud.py` 和 `backend/app/api/routes/` 中实现业务逻辑和 API，并在 `backend/app/api/main.py` 注册路由。
4. **生成迁移**：只有数据库模型发生变化时才生成 Alembic 迁移；检查迁移内容后再应用。
5. **编写测试**：覆盖成功路径、输入校验、未登录、权限不足、资源不存在和关键边界条件。使用项目统一的独立测试库流程。
6. **同步客户端**：API 请求或响应契约变化后运行：
   ```bash
   cd frontend && npm run generate-client
   ```
7. **实现前端**：在 `frontend/src/routes/`、`frontend/src/components/` 和 `frontend/src/hooks/` 中按现有模式实现页面和数据请求。
8. **更新导航**：需要出现在侧边栏时，修改 `frontend/src/components/Sidebar/AppSidebar.tsx`；不要手动修改自动生成的路由树。
9. **验证**：运行后端 lint/测试、`cd frontend && npm run lint && npm run build`，并检查生成客户端的变更。

## 交付说明

完成后列出修改文件、数据库迁移、API 客户端生成结果、测试命令和仍需用户确认的事项。不要自动提交、推送或执行破坏性数据库操作。
