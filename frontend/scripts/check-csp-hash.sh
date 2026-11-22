#!/usr/bin/env bash
# 校验 nginx CSP 放行的内联脚本 sha256 与构建产物一致：
# 改动 frontend/index.html 主题脚本后忘记同步 nginx.conf 时，这里拦下（CI 执行）。
# 全量双向比对：产物里每个无属性内联脚本都必须有对应 hash，nginx 里不能有多余 hash。
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f dist/index.html ]; then
  echo "❌ dist/index.html 不存在，请先 npm run build" >&2
  exit 1
fi

hashes_in_nginx=$(grep -o "sha256-[A-Za-z0-9+/=]*" nginx.conf | sort -u)
if [ -z "$hashes_in_nginx" ]; then
  echo "❌ nginx.conf 未配置内联脚本 sha256" >&2
  exit 1
fi

diff_output=$(
  diff <(printf '%s\n' "$hashes_in_nginx") <(
    node -e '
      const fs = require("fs");
      const crypto = require("crypto");
      const html = fs.readFileSync("dist/index.html", "utf8");
      // 只匹配无属性的裸 <script>（内联脚本）；带 src/type 等属性的动态导入不受 CSP hash 约束
      const scripts = html.match(/<script>([\s\S]*?)<\/script>/g) ?? [];
      const hashes = scripts.map((block) => {
        const content = block.replace(/^<script>/, "").replace(/<\/script>$/, "");
        // 浏览器计算 CSP 哈希前会剥离内联脚本首尾空白
        return "sha256-" + crypto.createHash("sha256")
          .update(content.replace(/^\s+|\s+$/g, "")).digest("base64");
      });
      if (!hashes.length) { process.exit(1); }
      console.log(hashes.sort().join("\n"));
    ' || { echo "❌ 无法从 dist/index.html 提取内联脚本" >&2; exit 1; }
  )
)

if [ -n "$diff_output" ]; then
  echo "❌ CSP 哈希集合与构建产物不一致（< 为 nginx.conf，> 为实际产物）：" >&2
  printf '%s\n' "$diff_output" >&2
  echo "   修改 frontend/index.html 主题脚本后需重算并更新 nginx.conf" >&2
  exit 1
fi
echo "✅ CSP 内联脚本哈希与构建产物一致"
