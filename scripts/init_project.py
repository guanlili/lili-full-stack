"""Initialize a copied template without reading or replacing existing secrets."""

import argparse
import hashlib
import html
import json
import os
import re
import secrets
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 模板自带、开新坑时可清理的示例业务资产。
# 每条规则：文件相对路径 + 是否删除；models.py / api 聚合文件用正则段摘除。
SAMPLE_FILES = [
    "backend/app/api/routes/private.py",
    "backend/tests/api/routes/test_private.py",
    "backend/app/alembic/versions/0005_jobs.py",
]

# models.py 中 Job / JobPublic 两个示例模型段（从 class Job 到下一个顶层 class 之前）
JOB_MODEL_BLOCK = re.compile(
    r"\nclass Job\(SQLModel, table=True\):.*?(?=\nclass \w+\(SQLModel|\nclass \w+\(BaseModel|\Z)",
    re.DOTALL,
)
JOB_PUBLIC_BLOCK = re.compile(
    r"\nclass JobPublic\(SQLModel\):.*?(?=\nclass \w+\(SQLModel|\nclass \w+\(BaseModel|\Z)",
    re.DOTALL,
)


def replace_once(source: str, pattern: str, value: str) -> str:
    result, count = re.subn(pattern, lambda _: value, source, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Expected exactly one match: {pattern}")
    return result


def strip_sample_business_code(root: Path) -> list[str]:
    """摘除模板示例业务代码（Job 后台任务表 + private 示例路由），返回已清理项说明。"""
    removed: list[str] = []

    for rel in SAMPLE_FILES:
        path = root / rel
        if path.exists():
            path.unlink()
            removed.append(rel)

    # 摘除 models.py 里的 Job / JobPublic 示例模型段
    models_path = root / "backend/app/models.py"
    if models_path.exists():
        text = models_path.read_text()
        text, _ = JOB_MODEL_BLOCK.subn("\n", text, count=1)
        text, count = JOB_PUBLIC_BLOCK.subn("\n", text, count=1)
        if count:
            models_path.write_text(text)
            removed.append("backend/app/models.py（Job / JobPublic 模型段）")

    # 摘除 api/main.py 里 private 路由的导入与条件挂载块；
    # 若摘除后 settings 不再被引用，一并去掉其导入。
    api_main = root / "backend/app/api/main.py"
    if api_main.exists():
        text = api_main.read_text()
        text = re.sub(
            r"from app\.api\.routes import [^\n]*\n",
            lambda m: re.sub(r"\bprivate\b\s*,?\s*", "", m.group(0)),
            text,
        )
        text = re.sub(
            r"\nif settings\.ENVIRONMENT == \"local\":\n\s*api_router\.include_router\(private\.router\)\n",
            "\n",
            text,
        )
        if "settings." not in text:
            text = re.sub(r"from app\.core\.config import settings\n", "", text)
        api_main.write_text(text)
        removed.append("backend/app/api/main.py（private 路由挂载）")

    # 0005_jobs 迁移被删除后，把后续迁移的 down_revision 指回 0004，保持链不断
    index_migration = root / "backend/app/alembic/versions/32f63b6790af_index_audit_log_created_at.py"
    if index_migration.exists():
        text = index_migration.read_text()
        new_text = text.replace('down_revision = "0005"', 'down_revision = "0004"')
        new_text = new_text.replace("down_revision = '0005'", "down_revision = '0004'")
        new_text = new_text.replace("Revises: 0005", "Revises: 0004")
        if new_text != text:
            index_migration.write_text(new_text)
            removed.append("backend/app/alembic/versions/32f63b6790af（迁移链指回 0004）")

    return removed


def reset_devledger_state(root: Path) -> list[str]:
    """把仓库内 devledger 项目编号/占位符重置为模板初始状态，供新项目重新接入。"""
    reset: list[str] = []
    # CLAUDE.md 里登记的 Project 编号还原为占位符，交由 new-project.sh 重新注入
    claude = root / "CLAUDE.md"
    if claude.exists():
        text = claude.read_text()
        new_text = re.sub(r"GitHub Project `#?\d+`", "GitHub Project `__PM_PROJECT__`", text)
        if new_text != text:
            claude.write_text(new_text)
            reset.append("CLAUDE.md（Project 编号 → __PM_PROJECT__ 占位符）")
    return reset


def initialize(
    root: Path,
    name: str,
    brand: str,
    slug: str,
    port: int,
    registration: bool,
    clean_sample: bool,
    reset_pm: bool,
) -> None:
    if (root / ".env").exists() or (root / ".env").is_symlink():
        raise ValueError(".env 已存在，拒绝读取或覆盖；请在新复制的项目中初始化")
    for value in (name, brand):
        if not value.strip() or any(ord(char) < 32 for char in value):
            raise ValueError("项目名和品牌不能为空或包含控制字符")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", slug):
        raise ValueError(
            "slug 必须为 1–63 位小写字母、数字、短横线，且以字母或数字开头"
        )
    if not 1 <= port <= 65535:
        raise ValueError("端口必须为 1–65535")

    if clean_sample:
        for item in strip_sample_business_code(root):
            print(f"  · 已清理示例业务代码：{item}")
    if reset_pm:
        for item in reset_devledger_state(root):
            print(f"  · 已重置项目管理状态：{item}")

    env = (root / ".env.example").read_text()
    values = {
        "PROJECT_NAME": json.dumps(name, ensure_ascii=False).replace("$", "$$"),
        "COMPOSE_PROJECT_NAME": slug,
        "APP_PORT": str(port),
        "USERS_OPEN_REGISTRATION": str(registration).lower(),
        "SECRET_KEY": secrets.token_urlsafe(48),
        "POSTGRES_PASSWORD": secrets.token_urlsafe(24),
        "FIRST_SUPERUSER_PASSWORD": secrets.token_urlsafe(24),
    }
    for key, value in values.items():
        env = replace_once(env, rf"^{key}=.*$", f"{key}={value}")
    files = {
        root / "frontend/src/config.ts": replace_once(
            (root / "frontend/src/config.ts").read_text(),
            r"^export const APP_NAME = .*$",
            f"export const APP_NAME = {json.dumps(brand, ensure_ascii=False)}",
        ),
        root / "frontend/index.html": replace_once(
            (root / "frontend/index.html").read_text(),
            r"<title>.*</title>",
            f"<title>{html.escape(brand)}</title>",
        ),
        root / "PROJECT_CONTEXT.md": replace_once(
            (root / "PROJECT_CONTEXT.md").read_text(),
            r"^- 项目名称：.*$",
            f"- 项目名称：{name}",
        ),
    }
    # Validate every source before writing. Exclusive creation prevents accidental
    # credential replacement, and restrictive mode applies from the first byte.
    descriptor = os.open(root / ".env", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        output.write(env)
    for path, content in files.items():
        path.write_text(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--brand", help="前端品牌，默认与项目名一致")
    parser.add_argument("--slug", help="同一服务器必须唯一的 Compose 项目标识")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--registration", choices=("open", "closed"), default="closed")
    parser.add_argument(
        "--clean-sample",
        action="store_true",
        help="清理模板自带的示例业务代码（Job 后台任务表、private 示例路由及其测试/迁移）",
    )
    parser.add_argument(
        "--reset-pm",
        action="store_true",
        help="重置 devledger 项目编号为占位符，便于新项目重新接入项目管理",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="跳过交互式确认，直接执行示例代码清理与 PM 重置",
    )
    args = parser.parse_args()
    slug = args.slug or re.sub(r"[^a-z0-9-]+", "-", args.name.lower()).strip("-")
    slug = slug or "project-" + hashlib.sha256(args.name.encode()).hexdigest()[:8]

    clean_sample = args.clean_sample
    reset_pm = args.reset_pm
    if not args.yes and not (clean_sample or reset_pm):
        # 交互式确认：默认建议清理示例代码并重置 PM 状态
        clean_sample = _confirm("是否清理模板自带的示例业务代码（Job 表 / private 路由）？", default=True)
        reset_pm = _confirm("是否重置 devledger 项目编号为占位符？", default=True)

    try:
        initialize(
            ROOT,
            args.name,
            args.brand or args.name,
            slug,
            args.port,
            args.registration == "open",
            clean_sample,
            reset_pm,
        )
    except (ValueError, OSError) as error:
        parser.exit(1, f"初始化失败：{error}\n")
    print(f"初始化完成：{args.name}；Compose 标识 {slug}；端口 {args.port}")
    print(
        "密钥已写入权限为 600 的 .env，不在终端输出。生产配置请独立设置 GitHub Secrets。"
    )
    print(
        "接下来填写 PROJECT_CONTEXT.md、替换 Logo/favicon，再运行 docker compose up --build。"
    )
    # devledger 项目管理自动激活（零输入）：本机装有 devledger skill 时执行，否则仅提示
    # 标准安装路径优先，~/devledger 兼容旧安装
    pm_script = next(
        (
            p
            for p in (
                os.path.expanduser("~/.agents/skills/devledger/scripts/new-project.sh"),
                os.path.expanduser("~/devledger/scripts/new-project.sh"),
            )
            if os.path.isfile(p)
        ),
        None,
    )
    origin = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True
    ).stdout.strip()
    m = re.search(r"[:/]([^/:]+/[^/.]+)(?:\.git)?$", origin) if origin else None
    # pm_script 在未安装 devledger 的机器上是 None，必须先判空再 isfile
    if pm_script and os.path.isfile(pm_script) and m and shutil.which("gh"):
        print("检测到 devledger，自动接入项目管理（建 Project + 激活占位符）...")
        code = subprocess.run(["bash", pm_script, m.group(1), "--local", ROOT]).returncode
        print("devledger 接入完成" if code == 0 else f"devledger 接入失败（exit {code}），可稍后手动运行：bash {pm_script} {m.group(1)} --local {ROOT}")
    else:
        print("提示：安装 devledger 可自动记账与出验收表 → git clone git@github.com:guanlili/devledger.git ~/.agents/skills/devledger")


def _confirm(prompt: str, default: bool) -> bool:
    suffix = " [Y/n] " if default else " [y/N] "
    answer = input(prompt + suffix).strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes", "是")


if __name__ == "__main__":
    main()
