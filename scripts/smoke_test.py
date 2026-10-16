"""Deployment smoke checks using dedicated accounts. Credentials come only from environment variables."""

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class SmokeFailure(Exception):
    pass


class SmokeClient:
    def __init__(self, base_url: str) -> None:
        parts = urlsplit(base_url)
        if (
            parts.scheme not in {"http", "https"}
            or not parts.netloc
            or parts.username
            or parts.password
            or parts.query
            or parts.fragment
        ):
            raise SmokeFailure("使用不含凭据、查询或片段的 http(s) 地址")
        self.base_url = base_url.rstrip("/")
        self.opener = build_opener(NoRedirect())

    def request(
        self,
        path: str,
        expected: int,
        token: str = "",
        body: dict | None = None,
        form: bool = False,
    ):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        data = None
        if body is not None:
            headers["Content-Type"] = (
                "application/x-www-form-urlencoded" if form else "application/json"
            )
            data = urlencode(body).encode() if form else json.dumps(body).encode()
        request = Request(self.base_url + path, headers=headers, data=data)
        try:
            response = self.opener.open(request, timeout=10)
        except HTTPError as error:
            response = error
        except OSError:
            raise SmokeFailure(f"连接失败：{path}") from None
        with response:
            if response.status != expected:
                raise SmokeFailure(
                    f"状态不符：{path}，预期 {expected}，实际 {response.status}"
                )
            content = response.read(2_000_000)
            if "json" in response.headers.get("Content-Type", ""):
                return json.loads(content)
            return content


def run(client: SmokeClient, credentials: dict[str, str]) -> None:
    if client.request("/api/v1/utils/ready-check/", 200) != {"message": "Ready"}:
        raise SmokeFailure("就绪响应格式异常")
    page = client.request("/login", 200)
    if not isinstance(page, bytes) or b'<div id="root"' not in page:
        raise SmokeFailure("登录页不是预期的前端应用")
    for path in ("/api/v1/access/me", "/api/v1/users/me", "/api/v1/roles/"):
        client.request(path, 401)
    print("公开入口、就绪和未登录保护检查通过")
    for role in ("ADMIN", "VISITOR"):
        email, password = (
            credentials.get(f"SMOKE_{role}_EMAIL"),
            credentials.get(f"SMOKE_{role}_PASSWORD"),
        )
        if bool(email) != bool(password):
            raise SmokeFailure(f"{role} 冒烟账号和密码须成对配置")
        if not email:
            print(f"跳过 {role} 登录/刷新检查：未配置专用冒烟账号")
            continue
        tokens = client.request(
            "/api/v1/login/access-token",
            200,
            body={"username": email, "password": password},
            form=True,
        )
        access = tokens["access_token"]
        rights = client.request("/api/v1/access/me", 200, token=access)
        if rights["is_admin"] != (role == "ADMIN"):
            raise SmokeFailure(f"{role} 冒烟账号身份不符")
        client.request("/api/v1/users/me", 200, token=access)
        client.request("/api/v1/roles/", 200 if role == "ADMIN" else 403, token=access)
        client.request(
            "/api/v1/users/",
            200 if role == "ADMIN" or "users.view" in rights["permissions"] else 403,
            token=access,
        )
        rotated = client.request(
            "/api/v1/login/refresh",
            200,
            body={"refresh_token": tokens["refresh_token"]},
        )
        client.request("/api/v1/access/me", 200, token=rotated["access_token"])
        # Revoke only sessions owned by this explicitly designated smoke account.
        client.request(
            "/api/v1/login/logout-all", 200, token=rotated["access_token"], body={}
        )
        print(f"{role} 登录、权限和刷新检查通过")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument(
        "--require-auth", action="store_true", help="缺少任一专用账号时失败"
    )
    parser.add_argument(
        "--credentials-stdin",
        action="store_true",
        help="从标准输入读取 JSON 凭据（部署通道使用）",
    )
    args = parser.parse_args()
    try:
        credentials = (
            json.load(sys.stdin) if args.credentials_stdin else dict(os.environ)
        )
        if not isinstance(credentials, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in credentials.items()
        ):
            raise SmokeFailure("冒烟凭据必须是字符串键值的 JSON 对象")
        require_auth = (
            args.require_auth or credentials.get("SMOKE_REQUIRE_AUTH") == "true"
        )
        if require_auth and not all(
            credentials.get(f"SMOKE_{role}_{key}")
            for role in ("ADMIN", "VISITOR")
            for key in ("EMAIL", "PASSWORD")
        ):
            raise SmokeFailure("完整检查需要 ADMIN 和 VISITOR 专用冒烟账号")
        run(SmokeClient(args.base_url), credentials)
    except (SmokeFailure, ValueError, KeyError, TypeError):
        # Never include HTTP response bodies or credentials in CI output.
        parser.exit(1, "冒烟检查失败，请检查服务状态、账号配置和权限。\n")


if __name__ == "__main__":
    main()
