import logging
import signal
import sys
import threading
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mealroulette.core.config import get_settings
from mealroulette.services.telegram_reminder import TelegramReminderService
from mealroulette.services.telegram_updates import TelegramUpdateService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _session_factory():
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    return engine, sessionmaker(bind=engine)


def run_scheduled_reminder() -> None:
    engine, session_factory = _session_factory()
    with session_factory() as db:
        try:
            result = TelegramReminderService(db).run_scheduled_reminder()
            if result is not None:
                logger.info("Scheduled Telegram reminder sent to %s subscriber(s)", result.recipient_count)
        except Exception:
            logger.exception("Scheduled Telegram reminder failed")
    engine.dispose()


def poll_telegram_updates(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        engine, session_factory = _session_factory()
        try:
            with session_factory() as db:
                processed = TelegramUpdateService(db).poll_once()
                if processed:
                    logger.info("Processed %s Telegram update(s)", processed)
        except Exception:
            logger.exception("Telegram update polling failed")
        finally:
            engine.dispose()
        stop_event.wait(1)


def main() -> None:
    stop_event = threading.Event()
    if get_settings().telegram_bot_token:
        threading.Thread(target=poll_telegram_updates, args=(stop_event,), daemon=True).start()
        logger.info("Telegram /subscribe polling enabled")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot commands disabled")

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run_scheduled_reminder, trigger="cron", minute="*", id="telegram_daily_reminder")
    logger.info("MealRoulette worker started")

    def shutdown(_signum: int, _frame: object) -> None:
        logger.info("Shutting down worker")
        stop_event.set()
        scheduler.shutdown(wait=False)
        time.sleep(0.2)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    scheduler.start()


if __name__ == "__main__":
    main()
