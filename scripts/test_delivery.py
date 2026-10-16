"""Regression tests use temporary copies and a local HTTP server, never project secrets."""

import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from check_page_permissions import ROOT, check
from init_project import initialize
from smoke_test import SmokeClient, SmokeFailure, run


class InitializationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (
            ".env.example",
            "frontend/src/config.ts",
            "frontend/index.html",
            "PROJECT_CONTEXT.md",
        ):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / name, target)

    def test_initialize_and_refuse_existing_secrets(self):
        initialize(self.root, '客户 "A" $订单', "A & B", "customer-a", 8085, False)
        env = self.root / ".env"
        self.assertEqual(env.stat().st_mode & 0o777, 0o600)
        self.assertIn("APP_PORT=8085", env.read_text())
        self.assertIn("USERS_OPEN_REGISTRATION=false", env.read_text())
        self.assertNotIn("=changethis", env.read_text())
        self.assertIn("$$订单", env.read_text())
        self.assertIn("A &amp; B", (self.root / "frontend/index.html").read_text())
        before = env.read_bytes()
        with self.assertRaises(ValueError):
            initialize(self.root, "Other", "Other", "other", 80, True)
        self.assertEqual(env.read_bytes(), before)

    def test_invalid_or_missing_source_never_creates_env(self):
        for slug, port, name in (
            ("bad/slug", 80, "name"),
            ("valid", 0, "name"),
            ("valid", 80, "bad\nname"),
        ):
            with self.assertRaises(ValueError):
                initialize(self.root, name, "Brand", slug, port, False)
            self.assertFalse((self.root / ".env").exists())
        (self.root / "frontend/src/config.ts").write_text("unrecognized template")
        with self.assertRaises(ValueError):
            initialize(self.root, "Name", "Brand", "valid", 80, False)
        self.assertFalse((self.root / ".env").exists())


class PermissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in (
            "frontend/src/routes",
            "backend/app/core",
            "backend/app/api/routes",
        ):
            shutil.copytree(ROOT / path, self.root / path)

    def test_missing_route_permission_and_stale_registry(self):
        self.assertEqual(check(self.root), [])
        route = self.root / "frontend/src/routes/_layout/reports.tsx"
        route.write_text('export const Route = createFileRoute("/_layout/reports")({})')
        self.assertTrue(
            any("页面未注册权限：/reports" in item for item in check(self.root))
        )
        route.unlink()
        (self.root / "frontend/src/routes/_layout/roles.tsx").unlink()
        self.assertTrue(
            any("缺少前端页面：/roles" in item for item in check(self.root))
        )

    def test_public_route_and_unknown_api_permission(self):
        (self.root / "frontend/src/routes/report.tsx").write_text(
            'createFileRoute("/reports")({})'
        )
        self.assertTrue(any("纳入权限" in item for item in check(self.root)))
        (self.root / "backend/app/api/routes/report.py").write_text(
            'guard = require_permission("unknown.view")'
        )
        self.assertTrue(any("未注册" in item for item in check(self.root)))


class SmokeTransportTests(unittest.TestCase):
    def test_required_credentials_fail_without_network_or_secret_output(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/smoke_test.py"),
                "http://127.0.0.1:1",
                "--credentials-stdin",
                "--require-auth",
            ],
            input='{"SMOKE_ADMIN_PASSWORD":"test-secret-never-log"}',
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("test-secret-never-log", result.stdout + result.stderr)
        self.assertIn("冒烟检查失败", result.stderr)

    def test_baseline_and_redirects(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                if self.path == "/login":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b'<div id="root"></div>')
                elif self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/login")
                    self.end_headers()
                else:
                    self.send_response(200 if "ready-check" in self.path else 401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"message":"Ready"}')

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = SmokeClient(f"http://127.0.0.1:{server.server_port}")
            with redirect_stdout(io.StringIO()):
                run(client, {})
            with self.assertRaises(SmokeFailure):
                client.request("/redirect", 200)
            with redirect_stdout(io.StringIO()), self.assertRaises(SmokeFailure):
                run(client, {"SMOKE_ADMIN_EMAIL": "test@example.invalid"})
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
