# AI Development Guidelines & Coding Standards

This project is a Full Stack application using **FastAPI** (Backend) and **React + Vite** (Frontend).
Follow these guidelines to ensure code stability, consistency, and maintainability.

## 1. Technology Stack

### Backend (`/backend`)
- **Framework**: FastAPI (Python 3.10+)
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Database**: PostgreSQL (via Docker)
- **Package Manager**: uv
- **Linting**: Ruff (strict adherence required)
- **Type Checking**: MyPy (strict mode)

### Frontend (`/frontend`)
- **Framework**: React 19
- **Build Tool**: Vite
- **Language**: TypeScript
- **Styling**: TailwindCSS v4
- **State/Data**: TanStack Query (React Query)
- **Routing**: TanStack Router
- **UI Components**: Radix UI + Lucide React (Icons)
- **Linting/Formatting**: Biome

## 2. Coding Conventions

### General
- **Naming**:
  - Python: `snake_case` for variables/functions, `PascalCase` for classes.
  - TypeScript: `camelCase` for variables/functions, `PascalCase` for components/interfaces.
  - Files:
    - Python: `snake_case.py`
    - TypeScript: `kebab-case.ts` (utils/hooks) or `PascalCase.tsx` (components).
- **Comments**: Write clear, concise comments for complex logic. Avoid stating the obvious.

### Backend (Python)
- **Type Hints**: Always use Python type hints.
  - `def get_user(id: uuid.UUID) -> User:`
- **Pydantic**: Use Pydantic models for all API Request/Response schemas.
- **Async**: Use `async def` for all route handlers and database operations.
- **Error Handling**: Use `HTTPException` for API errors. Do not return raw dictionaries for errors.

### Frontend (TypeScript/React)
- **Components**: Use Functional Components with Hooks.
- **Strict Mode**: Do not use `any`. Define proper Interfaces or Types.
- **Styles**: Use Tailwind utility classes. Avoid inline `style={{}}` unless dynamic.
- **Fetching**: Use custom hooks wrapping `useQuery` / `useMutation` for API interactions.
- **Imports**: Use absolute imports (e.g., `@/components/...`) where possible.

## 3. Deployment & Infrastructure

- **Compose**: `compose.yml` is production. `compose.override.yml` is local dev (auto-applied).
- **API Routing**: nginx proxies `/api`, `/docs`, `/redoc` to the `backend` container. `VITE_API_URL` is empty in production (relative URLs).
- **Local Dev**: `VITE_API_URL=http://localhost:8000` in override so frontend calls backend directly.
- **Credentials**: This is a private repository. Database passwords and secret keys can be hardcoded in `.env` for convenience.
- **Deploy**: Server-side git pull + `docker compose up -d --build`. See `.github/workflows/deploy.yml`.

## 4. Workflow & Best Practices

- **Modularity**: Keep components small and focused. One component per file is preferred.
- **Validation**: Validate all inputs at the API boundary (Pydantic).
- **Testing**: Write unit tests for critical utility functions in `backend/app/tests/`.

## 5. 前后端联动规范

- 后端改了模型或接口后，必须重新生成前端客户端：`cd frontend && bun run generate-client`
- 前端不允许手写 API 请求 URL 字符串，统一用 `client/` 目录下的生成代码
- 数据库模型变更后必须生成 Alembic 迁移文件，不允许直接改数据库

## 6. Forbidden Patterns

- No `print()` in production code — use `logging`.
- No circular imports — structure modules to avoid dependency cycles.
- No direct DOM manipulation in React — use refs if absolutely necessary.
- No magic numbers — use named constants.
- No `any` in TypeScript.
