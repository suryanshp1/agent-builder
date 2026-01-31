from celery import Celery
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "agentbuilder",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.agent_tasks", "app.tasks.scheduled_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time for long-running tasks
    broker_connection_retry_on_startup=True,
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.agent_tasks.execute_agent_task": {"queue": "agent_execution"},
    "app.tasks.agent_tasks.execute_workflow_task": {"queue": "workflow_execution"},
}

# Periodic tasks (Celery Beat schedule)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Example: Clean up old execution logs every day at 2am
    "cleanup-old-logs": {
        "task": "app.tasks.scheduled_tasks.cleanup_old_logs",
        "schedule": crontab(hour=2, minute=0),
    },
}


if __name__ == "__main__":
    celery_app.start()
