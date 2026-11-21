#!/usr/bin/env bash
# 校验 nginx CSP 放行的内联脚本 sha256 与构建产物一致：
# 改动 frontend/index.html 主题脚本后忘记同步 nginx.conf 时，这里拦下（CI 执行）。
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f dist/index.html ]; then
  echo "❌ dist/index.html 不存在，请先 npm run build" >&2
  exit 1
fi

hash_in_nginx=$(sed -n 's/.*sha256-\([A-Za-z0-9\/+=]*\).*/\1/p' nginx.conf | head -1)
if [ -z "$hash_in_nginx" ]; then
  echo "❌ nginx.conf 未配置内联脚本 sha256" >&2
  exit 1
fi

actual=$(
  node -e '
    const fs = require("fs");
    const crypto = require("crypto");
    const m = fs.readFileSync("dist/index.html", "utf8").match(/<script>([\s\S]*?)<\/script>/);
    if (!m) { process.exit(1); }
    // 浏览器计算 CSP 哈希前会剥离内联脚本首尾空白
    console.log(crypto.createHash("sha256").update(m[1].replace(/^\s+|\s+$/g, "")).digest("base64"));
  '
)

if [ "$hash_in_nginx" != "$actual" ]; then
  echo "❌ CSP 哈希不一致：nginx.conf=sha256-$hash_in_nginx 实际=sha256-$actual" >&2
  echo "   修改 frontend/index.html 主题脚本后需按 scripts/check-csp-hash.sh 顶部说明重算并更新 nginx.conf" >&2
  exit 1
fi
echo "✅ CSP 内联脚本哈希与构建产物一致"
