# app/tasks/notification_tasks.py
from app.core.celery_app import celery_app
from app.core.logger import logger


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # espera 60s antes de reintentar
    name="app.tasks.notification_tasks.send_member_invitation_email"
)
def send_member_invitation_email(
    self,
    project_id: str,
    user_email: str,
    invited_by_email: str,
    role: str
):
    """
    Envía email de invitación cuando se agrega un miembro a un proyecto.
    Por ahora loguea el envío. La integración con SMTP va después.
    """
    try:
        logger.info(
            "Sending invitation email",
            extra={
                "task_id": self.request.id,
                "project_id": project_id,
                "user_email": user_email,
                "invited_by": invited_by_email,
                "role": role,
            }
        )

        # Acá iría el código de SMTP real en el futuro.
        # Por ahora simulamos el envío.
        email_content = (
            f"You have been invited to project {project_id} "
            f"as {role} by {invited_by_email}"
        )

        logger.info(
            "Invitation email sent successfully",
            extra={
                "task_id": self.request.id,
                "user_email": user_email,
                "content": email_content,
            }
        )

        return {
            "status": "sent",
            "recipient": user_email,
            "project_id": project_id,
        }

    except Exception as exc:
        logger.error(
            "Failed to send invitation email",
            extra={
                "task_id": self.request.id,
                "user_email": user_email,
                "error": str(exc),
            }
        )
        # Reintenta automáticamente hasta max_retries veces
        raise self.retry(exc=exc)