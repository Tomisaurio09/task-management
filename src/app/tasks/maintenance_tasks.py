# app/tasks/maintenance_tasks.py
from datetime import datetime, timezone
from app.core.celery_app import celery_app
from app.core.logger import logger
from app.db.session import SessionLocal
from app.models.task import Task, TaskStatus


@celery_app.task(name="app.tasks.maintenance_tasks.archive_overdue_tasks")
def archive_overdue_tasks():
    """
    Corre cada hora via Celery Beat.
    Busca tasks con due_date vencida y status ACTIVE, las archiva.
    """
    db = SessionLocal()
    archived_count = 0

    try:
        now = datetime.now(timezone.utc)

        overdue_tasks = db.query(Task).filter(
            Task.due_date < now,
            Task.status == TaskStatus.ACTIVE,
            Task.archived.is_(False)
        ).all()

        for task in overdue_tasks:
            task.archived = True
            task.status = TaskStatus.ARCHIVED
            archived_count += 1

        if archived_count > 0:
            db.commit()

        logger.info(
            "Overdue tasks archived",
            extra={
                "archived_count": archived_count,
                "checked_at": now.isoformat(),
            }
        )

        return {
            "archived_count": archived_count,
            "executed_at": now.isoformat(),
        }

    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to archive overdue tasks",
            extra={"error": str(e)},
            exc_info=True
        )
        raise

    finally:
        db.close()