#!/usr/bin/env python3
"""Offline, consistent database + uploads snapshots for the Compose deployment."""

import argparse
import fcntl
import hashlib
import json
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

FILES = ("database.dump", "uploads.tar")
UPLOAD_BACKUP = """
import pathlib, sys, tarfile
root = pathlib.Path('/app/uploads')
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as archive:
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.is_symlink():
            raise RuntimeError('Uploads must contain regular files only')
        archive.add(path, arcname=path.name, recursive=False)
"""
UPLOAD_CHECK = """
import pathlib
root = pathlib.Path('/app/uploads')
if any(root.iterdir()):
    raise RuntimeError('Refusing to restore into a non-empty uploads volume')
"""
UPLOAD_RESTORE = """
import sys, tarfile
with tarfile.open(fileobj=sys.stdin.buffer, mode='r|') as archive:
    archive.extractall('/app/uploads', filter='data')
"""


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
    # Validate every member before changing the target database or volume.
    import tarfile

    with tarfile.open(snapshot / "uploads.tar") as archive:
        for member in archive:
            if not member.isfile() or Path(member.name).name != member.name:
                raise RuntimeError("Unsafe entry in uploads archive")


class Deployment:
    def __init__(self, project: Path):
        self.project = project
        self.command = ["docker", "compose", "-f", str(project / "compose.yml")]

    def run(self, *args: str, **kwargs):
        return subprocess.run(
            [*self.command, *args], cwd=self.project, check=True, **kwargs
        )

    def helper(self, code: str, **kwargs):
        return self.run(
            "run",
            "--rm",
            "--no-deps",
            "-T",
            "--entrypoint",
            "python",
            "backend",
            "-c",
            code,
            **kwargs,
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
        snapshot = destination / datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%S.%fZ"
        )
        snapshot.mkdir(mode=0o700)
        running = self.run(
            "ps", "--status", "running", "--services", capture_output=True, text=True
        ).stdout.splitlines()
        if "prestart" in running:
            raise RuntimeError("Wait for deployment/migrations to finish before backup")
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
            with (snapshot / FILES[1]).open("xb") as target:
                self.helper(UPLOAD_BACKUP, stdout=target)
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
        result = self.run(
            "exec",
            "-T",
            "db",
            "sh",
            "-c",
            'exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc '
            '"SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace '
            "WHERE n.nspname NOT IN ('pg_catalog','information_schema') "
            "AND n.nspname NOT LIKE 'pg_toast%' AND c.relkind IN ('r','p','v','m','S','f')\"",
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() != "0":
            raise RuntimeError("Refusing to restore into a non-empty database")
        self.helper(UPLOAD_CHECK)
        # Validate the dump header before writing either store.
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
        with (snapshot / FILES[1]).open("rb") as source:
            self.helper(UPLOAD_RESTORE, stdin=source)
        print(
            "Restored database and uploads. Start the application and verify readiness."
        )


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
        print("Backup checksums and archive entries verified.")
    elif not args.confirm_restore:
        parser.error(
            "Restore requires --confirm-restore and an empty target database/volume"
        )
    else:
        deployment.restore(path)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Backup/restore failed: {exc}", file=sys.stderr)
        sys.exit(1)
