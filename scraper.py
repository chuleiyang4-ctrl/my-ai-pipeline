import re
import time
import logging
import feedparser
import requests
from datetime import datetime, timezone

from config import RSS_FEEDS, FALLBACK_NEWS, REQUEST_HEADERS, MAX_NEWS_ITEMS, CATEGORY_KEYWORDS, DEFAULT_CATEGORY

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def infer_category(title: str, summary: str = "") -> str:
    text = (title + " " + summary).lower()
    scores: dict[str, int] = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text:
                score += 1
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return DEFAULT_CATEGORY


def fetch_feed(feed_info: dict) -> list[dict]:
    name = feed_info["name"]
    url = feed_info["url"]
    default_cat = feed_info.get("category", DEFAULT_CATEGORY)
    items: list[dict] = []

    try:
        logger.info(f"Fetching RSS feed: {name}")
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.text)

        for entry in parsed.entries[:10]:
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()
            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = time.strftime("%Y-%m-%dT%H:%M:%SZ", entry.published_parsed)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = time.strftime("%Y-%m-%dT%H:%M:%SZ", entry.updated_parsed)
            else:
                published = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            clean_summary = re.sub(r"<[^>]+>", "", raw_summary).strip()

            category = infer_category(title, clean_summary)
            if category == DEFAULT_CATEGORY and default_cat != DEFAULT_CATEGORY:
                category = default_cat

            if title and link:
                items.append({
                    "title": title,
                    "link": link,
                    "published": published,
                    "summary": clean_summary[:500],
                    "category": category,
                })

        logger.info(f"Fetched {len(items)} items from {name}")
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {name}: {e}")
    except Exception as e:
        logger.warning(f"Error parsing {name}: {e}")

    return items


def scrape_all() -> list[dict]:
    all_items: list[dict] = []

    for feed_info in RSS_FEEDS:
        try:
            items = fetch_feed(feed_info)
            all_items.extend(items)
        except Exception as e:
            logger.warning(f"Unexpected error for {feed_info['name']}: {e}")
            continue

    if not all_items:
        logger.warning("All feeds returned empty. Using fallback news list.")
        all_items = [item.copy() for item in FALLBACK_NEWS]

    all_items = all_items[:MAX_NEWS_ITEMS]
    logger.info(f"Total scraped items: {len(all_items)}")
    return all_items