# app/core/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "task_management",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.notification_tasks",
        "app.tasks.maintenance_tasks",
    ]
)

celery_app.conf.update(
    # Serialización
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=True,

    # Reintentos por defecto para todas las tasks
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Beat schedule: tareas periódicas
    beat_schedule={
        "archive-overdue-tasks": {
            "task": "app.tasks.maintenance_tasks.archive_overdue_tasks",
            "schedule": 3600.0,  # cada 1 hora en segundos
        },
    },
)