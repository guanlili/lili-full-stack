#!/usr/bin/env bash
# 安装（或预览）数据库定时备份的 systemd timer，并可选接入 healthchecks 类
# 死人开关告警：成功 ping <url>，失败 ping <url>/fail——timer 静默坏掉时对方也会
# 因"长时间无 ping"告警。在服务器部署目录内运行。
#
# 用法：
#   sudo bash scripts/install-backup-timer.sh \
#     --backups-dir /srv/backups/myproject \
#     [--healthchecks-url https://hc-ping.com/<uuid>] \
#     [--schedule 03:00] [--dry-run]
#
# --dry-run：只打印将安装的 unit 文件与命令，不写系统、不需要 root。

set -euo pipefail

# POSIX sh 单引号安全包裹：值里的 ' 转成 '\''
single_quote() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUPS_DIR="${ROOT_DIR}/backups"
HEALTHCHECKS_URL=""
SCHEDULE="03:00"
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --backups-dir) BACKUPS_DIR="${2:?}" ; shift 2 ;;
    --healthchecks-url) HEALTHCHECKS_URL="${2:?}" ; shift 2 ;;
    --schedule) SCHEDULE="${2:?}" ; shift 2 ;;
    --dry-run) DRY_RUN=1 ; shift ;;
    *) echo "未知参数：$1" >&2 ; exit 2 ;;
  esac
done

if ! printf '%s' "$SCHEDULE" | grep -Eq '^([01][0-9]|2[0-3]):[0-5][0-9]$'; then
  echo "❌ --schedule 需为 HH:MM（24 小时制）" >&2
  exit 2
fi
if [ -n "$HEALTHCHECKS_URL" ]; then
  case "$HEALTHCHECKS_URL" in
    http://*|https://*) : ;;
    *) echo "❌ --healthchecks-url 需以 http(s):// 开头" >&2 ; exit 2 ;;
  esac
fi

# unit 名用 Compose 项目标识（与 .env COMPOSE_PROJECT_NAME 一致），保持服务器多项目唯一
PROJECT_NAME=""
if [ -f "$ROOT_DIR/.env" ]; then
  PROJECT_NAME="$(sed -n 's/^COMPOSE_PROJECT_NAME="\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' "$ROOT_DIR/.env" | head -1)"
fi
[ -n "$PROJECT_NAME" ] || PROJECT_NAME="$(basename "$ROOT_DIR")"
UNIT_NAME="backup-$(printf '%s' "$PROJECT_NAME" | tr -c 'a-zA-Z0-9-' '-')"

# 生成 runner 脚本内容：ExecStart 只带一个加引号的路径参数（systemd 按自身
# 规则分词），路径含空格也安全——不手工拼 /bin/sh -c 的双层引号（那会在空格/引号/
# $ 上碎掉）。dry-run 只打印；真实安装时幂等覆盖写入 scripts/run-backup.sh。
RUNNER="$ROOT_DIR/scripts/run-backup.sh"
RUNNER_CONTENT="$(
  printf '#!/bin/sh\n'
  printf '# 由 install-backup-timer.sh 生成（幂等覆盖）：systemd timer 的执行体，勿手改\n'
  printf 'set -eu\n'
  printf 'if python3 %s backup %s --project-dir %s; then\n' \
    "$(single_quote "$ROOT_DIR/scripts/backup_restore.py")" \
    "$(single_quote "$BACKUPS_DIR")" \
    "$(single_quote "$ROOT_DIR")"
  if [ -n "$HEALTHCHECKS_URL" ]; then
    printf '  curl -fsS --retry 3 --max-time 30 %s\n' "$(single_quote "$HEALTHCHECKS_URL")"
    printf 'else\n'
    printf '  curl -fsS --retry 3 --max-time 30 %s || true\n' "$(single_quote "$HEALTHCHECKS_URL/fail")"
    printf '  exit 1\n'
  else
    printf 'else\n'
    printf '  exit 1\n'
  fi
  printf 'fi\n'
)"

# systemd 里 % 是特殊字符，转义为 %%
EXEC_START="'$(printf '%s' "$RUNNER" | sed "s/'/'\\\\''/g; s/%/%%/g")'"

SERVICE_UNIT="[Unit]
Description=Database backup for $PROJECT_NAME

[Service]
Type=oneshot
# 备份内部经 .maintenance.lock 与部署互斥；失败保留历史快照（见 backup_restore.py）
ExecStart=$EXEC_START
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7"

TIMER_UNIT="[Unit]
Description=Nightly backup timer for $PROJECT_NAME

[Timer]
OnCalendar=*-*-* $SCHEDULE:00
# 错峰与补跑：随机延迟 30 分钟内；关机错过的时段开机后补执行
RandomizedDelaySec=30m
Persistent=true

[Install]
WantedBy=timers.target"

mkdir -p "$BACKUPS_DIR"
chmod 700 "$BACKUPS_DIR"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "=== dry-run：将安装以下内容（不写系统、不写仓库文件）==="
  echo "--- ${RUNNER}（生成后 700 权限）---"
  printf '%s\n' "$RUNNER_CONTENT"
  echo "--- /etc/systemd/system/$UNIT_NAME.service ---"
  printf '%s\n' "$SERVICE_UNIT"
  echo "--- /etc/systemd/system/$UNIT_NAME.timer ---"
  printf '%s\n' "$TIMER_UNIT"
  echo "--- 后续命令 ---"
  echo "systemctl daemon-reload && systemctl enable --now $UNIT_NAME.timer"
  echo "备份目录：${BACKUPS_DIR}（已确保 700 权限）"
  exit 0
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "❌ 未找到 systemctl；无 systemd 的服务器按 docs/deployment.md 手工配 cron" >&2
  exit 1
fi
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ 安装需要 root（写 /etc/systemd/system）；先用 --dry-run 预览" >&2
  exit 1
fi

printf '%s\n' "$RUNNER_CONTENT" > "$RUNNER"
chmod 700 "$RUNNER"
printf '%s\n' "$SERVICE_UNIT" > "/etc/systemd/system/$UNIT_NAME.service"
printf '%s\n' "$TIMER_UNIT" > "/etc/systemd/system/$UNIT_NAME.timer"
systemctl daemon-reload
systemctl enable --now "$UNIT_NAME.timer"

echo "✅ 已安装并启用 ${UNIT_NAME}.timer（每日 ${SCHEDULE}，随机延迟 ≤30 分钟，错过补跑）"
echo "   手动验证一次：systemctl start $UNIT_NAME.service && journalctl -u $UNIT_NAME.service -e"
if [ -n "$HEALTHCHECKS_URL" ]; then
  echo "   告警：成功 ping 基础 URL、失败 ping /fail；timer 静默失效由对方超时告警兜底"
fi
