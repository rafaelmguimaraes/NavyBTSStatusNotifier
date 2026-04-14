"""Fetch the latest ferry operation bulletin and notify it to Telegram."""

from datetime import date, datetime, timedelta, timezone
from enum import IntEnum
import hashlib
from html import unescape
import json
import logging
import os
import re
import sys
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from parsel import Selector
import requests

ITS_CATEGORY_ID = 6
ITS_POSTS_API_URL = "https://www.internacionaltravessias.com.br/wp-json/wp/v2/posts"
ITS_OPERACAO_FEED_URL = (
    "https://www.internacionaltravessias.com.br/category/operacao/feed/"
)
TIMEOUT = 15
LOG_DIR = "logs"
STATE_DIR = "state"
STATE_FILE = os.path.join(STATE_DIR, "last_status.json")
SOURCE_MAX_AGE = timedelta(hours=48)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json,application/rss+xml,text/xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}
SUMMARY_PATTERNS = (
    re.compile(r"\boperam os ferries\b", re.IGNORECASE),
    re.compile(r"\best[aã]o em opera[cç][aã]o\b", re.IGNORECASE),
    re.compile(r"\bmovimento\b", re.IGNORECASE),
)


class ErrorCode(IntEnum):
    SUCCESS = 0
    TOKEN_NOT_AVAILABLE = 2
    FETCH_FAILED = 3
    STATUS_NOT_FOUND = 4
    TELEGRAM_FAILED = 5
    STALE_SOURCE = 6


class TokenNotAvailableException(Exception):
    """Raised when Telegram credentials are missing."""


class FetchStatusException(Exception):
    """Raised when the Navy website cannot be fetched."""


class StatusNotFoundException(Exception):
    """Raised when the status cannot be extracted from the page."""


class TelegramNotificationException(Exception):
    """Raised when the Telegram API rejects or fails the notification."""


class StaleSourceException(Exception):
    """Raised when the fetched bulletin is too old to trust."""


def configure_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"{date.today().isoformat()}.log")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)


def build_http_session():
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    return session


def load_tokens():
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise TokenNotAvailableException(
            "TELEGRAM_TOKEN or TELEGRAM_CHAT_ID is not configured."
        )
    return token, chat_id


def clean_text(value):
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def extract_paragraphs(html_content):
    selector = Selector(text=f"<root>{html_content}</root>")
    paragraphs = []
    for paragraph in selector.xpath("//p"):
        text = clean_text(" ".join(paragraph.xpath(".//text()").getall()))
        if text:
            paragraphs.append(text)
    return paragraphs


def select_summary_paragraph(paragraphs):
    for pattern in SUMMARY_PATTERNS:
        for paragraph in paragraphs:
            if pattern.search(paragraph):
                return paragraph

    for paragraph in paragraphs:
        if len(paragraph) >= 40:
            return paragraph

    raise StatusNotFoundException(
        "Operation bulletin was fetched, but no usable summary paragraph was found."
    )


def parse_api_bulletin(payload):
    title = clean_text(payload["title"]["rendered"])
    link = payload["link"]
    published_at = datetime.fromisoformat(payload["date_gmt"]).replace(
        tzinfo=timezone.utc
    )
    paragraphs = extract_paragraphs(payload["content"]["rendered"])
    summary = select_summary_paragraph(paragraphs)
    return {
        "source": "Internacional Travessias",
        "source_kind": "wp-json",
        "title": title,
        "link": link,
        "published_at": published_at,
        "summary": summary,
    }


