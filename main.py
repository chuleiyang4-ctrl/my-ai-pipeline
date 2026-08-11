import json
import os
import logging
from datetime import datetime, timezone

from scraper import scrape_all
from cleaner import clean_all
from llm_reasoner import reason_all, _fallback_reason
from config import RESULTS_FILE, FALLBACK_NEWS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


FALLBACK_CARDS = [
    {
        "title": item["title"],
        "summary": item.get("summary", ""),
        "first_order_impact": f"Direct implications for {item.get('category', 'AI sector')} stakeholders.",
        "second_order_reasoning": f"Ripple effects across the {item.get('category', 'AI')} value chain may create new paradigms.",
        "source_url": item.get("link", ""),
        "category": item.get("category", "AI应用"),
        "reasoned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "is_fallback": True,
    }
    for item in FALLBACK_NEWS
]


def run_pipeline() -> list[dict]:
    logger.info("=== Starting Standard Pipeline ===")

    raw_items = scrape_all()
    logger.info(f"Scraped {len(raw_items)} raw items")

    cleaned = clean_all(raw_items)
    logger.info(f"Cleaned {len(cleaned)} items")

    reasoned = reason_all(cleaned)
    logger.info(f"Reasoned {len(reasoned)} cards")

    if not reasoned:
        logger.warning("All cards are empty! Using fallback data to prevent empty file overwrite.")
        reasoned = FALLBACK_CARDS

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(reasoned),
        "cards": reasoned,
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"Pipeline complete. {len(reasoned)} cards written to {RESULTS_FILE}")
    return reasoned


if __name__ == "__main__":
    run_pipeline()