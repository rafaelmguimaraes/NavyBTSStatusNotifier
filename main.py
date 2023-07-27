import logging
import logging.handlers
import os
from parsel import Selector
import requests


def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger_file_handler = logging.handlers.RotatingFileHandler(
        "status.log",
        maxBytes=1024 * 1024,
        backupCount=1,
        encoding="utf8",
    )
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger_file_handler.setFormatter(formatter)
    logger.addHandler(logger_file_handler)
    return logger


def load_enviroment(logger):
    try:
        TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
        TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
        logger.info("Tokens read successfully!")
        return TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    except KeyError:
        logger.info("Token not available!")
        raise


def load_bts_status_from_navy():
    try:
        response = requests.get("https://www.marinha.mil.br/cpba/", timeout=15)
        selector = Selector(text=response.text)
        statusBTS = selector.css('#block-block-17 strong::text').get()
        return statusBTS
    except requests.ReadTimeout:
        return "Timeout (www.marinha.mil.br/cpba) - " + response.status_code


def send_message_to_telegram(token, chat_id, message, logger):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
        response = requests.get(url, timeout=15).json()
        logger.info(message)
    except requests.ReadTimeout:
        logger.info("Timeout (api.telegram.org/bot) - " + response.status_code)


if __name__ == "__main__":
    logger = setup_logger()
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = load_enviroment(logger)
    statusBTS = load_bts_status_from_navy()
    message = "CONDIÇÕES DE NAVEGABILIDADE NA BTS: " + statusBTS
    send_message_to_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message, logger)
