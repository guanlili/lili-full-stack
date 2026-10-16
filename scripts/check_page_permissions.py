"""Check authenticated frontend routes against the backend page registry, without importing the app."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# This page contains only an access-denied message and links to granted pages.
EXEMPT = {"/forbidden"}


def check(root: Path) -> list[str]:
    errors: list[str] = []
    tree = ast.parse((root / "backend/app/core/permissions.py").read_text())
    registry = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "PAGES"
            for target in node.targets
        )
    )
    paths: set[str] = set()
    codes: set[str] = set()
    for entry in registry.elts:
        if not isinstance(entry, ast.Call) or len(entry.args) < 3:
            raise ValueError("PAGES 必须由显式 PagePermission 条目组成")
        path, code, title = [ast.literal_eval(arg) for arg in entry.args[:3]]
        if not all(isinstance(value, str) and value for value in (path, code, title)):
            raise ValueError("页面路径、权限码和标题必须为非空字符串")
        if path in paths or code in codes:
            errors.append(f"重复页面路径或权限码：{path} / {code}")
        if not path.startswith("/") or (path != "/" and path.endswith("/")):
            errors.append(f"页面路径必须以 / 开头且不能带尾斜线：{path}")
        paths.add(path)
        codes.add(code)
    routes: set[str] = set()
    for file in (root / "frontend/src/routes").rglob("*"):
        if file.suffix not in {".ts", ".tsx"}:
            continue
        if file.name == "__root.tsx":
            continue
        source = file.read_text()
        declarations = re.findall(
            r'createFileRoute\(\s*["\']([^"\']+)["\']\s*\)', source
        )
        if not declarations:
            # Fail closed for route files rather than silently skipping expressions
            # or new source layouts that this checker cannot understand.
            errors.append(
                f"路由文件须使用静态 createFileRoute 路径：{file.relative_to(root)}"
            )
        for route in declarations:
            if route == "/_layout":
                continue
            if not route.startswith("/_layout/"):
                # New public pages must be reviewed deliberately; existing auth
                # entry points are the only default public pages in this template.
                if route not in {
                    "/login",
                    "/signup",
                    "/recover-password",
                    "/reset-password",
                }:
                    errors.append(f"新增页面必须放在 /_layout 下纳入权限：{route}")
                continue
            path = route.removeprefix("/_layout").rstrip("/") or "/"
            if path in routes:
                errors.append(f"重复前端页面：{path}")
            routes.add(path)
    for path in sorted(routes - paths - EXEMPT):
        errors.append(
            f"页面未注册权限：{path}（请加入 backend/app/core/permissions.py PAGES）"
        )
    for path in sorted(paths - routes):
        errors.append(f"权限注册缺少前端页面：{path}")
    for file in (root / "backend/app/api/routes").rglob("*.py"):
        for match in re.finditer(r"require_permission\(\s*([^)]*)\)", file.read_text()):
            try:
                code = ast.literal_eval(match[1])
            except (ValueError, SyntaxError):
                code = None
            if code not in codes:
                errors.append(
                    f"API 引用了未注册或非静态权限码：{file.relative_to(root)}"
                )
    return errors


if __name__ == "__main__":
    try:
        failures = check(ROOT)
    except (ValueError, SyntaxError, StopIteration, AttributeError) as error:
        raise SystemExit(f"权限检查无法解析：{error}") from None
    if failures:
        raise SystemExit("\n".join(failures))
    print("页面与 API 权限登记检查通过")
