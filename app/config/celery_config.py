import os
import sys
import time
from functools import lru_cache
from conversation_core.shared.constants import Constants

from apscheduler.schedulers.background import BackgroundScheduler
from celery import current_app as current_celery_app
from common_worker_utils.helm.helm_v2 import HelmV2
from conversation_core.celery_config.base_config import CeleryBaseSettings
from conversation_core.celery_config.v2.queue_config import QueueConfig
from conversation_core.shared.services.scheduling_callback_service import ScheduleMonitorService
from conversation_core.shared.worker.worker_signals import initialize_worker_signals

from raslogger import LoggingFactory

from services.common_services import answer_profile_service
from services.helm_service import helm_service

logger = LoggingFactory.get_logger(__name__)
scheduler = BackgroundScheduler()

TASK_TIME_LIMIT_MINS = 59
QUEUE_NAME = "westlaw_50ss"


@lru_cache()
def get_celery_settings():
    settings = CeleryBaseSettings()
    return settings


env = os.getenv(Constants.ENVIRONMENT, os.getenv(Constants.DD_ENV, "local"))
service = os.getenv(Constants.DD_SERVICE, "ai-rag-westlaw-50-states-survey")

if os.getenv(Constants.ENVIRONMENT, os.getenv(Constants.DD_ENV, "local")) == "local":
    helm_util = None
else:
    helm_util = HelmV2(service=service,
                       namespace=f"207891-ras-search-ai-{env}",
                       environment=env,
                       version=os.getenv("DD_VERSION"))


def is_version_green():
    if os.getenv(Constants.ENVIRONMENT, os.getenv(Constants.DD_ENV, "local")) == "local":
        return False

    return helm_util.is_version_green()


def poll_for_blue(scheduler_server):
    is_blue = not is_version_green()
    if is_blue:
        host_name = os.getenv("HOSTNAME")
        celery_app = current_celery_app
        blue_queues = answer_profile_service.get_queue_list([QUEUE_NAME], is_green=False)

        green_queues = answer_profile_service.get_queue_list([QUEUE_NAME], is_green=True)

        logger.info(f"Connecting {host_name} to blue queues and disconnecting from the green queues.")

        for queue in blue_queues:
            for attempt in range(3):
                try:
                    celery_app.control.add_consumer(queue.name, destination=[f"celery@{host_name}"], reply=True)
                    break  # Exit the retry loop if successful
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} to connect to blue queue {queue.name} failed: {e}")
                    if attempt == 2:  # Final attempt
                        logger.error(f"Failed to connect to blue queue {queue.name} after 3 attempts. Killing the process.")
                        sys.exit(1)
                    time.sleep(2)

        for queue in green_queues:
            for attempt in range(3):
                try:
                    celery_app.control.cancel_consumer(queue.name, destination=[f"celery@{host_name}"], reply=True)
                    break  # Exit the retry loop if successful
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} to disconnect from green queue {queue.name} failed: {e}")
                    if attempt == 2:  # Final attempt
                        logger.error(f"Failed to disconnect from green queue {queue.name} after 3 attempts. Killing the process.")
                        sys.exit(1)

                    time.sleep(2)

        logger.info("Blue is now active!")
        scheduler_server.stop()


def create_celery(worker_concurrency: int = 1):
    input_settings = get_celery_settings()
    celery_app = current_celery_app
    celery_app.conf.update(broker_url=input_settings.broker_url)
    celery_app.conf.update(result_backend=input_settings.result_backend)
    celery_app.conf.update(broker_connection_retry_on_startup=True)
    celery_app.conf.update(task_track_started=True)
    celery_app.conf.update(task_queue_max_priority=10)
    celery_app.conf.update(task_default_priority=5)
    # this should mean we don't lose messages if a pod is forcibly killed and another worker should pick up the message
    celery_app.conf.update(task_acks_late=True)
    celery_app.conf.update(task_serializer='pickle')
    celery_app.conf.update(result_serializer='pickle')
    celery_app.conf.update(accept_content=['pickle', 'json'])
    celery_app.conf.update(result_expires=3600)
    celery_app.conf.update(result_persistent=True)
    celery_app.conf.update(worker_send_task_events=True)
    # this should mean no prefetch is happening since task_acks_late is set to True
    celery_app.conf.update(worker_prefetch_multiplier=1)
    celery_app.conf.update(worker_concurrency=worker_concurrency)
    celery_app.conf.update(imports=["app.worker.v4.action_sequencing_tasks"])
    is_green = is_version_green()
    celery_app.conf.update(task_queues=answer_profile_service.get_queue_list([QUEUE_NAME], is_green=is_green))
    celery_app.conf.update(task_routes=(QueueConfiguration().route_task,))
    celery_app.conf.update(task_soft_time_limit=60 * TASK_TIME_LIMIT_MINS)
    celery_app.conf.update(task_time_limit=60 * TASK_TIME_LIMIT_MINS + 1)
    celery_app.conf.update(worker_max_tasks_per_child=1000)
    celery_app.conf.update(worker_max_memory_per_child=500000000)
    celery_app.conf.update(broker_pool_limit=10)
    celery_app.conf.update(broker_connection_retry=True)
    celery_app.conf.update(task_reject_on_worker_lost=True)
    celery_app.conf.update(socket_keepalive=True)
    celery_app.conf.update(health_check_interval=30)
    celery_app.conf.update(worker_cancel_long_running_tasks_on_connection_loss=True)
    # Explicitly setting visibility_timeout to 60 minutes
    # All celery applications on the same Redis instance adopt the lowest value among all celery applications
    # Do not change these value or you may impact other applications
    celery_app.conf.update(visibility_timeout=60 * 60)
    celery_app.conf.update(result_backend_transport_options={'visibility_timeout': 60 * 60})
    celery_app.conf.update(broker_transport_options={'visibility_timeout': 60 * 60})
    celery_app.conf.update()
    # init_monitors(QUEUE_NAME, input_settings, answer_profile_service)
    initialize_worker_signals()
    if is_green:
        scheduler_server = ScheduleMonitorService(scheduler)
        scheduler.add_job(poll_for_blue, 'interval', args=[scheduler_server], seconds=10)
        scheduler_server.start()
        logger.info("Green state detected. Poller started to wait for blue state.")

    return celery_app


class QueueConfiguration(QueueConfig):
    def __init__(self):
        super().__init__(answer_profile_service)