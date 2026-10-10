#!/usr/bin/env python3
"""Backup validation tests; --integration exercises two disposable app_test databases."""

import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from backup_restore import FILES, Deployment, digest, verify

INTEGRATION = "--integration" in sys.argv
if INTEGRATION:
    sys.argv.remove("--integration")


class BackupValidationTests(unittest.TestCase):
    def make_snapshot(self, root: Path, unsafe: bool = False) -> Path:
        (root / FILES[0]).write_bytes(b"PGDMP-test")
        with tarfile.open(root / FILES[1], "w") as archive:
            member = tarfile.TarInfo("../escape" if unsafe else "attachment.txt")
            member.size = 3
            archive.addfile(member, io.BytesIO(b"abc"))
        (root / "manifest.json").write_text(
            json.dumps(
                {
                    "format": 1,
                    "sha256": {name: digest(root / name) for name in FILES},
                }
            )
        )
        return root

    def test_corruption_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_snapshot(Path(tmp))
            verify(root)
            (root / FILES[0]).write_bytes(b"corrupted")
            with self.assertRaisesRegex(RuntimeError, "Checksum mismatch"):
                verify(root)

    def test_path_traversal_rejected_before_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_snapshot(Path(tmp), unsafe=True)
            deployment = Deployment(root)
            with patch.object(deployment, "run") as run:
                with self.assertRaisesRegex(RuntimeError, "Unsafe entry"):
                    deployment.restore(root)
                run.assert_not_called()

    def test_failed_backup_is_removed_and_services_restart(self):
        for stage in ("dump", "tar", "verify"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                deployment = Deployment(Path(tmp))
                destination = Path(tmp) / "backups"
                previous = destination / "previous"
                previous.mkdir(parents=True)
                self.make_snapshot(previous)
                calls = []

                def run(*args, **kwargs):
                    calls.append(args)
                    if args[0] == "ps":
                        return subprocess.CompletedProcess(
                            [], 0, stdout="backend\nfrontend\n"
                        )
                    if args[0] == "exec":
                        kwargs["stdout"].write(b"partial dump")
                        if stage == "dump":
                            raise RuntimeError("dump failed")
                    return subprocess.CompletedProcess([], 0)

                def helper(_code, **kwargs):
                    kwargs["stdout"].write(b"partial archive")
                    if stage == "tar":
                        raise RuntimeError("tar failed")

                with (
                    patch.object(deployment, "run", side_effect=run),
                    patch.object(deployment, "helper", side_effect=helper),
                    patch(
                        "backup_restore.verify",
                        side_effect=RuntimeError("verify failed"),
                    ),
                ):
                    with self.assertRaisesRegex(RuntimeError, f"{stage} failed"):
                        deployment.backup(destination)
                self.assertIn(("start", "backend", "frontend"), calls)
                self.assertEqual(list(destination.iterdir()), [previous])
                verify(previous)

    def test_nonempty_database_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_snapshot(Path(tmp))
            deployment = Deployment(root)
            with (
                patch.object(
                    deployment,
                    "run",
                    side_effect=[
                        subprocess.CompletedProcess([], 0, stdout=""),
                        subprocess.CompletedProcess([], 0),
                        subprocess.CompletedProcess([], 0, stdout="1\n"),
                    ],
                ),
                patch.object(deployment, "helper") as helper,
            ):
                with self.assertRaisesRegex(RuntimeError, "non-empty database"):
                    deployment.restore(root)
                helper.assert_not_called()


@unittest.skipUnless(
    INTEGRATION, "Pass --integration to run disposable Docker restore drill"
)
class RestoreIntegrationTests(unittest.TestCase):
    def test_database_and_attachment_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            deployments = []
            try:
                for label in ("source", "target"):
                    project = root / label
                    project.mkdir()
                    project_name = f"backup-test-{uuid.uuid4().hex[:12]}"
                    (project / "compose.yml").write_text(f"""name: {project_name}
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: isolated-test-only
      POSTGRES_DB: app_test
    healthcheck:
      test: [CMD-SHELL, "pg_isready -U postgres -d app_test"]
      interval: 1s
      timeout: 3s
      retries: 30
    volumes:
      - database:/var/lib/postgresql
  backend:
    image: python:3.12-slim
    entrypoint: [python]
    command: ["-c", "import time; time.sleep(3600)"]
    volumes:
      - uploads:/app/uploads
  frontend:
    image: python:3.12-slim
    command: [python, -c, "import time; time.sleep(3600)"]
volumes:
  database:
  uploads:
""")
                    deployments.append(Deployment(project))
                source, target = deployments
                source.run("up", "-d", "--wait", "db", "backend", "frontend")
                source.run(
                    "exec",
                    "-T",
                    "db",
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    "app_test",
                    "-c",
                    "CREATE TABLE restore_probe (id int primary key, value text); "
                    "INSERT INTO restore_probe VALUES (1, 'restored');",
                )
                source.helper(
                    "from pathlib import Path; Path('/app/uploads/probe.bin').write_bytes(bytes(range(256)))"
                )
                snapshot = source.backup(root / "backups")
                running = source.run(
                    "ps",
                    "--status",
                    "running",
                    "--services",
                    capture_output=True,
                    text=True,
                ).stdout
                self.assertIn("backend", running)
                self.assertIn("frontend", running)
                target.restore(snapshot)
                restored = target.run(
                    "exec",
                    "-T",
                    "db",
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    "app_test",
                    "-Atc",
                    "SELECT value FROM restore_probe",
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(restored.stdout.strip(), "restored")
                target.helper(
                    "from pathlib import Path; assert Path('/app/uploads/probe.bin').read_bytes() == bytes(range(256))"
                )
                with self.assertRaisesRegex(RuntimeError, "non-empty database"):
                    target.restore(snapshot)
            finally:
                for deployment in deployments:
                    deployment.run("down", "--volumes", "--remove-orphans")


if __name__ == "__main__":
    unittest.main()
