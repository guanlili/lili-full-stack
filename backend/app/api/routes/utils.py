import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic.networks import EmailStr
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.core.config import settings
from app.models import Message
from app.utils import generate_test_email, send_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    if not settings.emails_enabled:
        # superuser 专用接口，直接说明原因，优于让 send_email 抛 500
        raise HTTPException(
            status_code=400,
            detail="Email is not configured (SMTP_HOST / EMAILS_FROM_EMAIL missing)",
        )
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    """
    轻量存活检查（liveness）：进程能响应即返回 True，不触碰数据库。
    容器重启判定、负载均衡存活探针用它。
    """
    return True


@router.get("/ready-check/")
def ready_check(session: SessionDep) -> Message:
    """
    就绪检查（readiness）：验证数据库连接可用，失败返回 503。
    容器健康检查与部署后验证用它；数据库恢复后自动恢复正常。
    """
    try:
        # 限制单次探测 3 秒：DB 半死（连接挂起）时快速失败，不让探针请求堆积
        conn = session.connection()
        conn.exec_driver_sql("SET LOCAL statement_timeout = 3000")
        session.exec(select(1))
    except Exception:
        # 只记服务端日志，不向调用方暴露内部异常细节
        logger.warning("Readiness check failed: database not reachable")
        raise HTTPException(status_code=503, detail="Service not ready") from None
    return Message(message="Ready")
