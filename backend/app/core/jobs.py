import csv
import io
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, col, select

from app.core.config import settings
from app.core.db import engine
from app.models import FileAsset, Job, User


def run_user_export_job(job_id: uuid.UUID) -> None:
    """Run the built-in export task in FastAPI's background worker."""
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if job is None:
            return
        job.status = "running"
        session.add(job)
        session.commit()
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                ["email", "full_name", "is_active", "is_superuser", "created_at"]
            )
            for user in session.exec(select(User).order_by(col(User.created_at))).all():
                writer.writerow(
                    [
                        user.email,
                        user.full_name or "",
                        user.is_active,
                        user.is_superuser,
                        user.created_at.isoformat() if user.created_at else "",
                    ]
                )
            asset = FileAsset(
                original_name="users-export.csv",
                stored_name=f"{uuid.uuid4().hex}.csv",
                content_type="text/csv",
                size=len(output.getvalue().encode("utf-8")),
                owner_user_id=job.owner_user_id,
            )
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)
            (upload_dir / asset.stored_name).write_text(
                output.getvalue(), encoding="utf-8"
            )
            session.add(asset)
            job.status = "completed"
            job.result = {"file_id": str(asset.id)}
            job.finished_at = datetime.now(UTC)
            session.add(job)
            session.commit()
        except Exception as exc:
            session.rollback()
            job = session.get(Job, job_id)
            if job:
                job.status = "failed"
                job.error = type(exc).__name__
                job.finished_at = datetime.now(UTC)
                session.add(job)
                session.commit()
