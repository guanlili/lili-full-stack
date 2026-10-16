"""Initialize a copied template without reading or replacing existing secrets."""

import argparse
import hashlib
import html
import json
import re
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(source: str, pattern: str, value: str) -> str:
    result, count = re.subn(pattern, lambda _: value, source, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Expected exactly one match: {pattern}")
    return result


def initialize(
    root: Path, name: str, brand: str, slug: str, port: int, registration: bool
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
    import os

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
    args = parser.parse_args()
    slug = args.slug or re.sub(r"[^a-z0-9-]+", "-", args.name.lower()).strip("-")
    slug = slug or "project-" + hashlib.sha256(args.name.encode()).hexdigest()[:8]
    try:
        initialize(
            ROOT,
            args.name,
            args.brand or args.name,
            slug,
            args.port,
            args.registration == "open",
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


if __name__ == "__main__":
    main()
