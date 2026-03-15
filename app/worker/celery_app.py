from celery import Celery
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "deribit_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"]
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=60,  # 1 minute
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    
    # Result settings
    result_expires=3600,  # 1 hour
    result_backend=settings.CELERY_RESULT_BACKEND,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "fetch-btc-price-every-minute": {
            "task": "app.worker.tasks.fetch_and_save_price",
            "schedule": 60.0,  # every minute
            "args": ("btc_usd",),
            "options": {"queue": "prices"}
        },
        "fetch-eth-price-every-minute": {
            "task": "app.worker.tasks.fetch_and_save_price",
            "schedule": 60.0,  # every minute
            "args": ("eth_usd",),
            "options": {"queue": "prices"}
        },
        "cleanup-old-records-daily": {
            "task": "app.worker.tasks.cleanup_old_records",
            "schedule": 86400.0,  # daily at midnight
            "args": (30,),
            "options": {"queue": "maintenance"}
        }
    },
    
    # Queue configuration
    task_queues={
        "prices": {"exchange": "prices", "routing_key": "prices"},
        "maintenance": {"exchange": "maintenance", "routing_key": "maintenance"},
        "default": {"exchange": "default", "routing_key": "default"}
    },
    
    # Routing
    task_routes={
        "app.worker.tasks.fetch_and_save_price": {"queue": "prices"},
        "app.worker.tasks.cleanup_old_records": {"queue": "maintenance"},
    }
)

logger.info("Celery app configured successfully")

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working"""
    logger.info(f"Debug task executed: {self.request.id}")
    return {"status": "ok", "task_id": self.request.id}