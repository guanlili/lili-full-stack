# 升级依赖包

定期维护任务，将后端 Python 包和前端 npm 包升级到最新版本。

## 执行步骤

1. **升级后端依赖**：
   ```bash
   cd backend && uv lock --upgrade
   ```
   检查 `backend/uv.lock` 的变更，关注主要包（fastapi、sqlmodel、pydantic）的版本变化

2. **升级前端依赖**：
   ```bash
   cd frontend && bun update
   ```
   检查 `frontend/package.json` 的版本变化

3. **验证后端正常启动**：
   ```bash
   docker compose up --build backend
   ```
   确认没有 import 错误或启动报错

4. **验证前端正常构建**：
   ```bash
   docker compose up --build frontend
   ```

5. 如有报错，查看具体包的 changelog，按需调整代码

6. 一切正常后提交：
   ```bash
   git add uv.lock backend/uv.lock frontend/package.json frontend/bun.lock
   git commit -m "chore: upgrade dependencies"
   ```