def fetch_latest_bulletin_from_api(session):
    try:
        response = session.get(
            ITS_POSTS_API_URL,
            params={
                "categories": ITS_CATEGORY_ID,
                "per_page": 1,
                "orderby": "date",
                "order": "desc",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise FetchStatusException(
            f"Error fetching operation bulletin from WordPress API: {exc}"
        ) from exc
    except ValueError as exc:
        raise FetchStatusException(
            f"Invalid JSON returned by WordPress API: {exc}"
        ) from exc

    if not payload:
        raise StatusNotFoundException("No operation bulletin was returned by the API.")

    return parse_api_bulletin(payload[0])


def parse_feed_bulletin(feed_xml):
    namespaces = {"content": "http://purl.org/rss/1.0/modules/content/"}
    root = ElementTree.fromstring(feed_xml)
    item = root.find("./channel/item")
    if item is None:
        raise StatusNotFoundException(
            "No operation bulletin was returned by the RSS feed."
        )

    title = clean_text(item.findtext("title"))
    link = clean_text(item.findtext("link"))
    pub_date = item.findtext("pubDate")
    content = item.findtext("content:encoded", default="", namespaces=namespaces)
    if not content:
        content = item.findtext("description", default="")

    try:
        published_at = parsedate_to_datetime(pub_date).astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise FetchStatusException(
            f"Invalid publication date in RSS feed: {exc}"
        ) from exc

    paragraphs = extract_paragraphs(content)
    summary = select_summary_paragraph(paragraphs)
    return {
        "source": "Internacional Travessias",
        "source_kind": "rss",
        "title": title,
        "link": link,
        "published_at": published_at,
        "summary": summary,
    }


def fetch_latest_bulletin_from_feed(session):
    try:
        response = session.get(ITS_OPERACAO_FEED_URL, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchStatusException(
            f"Error fetching operation bulletin from RSS feed: {exc}"
        ) from exc

    try:
        return parse_feed_bulletin(response.text)
    except ElementTree.ParseError as exc:
        raise FetchStatusException(f"Invalid RSS returned by source: {exc}") from exc


def ensure_recent_bulletin(bulletin):
    age = datetime.now(timezone.utc) - bulletin["published_at"]
    if age > SOURCE_MAX_AGE:
        raise StaleSourceException(
            "Latest operation bulletin is stale: "
            f"published at {bulletin['published_at'].isoformat()}."
        )


def fetch_latest_operation_bulletin():
    session = build_http_session()
    errors = []
    saw_stale_source = False

    for fetcher in (fetch_latest_bulletin_from_api, fetch_latest_bulletin_from_feed):
        try:
            bulletin = fetcher(session)
            ensure_recent_bulletin(bulletin)
            return bulletin
        except (
            FetchStatusException,
            StatusNotFoundException,
            StaleSourceException,
        ) as exc:
            if isinstance(exc, StaleSourceException):
                saw_stale_source = True
            errors.append(str(exc))

    if saw_stale_source:
        raise StaleSourceException(" | ".join(errors))

    raise FetchStatusException(" | ".join(errors))


def build_status_hash(summary):
    normalized_summary = clean_text(summary).lower()
    return hashlib.sha256(normalized_summary.encode("utf-8")).hexdigest()


def load_previous_state():
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, encoding="utf-8") as state_file:
            return json.load(state_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise FetchStatusException(f"Error reading saved state: {exc}") from exc


def save_current_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as state_file:
            json.dump(state, state_file, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise FetchStatusException(f"Error saving state: {exc}") from exc


def build_state_payload(bulletin, summary_hash):
    return {
        "summary_hash": summary_hash,
        "summary": bulletin["summary"],
        "title": bulletin["title"],
        "link": bulletin["link"],
        "published_at": bulletin["published_at"].isoformat(),
        "source": bulletin["source"],
        "source_kind": bulletin["source_kind"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_telegram_message(bulletin):
    return (
        f"{bulletin['title']}\n"
        f"{bulletin['summary']}\n\n"
        f"Fonte: {bulletin['source']}\n"
        f"{bulletin['link']}"
    )


def notify_by_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        response = requests.post(url, data=payload, timeout=TIMEOUT)
        response.raise_for_status()
        response_json = response.json()
    except requests.RequestException as exc:
        raise TelegramNotificationException(
            f"Error contacting Telegram API: {exc}"
        ) from exc

    if not response_json.get("ok"):
        description = response_json.get("description", "unknown Telegram error")
        raise TelegramNotificationException(
            f"Telegram API returned an error: {description}"
        )


def main():
    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        telegram_token, telegram_chat_id = load_tokens()
        bulletin = fetch_latest_operation_bulletin()
        previous_state = load_previous_state()
        summary_hash = build_status_hash(bulletin["summary"])
        current_state = build_state_payload(bulletin, summary_hash)

        logger.info(
            "Latest bulletin fetched via %s: %s",
            bulletin["source_kind"],
            bulletin["title"],
        )

        if previous_state and previous_state.get("summary_hash") == summary_hash:
            logger.info("Operation summary unchanged. Skipping Telegram notification.")
            save_current_state(current_state)
            return ErrorCode.SUCCESS

        notify_by_telegram(
            telegram_token,
            telegram_chat_id,
            build_telegram_message(bulletin),
        )
        save_current_state(current_state)
        logger.info("Updated bulletin sent successfully: %s", bulletin["summary"])
        return ErrorCode.SUCCESS
    except TokenNotAvailableException as exc:
        logger.error(str(exc))
        return ErrorCode.TOKEN_NOT_AVAILABLE
    except FetchStatusException as exc:
        logger.error(str(exc))
        return ErrorCode.FETCH_FAILED
    except StaleSourceException as exc:
        logger.error(str(exc))
        return ErrorCode.STALE_SOURCE
    except StatusNotFoundException as exc:
        logger.error(str(exc))
        return ErrorCode.STATUS_NOT_FOUND
    except TelegramNotificationException as exc:
        logger.error(str(exc))
        return ErrorCode.TELEGRAM_FAILED
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        return ErrorCode.FETCH_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
