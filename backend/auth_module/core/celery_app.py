"""
Celery application configuration for background tasks.

This module sets up Celery for handling asynchronous tasks like:
- Email sending
- Data scraping
- Report generation
- Cache warming
"""

from celery import Celery
from .config import config
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "luftway",
    broker=config.redis_url,  # Use Redis as message broker
    backend=config.redis_url,  # Use Redis as result backend
    include=[
        "auth_module.tasks.email_tasks",
        "search_booking_module.tasks.scraping_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,
    task_routes={
        "auth_module.tasks.email_tasks.*": {"queue": "emails"},
        "search_booking_module.tasks.scraping_tasks.*": {"queue": "scraping"},
        "search_booking_module.tasks.cache_tasks.*": {"queue": "cache"},
    },
    task_default_queue="default",
    task_default_exchange="tasks",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
)

logger.info("Celery application configured successfully")

