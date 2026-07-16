import logging
import signal
import sys
import threading
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mealroulette.core.config import get_settings
from mealroulette.services.backup_service import BackupService
from mealroulette.services.cooking_timer_alerts import CookingTimerAlertService
from mealroulette.services.telegram_reminder import TelegramReminderService
from mealroulette.services.scheduled_roulette import ScheduledRouletteService
from mealroulette.services.telegram_updates import TelegramUpdateService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_engine = create_engine(get_settings().database_url, pool_pre_ping=True)
_session_factory = sessionmaker(bind=_engine)


def run_scheduled_reminder() -> None:
    with _session_factory() as db:
        try:
            results = TelegramReminderService(db).run_scheduled_reminder()
            for result in results:
                logger.info("Scheduled Telegram reminder sent to %s recipient(s)", result.recipient_count)
        except Exception:
            logger.exception("Scheduled Telegram reminder failed")


def poll_telegram_updates(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        try:
            with _session_factory() as db:
                processed = TelegramUpdateService(db).poll_once()
                if processed:
                    logger.info("Processed %s Telegram update(s)", processed)
        except Exception:
            logger.exception("Telegram update polling failed")
        stop_event.wait(1)


def run_scheduled_roulette() -> None:
    with _session_factory() as db:
        try:
            from mealroulette.services.scheduler_settings import SchedulerSettingsService

            for settings_row in SchedulerSettingsService(db).list_all_rows():
                result = ScheduledRouletteService(db, household_id=settings_row.household_id).run_scheduled()
                if result is not None:
                    logger.info(
                        "Scheduled meal roulette generated %s assignments for household %s week %s",
                        result.assignments_count,
                        settings_row.household_id,
                        result.week_start_date,
                    )
        except Exception:
            logger.exception("Scheduled meal roulette failed")


def run_cooking_timer_alerts() -> None:
    with _session_factory() as db:
        try:
            processed = CookingTimerAlertService(db).process_due()
            if processed:
                logger.info("Processed %s cooking timer alert(s)", processed)
        except Exception:
            logger.exception("Cooking timer alert processing failed")


def run_scheduled_backup() -> None:
    with _session_factory() as db:
        try:
            result = BackupService(db).run_scheduled_backup()
            if result:
                logger.info("Scheduled backup created %s artifact(s)", len(result))
        except Exception:
            logger.exception("Scheduled backup failed")


def main() -> None:
    stop_event = threading.Event()
    if get_settings().telegram_bot_token:
        threading.Thread(target=poll_telegram_updates, args=(stop_event,), daemon=True).start()
        logger.info("Telegram /subscribe polling enabled")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot commands disabled")

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run_scheduled_reminder, trigger="cron", minute="*", id="telegram_daily_reminder")
    scheduler.add_job(run_scheduled_roulette, trigger="cron", minute="*", id="scheduled_meal_roulette")
    scheduler.add_job(run_scheduled_backup, trigger="cron", minute="*", id="scheduled_backup")
    scheduler.add_job(run_cooking_timer_alerts, trigger="interval", seconds=2, id="cooking_timer_alerts")
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
