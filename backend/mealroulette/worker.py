import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("MealRoulette worker placeholder started")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
