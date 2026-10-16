#!/usr/bin/env bash
# 新项目初始化；拒绝覆盖现有 .env，不打印生成的密钥。
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "$#" -eq 0 ]; then
  read -r -p '项目显示名: ' project_name
  set -- "$project_name"
fi
exec python3 scripts/init_project.py "$@"
