#!/usr/bin/env bash
# 检查模板的结构性约束，避免复制到新项目后带入样例、坏脚本或不可解析的 Compose 配置。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  ".env.example"
  "AGENTS.md"
  "AI_RULES.md"
  "CLAUDE.md"
  "PROJECT_CONTEXT.md"
  "compose.yml"
  "compose.override.yml"
  "docs/deployment.md"
  "docs/module-development.md"
  "docs/template-upgrades.md"
  "CHANGELOG.md"
  "scripts/backup_restore.py"
  "scripts/test_backup_restore.py"
  "frontend/package.json"
  "frontend/package-lock.json"
)

for file in "${required_files[@]}"; do
  if [ ! -f "$file" ]; then
    echo "❌ 缺少必需文件：$file" >&2
    exit 1
  fi
done

if ! git check-ignore -q .env; then
  echo "❌ .env 未被 .gitignore 忽略，禁止把本地配置带入提交。" >&2
  exit 1
fi

for script in scripts/*.sh backend/scripts/*.sh frontend/scripts/*.sh; do
  bash -n "$script"
done

if git grep -n -E 'backend/app/api/routes/items\.py|frontend/src/routes/_layout/items\.tsx|ItemsService|class Item(Base|Create|Public|Update)|test_items' -- . ':!scripts/check-template.sh'; then
  echo "❌ 检测到模板业务示例残留，请删除后再交付。" >&2
  exit 1
fi

COMPOSE_ENV_FILE=.env.example docker compose --env-file .env.example -f compose.yml config --quiet
# OpenAPI 生成器会在 src/client/ 的空行保留缩进空格；该目录由生成器管理，
# 其契约一致性由 CI 的 openapi-ts 漂移检查负责。手写源码仍全部检查。
git diff --check -- ':!frontend/src/client/'

echo "✅ 模板完整性检查通过"
