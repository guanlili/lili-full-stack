import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.jobs import run_user_export_job
from app.models import Job, JobPublic

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "/users-export",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=JobPublic,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_users_export(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> Job:
    job = Job(task_type="users.export", owner_user_id=current_user.id)
    session.add(job)
    session.commit()
    session.refresh(job)
    background_tasks.add_task(run_user_export_job, job.id)
    return job


@router.get("/{job_id}", response_model=JobPublic)
def read_job(job_id: uuid.UUID, session: SessionDep, current_user: CurrentUser) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if not current_user.is_superuser and job.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    return job
