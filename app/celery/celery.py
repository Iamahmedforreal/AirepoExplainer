from celery import Celery
from app.config.app_config import settings

redis_url= settings.redis_url

app = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

