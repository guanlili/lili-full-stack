# AI Development Guidelines & Coding Standards

This project is a Full Stack application using **FastAPI** (Backend) and **React + Vite** (Frontend).
Follow these guidelines to ensure code stability, consistency, and maintainability.

## 1. Technology Stack

### Backend (`/backend`)
- **Framework**: FastAPI (Python 3.10+)
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Database**: PostgreSQL (via Docker)
- **Package Manager**: uv
- **Linting**: Ruff (Strict adherence required)
- **Type Checking**: MyPy (Strict mode)

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
- **Type Hints**: ALways use Python type hints.
  - ❌ `def get_user(id):`
  - ✅ `def get_user(id: uuid.UUID) -> User:`
- **Pydantic**: Use Pydantic models for all API Request/Response schemas.
- **Async**: Use `async def` for all route handlers and database operations.
- **Error Handling**: Use `HTTPException` for API errors. Do not return raw dictionaries for errors.

### Frontend (TypeScript/React)
- **Components**: Use Functional Components with Hooks.
- **Strict Mode**: Do not use `any`. Define proper Interfaces or Types.
- **Styles**: Use Tailwind utility classes. Avoid inline `style={{}}` unless dynamic.
- **Fetching**: Use custom hooks wrapping `useQuery` / `useMutation` for API interactions.
- **Imports**: Use absolute imports (e.g., `@/components/...`) where possible.

## 3. Workflow & Best Practices

- **Modularity**: Keep components small and focused. One component per file is preferred.
- **Validation**: Validate all inputs at the API boundary (Pydantic).
- **Environment**: Use `.env` files for configuration. NEVER hardcode secrets.
- **Testing**: Ensure code is testable. Write unit tests for utility functions.

## 4. Forbidden Patterns

- ❌ **No `print()` in production code**: Use `logging` or a logger instance.
- ❌ **No circular imports**: Structure modules to avoid dependency cycles.
- ❌ **No direct DOM manipulation**: Use Refs if absolutely necessary, but prefer React state.
- ❌ **No magic numbers**: usage constants with descriptive names.
