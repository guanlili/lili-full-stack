#!/usr/bin/env python3
"""Offline, consistent database snapshots for the Compose deployment."""

import argparse
import fcntl
import hashlib
import json
import shutil
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

FILES = ("database.dump",)


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify(snapshot: Path) -> None:
    manifest = json.loads((snapshot / "manifest.json").read_text())
    if manifest.get("format") != 1 or set(manifest.get("sha256", {})) != set(FILES):
        raise RuntimeError("Unsupported or incomplete backup manifest")
    for name in FILES:
        path = snapshot / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing or invalid backup file: {name}")
        if digest(path) != manifest["sha256"][name]:
            raise RuntimeError(f"Checksum mismatch: {name}")


class Deployment:
    def __init__(self, project: Path):
        self.project = project
        self.command = ["docker", "compose", "-f", str(project / "compose.yml")]

    def run(self, *args: str, **kwargs):
        return subprocess.run(
            [*self.command, *args], cwd=self.project, check=True, **kwargs
        )

    @contextmanager
    def maintenance(self):
        with (self.project / ".maintenance.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def backup(self, destination: Path) -> Path:
        with self.maintenance():
            return self._backup(destination)

    def _backup(self, destination: Path) -> Path:
        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
        running = self.run(
            "ps", "--status", "running", "--services", capture_output=True, text=True
        ).stdout.splitlines()
        if "prestart" in running:
            raise RuntimeError("Wait for deployment/migrations to finish before backup")
        snapshot = destination / datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%S.%fZ"
        )
        snapshot.mkdir(mode=0o700)
        stopped = [name for name in ("frontend", "backend") if name in running]
        try:
            if stopped:
                self.run("stop", *stopped)
            with (snapshot / FILES[0]).open("xb") as target:
                self.run(
                    "exec",
                    "-T",
                    "db",
                    "sh",
                    "-c",
                    'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc',
                    stdout=target,
                )
            manifest = {
                "format": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "sha256": {name: digest(snapshot / name) for name in FILES},
            }
            for name in FILES:
                (snapshot / name).chmod(0o600)
            (snapshot / "manifest.json").write_text(json.dumps(manifest, indent=2))
            (snapshot / "manifest.json").chmod(0o600)
            verify(snapshot)
        except BaseException:
            # This directory was created exclusively by this run. Keep prior snapshots.
            shutil.rmtree(snapshot)
            raise
        finally:
            if stopped:
                self.run("start", *reversed(stopped))
        return snapshot

    def restore(self, snapshot: Path) -> None:
        with self.maintenance():
            self._restore(snapshot)

    def _restore(self, snapshot: Path) -> None:
        verify(snapshot)
        running = self.run(
            "ps", "--status", "running", "--services", capture_output=True, text=True
        ).stdout.splitlines()
        if any(name in running for name in ("backend", "frontend", "prestart")):
            raise RuntimeError("Stop frontend, backend and prestart before restoring")
        self.run("up", "-d", "--wait", "db")
        # --wait 只等 healthcheck 通过，psql 仍可能撞上启动窗口（CI 偶发 exit 2 竞态）：
        # 计数放进容器内重试循环，30 秒内拿到结果，全部失败才报错
        result = self.run(
            "exec",
            "-T",
            "db",
            "sh",
            "-c",
            'sql="SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace '
            "WHERE n.nspname NOT IN ('pg_catalog','information_schema') "
            "AND n.nspname NOT LIKE 'pg_toast%' AND c.relkind IN ('r','p','v','m','S','f')\"; "
            'for i in $(seq 1 30); do '
            'count=$(exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "$sql" 2>/dev/null) '
            "&& break; sleep 1; done; "
            '[ -n "$count" ] || exit 1; echo "$count"',
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() != "0":
            raise RuntimeError("Refusing to restore into a non-empty database")
        # Validate the dump header before writing the target store.
        with (snapshot / FILES[0]).open("rb") as source:
            self.run(
                "exec",
                "-T",
                "db",
                "pg_restore",
                "--list",
                stdin=source,
                stdout=subprocess.DEVNULL,
            )
        with (snapshot / FILES[0]).open("rb") as source:
            self.run(
                "exec",
                "-T",
                "db",
                "sh",
                "-c",
                'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" '
                "--no-owner --no-acl --exit-on-error --single-transaction",
                stdin=source,
            )
        print("Restored database. Start the application and verify readiness.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("backup", "verify", "restore"))
    parser.add_argument(
        "path", type=Path, help="Backup directory or snapshot to verify/restore"
    )
    parser.add_argument(
        "--project-dir", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument(
        "--confirm-restore",
        action="store_true",
        help="Explicitly authorize writing to the empty target",
    )
    args = parser.parse_args()
    path = args.path.resolve()
    deployment = Deployment(args.project_dir.resolve())
    if args.action == "backup":
        print(deployment.backup(path))
    elif args.action == "verify":
        verify(path)
        print("Backup checksums verified.")
    elif not args.confirm_restore:
        parser.error("Restore requires --confirm-restore and an empty target database")
    else:
        deployment.restore(path)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Backup/restore failed: {exc}", file=sys.stderr)
        sys.exit(1)
