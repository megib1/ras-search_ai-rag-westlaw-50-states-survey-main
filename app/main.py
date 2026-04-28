import logging

from common_utils.logging_helper import init_logging
from ddtrace import patch_all
from raslogger import LoggingFactory
from config.celery_config import create_celery
from config.settings import get_settings


logger = LoggingFactory.get_logger(__name__)
settings = get_settings()

if settings.DISABLE_ALL_PY_WARNINGS:
    LoggingFactory.get_logger("langchain.vectorstores").setLevel(logging.ERROR)
    LoggingFactory.get_logger("langchain.embeddings").setLevel(logging.ERROR)
    LoggingFactory.get_logger("py.warnings").setLevel(logging.ERROR)

patch_all(unittest=settings.patch_unittest)

init_logging(settings.LOGGER_FIX_LIST.split(","))

schedule_logger = logging.getLogger("apscheduler.executors.default")
schedule_logger.setLevel(logging.WARNING)

celery_app = create_celery(worker_concurrency=settings.CELERY_WORKER_CONCURRENCY)

if __name__ == '__main__':
    logger.info("**Starting celery worker from main.")
    celery_app.worker_main(argv=['worker', '--loglevel=info', '-P', 'solo', '-E', '--without-mingle', '--without-gossip', '--heartbeat-interval', '30' ])
