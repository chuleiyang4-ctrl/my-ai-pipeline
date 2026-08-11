import re
import logging

from config import SUMMARY_MAX_LEN

logger = logging.getLogger(__name__)

_SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE)
_STYLE_RE = re.compile(r"<style[^>]*>.*?</style>", re.DOTALL | re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def clean_html(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = _SCRIPT_RE.sub("", raw_text)
    text = _STYLE_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def truncate_summary(text: str, max_len: int = SUMMARY_MAX_LEN) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rsplit(" ", 1)[0]
    if not truncated:
        truncated = text[:max_len]
    return truncated.rstrip(".,;:!?") + "..."


def clean_news_item(item: dict) -> dict:
    cleaned = item.copy()
    raw_summary = cleaned.get("summary", "")
    cleaned["summary"] = truncate_summary(clean_html(raw_summary))
    cleaned["title"] = clean_html(cleaned.get("title", ""))
    return cleaned


def clean_all(items: list[dict]) -> list[dict]:
    cleaned = [clean_news_item(item) for item in items]
    cleaned = [item for item in cleaned if item.get("title") and item.get("summary")]
    logger.info(f"Cleaned items: {len(cleaned)}")
    return cleaned