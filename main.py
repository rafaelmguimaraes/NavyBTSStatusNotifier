"""
NavyBTSStatusNotifier is a Python script that fetches the status updates from
the Capitania dos Portos da Bahia (Navy) website regarding the Bahia de Todos
os Santos (BTS) area and sends notifications to a specified Telegram chat.
"""
import logging
import logging.handlers
import os
from parsel import Selector
import requests
from enum import Enum

TELEGRAM_TOKEN = None
TELEGRAM_CHAT_ID = None
BASE_URL = "https://www.marinha.mil.br/cpba/"
TIMEOUT = 15
LOG_FILE = "status.log"


class ErrorCode(Enum):
    TIMEOUT = 1
    TOKEN_NOT_AVAILABLE = 2


class TimeoutException(Exception):
    pass


class TokenNotAvailableException(Exception):
    pass


def load_tokens():
    try:
        TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
        TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
        return TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    except KeyError:
        raise TokenNotAvailableException()


def fetch_bts_status_from_navy():
    try:
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        response.raise_for_status()
        selector = Selector(text=response.text)
        statusBTS = selector.css('#block-block-17 strong::text').get()
        return statusBTS
    except requests.ReadTimeout:
        raise TimeoutException()
    except requests.RequestException as e:
        raise Exception("Error fetching BTS status: " + str(e))


def notify_by_telegram(token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{token}" \
              "/sendMessage?chat_id={chat_id}&text={message}"
        requests.get(url, timeout=15).json()
    except requests.RequestException as e:
        raise Exception("Error fetching Telegram API: " + str(e))


def main():
    logging.basicConfig(
        filename=LOG_FILE,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG
    )
    logger = logging.getLogger(__name__)
    try:
        TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = load_tokens()
        statusBTS = fetch_bts_status_from_navy()
        notify_by_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, statusBTS)
        logger.info(statusBTS)
    except TokenNotAvailableException:
        logger.error("Telegram token not available. Exiting.")
    except TimeoutException:
        logger.error("Timeout occurred while fetching BTS status.")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
