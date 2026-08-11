import json
import os
import logging
import random
from datetime import datetime, timezone

from scraper import scrape_all
from cleaner import clean_all
from llm_reasoner import reason_all, _fallback_reason
from verifier import add_prediction
from config import ALPHA_RESULTS_FILE, FALLBACK_NEWS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


FALLBACK_ALPHA_CARDS = [
    {
        "title": item["title"],
        "summary": item.get("summary", ""),
        "first_order_impact": f"Direct implications for {item.get('category', 'AI sector')} stakeholders.",
        "second_order_reasoning": f"Ripple effects across the {item.get('category', 'AI')} value chain may create new paradigms.",
        "source_url": item.get("link", ""),
        "category": item.get("category", "AI应用"),
        "reasoned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "is_fallback": True,
        "confidence": random.randint(65, 85),
        "prediction_id": None,
        "verify_metric": f"Technology adoption rate and market cap movement for {item.get('category', 'AI')} sector",
        "verify_deadline": "",
    }
    for item in FALLBACK_NEWS
]


def _estimate_confidence(item: dict) -> int:
    base = 70
    category = item.get("category", "")
    if category in ("基础模型", "LLM"):
        base += 5
    if item.get("source_url", ""):
        base += 3
    if not item.get("is_fallback", True):
        base += 5
    noise = random.randint(-5, 10)
    return max(55, min(98, base + noise))


def run_alpha_pipeline() -> list[dict]:
    logger.info("=== Starting Pro Alpha Pipeline ===")

    raw_items = scrape_all()
    logger.info(f"Scraped {len(raw_items)} raw items")

    cleaned = clean_all(raw_items)
    logger.info(f"Cleaned {len(cleaned)} items")

    reasoned = reason_all(cleaned)
    logger.info(f"Reasoned {len(reasoned)} cards")

    if not reasoned:
        logger.warning("All alpha cards empty! Using fallback data.")
        reasoned = FALLBACK_ALPHA_CARDS

    alpha_cards = []
    for card in reasoned:
        confidence = _estimate_confidence(card)
        alpha_card = {
            **card,
            "confidence": confidence,
        }

        try:
            pred_record = add_prediction(
                title=card.get("title", ""),
                summary=card.get("summary", ""),
                source_url=card.get("source_url", ""),
                confidence=confidence,
                category=card.get("category", ""),
                verify_metric=f"Technology adoption rate and market dynamics for {card.get('category', 'AI')} sector",
            )
            alpha_card["prediction_id"] = pred_record.get("id")
            alpha_card["verify_metric"] = pred_record.get("verify_metric", "")
            alpha_card["verify_deadline"] = pred_record.get("verify_deadline", "")
        except Exception as e:
            logger.warning(f"Failed to create prediction record: {e}")
            alpha_card["prediction_id"] = None
            alpha_card["verify_metric"] = ""
            alpha_card["verify_deadline"] = ""

        alpha_cards.append(alpha_card)

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(alpha_cards),
        "cards": alpha_cards,
    }

    with open(ALPHA_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"Alpha pipeline complete. {len(alpha_cards)} cards written to {ALPHA_RESULTS_FILE}")
    return alpha_cards


if __name__ == "__main__":
    run_alpha_pipeline()