import json
import os
import logging
from datetime import datetime, timezone, timedelta

from config import PREDICTIONS_FILE, GEMINI_API_KEY, GEMINI_MODEL, CATEGORY_KEYWORDS, DEFAULT_CATEGORY

logger = logging.getLogger(__name__)


def _load_predictions() -> list[dict]:
    if os.path.exists(PREDICTIONS_FILE):
        try:
            with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load {PREDICTIONS_FILE}: {e}")
    return []


def _save_predictions(predictions: list[dict]) -> None:
    with open(PREDICTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)


def _generate_id() -> str:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    predictions = _load_predictions()
    existing = [p.get("id", "") for p in predictions]
    counter = 1
    while f"pred_{date_str}_{counter:03d}" in existing:
        counter += 1
    return f"pred_{date_str}_{counter:03d}"


def _infer_category(title: str, summary: str = "") -> str:
    text = (title + " " + summary).lower()
    scores: dict[str, int] = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return DEFAULT_CATEGORY


def add_prediction(title: str, summary: str, source_url: str, confidence: int = 75,
                   category: str = "", verify_metric: str = "", verify_window: str = "6-12个月") -> dict:
    predictions = _load_predictions()

    if not category:
        category = _infer_category(title, summary)

    created_at = datetime.now(timezone.utc)
    deadline = created_at + timedelta(days=180)

    pred_record = {
        "id": _generate_id(),
        "created_at": created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "category": category,
        "prediction": f"{title} — {summary}",
        "verify_metric": verify_metric or f"Market and technology adoption metrics for {category}",
        "verify_window": verify_window,
        "verify_deadline": deadline.strftime("%Y-%m-%d"),
        "confidence_at_creation": max(50, min(99, confidence)),
        "status": "pending",
        "resolution": None,
        "resolution_date": None,
        "resolution_reasoning": None,
        "source_url": source_url,
    }

    predictions.append(pred_record)
    _save_predictions(predictions)
    logger.info(f"Added prediction {pred_record['id']} to {PREDICTIONS_FILE}")
    return pred_record


def _build_verification_prompt(prediction: dict, related_news: list[dict]) -> str:
    pred_text = f"{prediction.get('prediction', '')}"
    metric = prediction.get("verify_metric", "")
    category = prediction.get("category", "")

    news_text = ""
    for i, news in enumerate(related_news[:5], 1):
        news_text += f"\nNews {i}: {news.get('title', '')}\nSummary: {news.get('summary', '')}\n"

    return f"""You are a senior AI industry analyst verifying a historical prediction against current news.

HISTORICAL PREDICTION:
{pred_text}

VERIFICATION METRIC:
{metric}

CATEGORY: {category}

RELATED CURRENT NEWS:{news_text}

Based on the current news, determine if the original prediction has been:
- "hit": The prediction has been largely validated by events
- "miss": The prediction has been contradicted or proven wrong
- "partial": The prediction shows some signs of being correct but is not fully validated

Output ONLY a valid JSON object with these fields:
- "status": One of "hit", "miss", or "partial"
- "resolution_reasoning": A brief 2-3 sentence explanation of your judgment
- "has_sufficient_evidence": true/false indicating whether current news provides enough evidence to make a judgment

Rules:
- If current news is insufficient, set "has_sufficient_evidence" to false and choose the most conservative status.
- Be rigorous and evidence-based.
- Output ONLY JSON, no markdown code blocks.
"""


def _query_llm_for_verification(prediction: dict, related_news: list[dict], client=None) -> dict | None:
    if not GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not configured, skipping LLM verification")
        return None

    try:
        if client is None:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            client = genai.GenerativeModel(GEMINI_MODEL)

        prompt = _build_verification_prompt(prediction, related_news)
        response = client.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()

        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1:
            raw_text = raw_text[start:end + 1]

        result = json.loads(raw_text)
        return result

    except Exception as e:
        logger.warning(f"LLM verification failed for {prediction.get('id', 'N/A')}: {e}")
        return None


def verify_predictions(current_news: list[dict] | None = None) -> list[dict]:
    predictions = _load_predictions()
    now = datetime.now(timezone.utc)
    updated = False
    results: list[dict] = []

    client = None
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            client = genai.GenerativeModel(GEMINI_MODEL)
        except Exception as e:
            logger.warning(f"Failed to init Gemini for verification: {e}")

    for i, pred in enumerate(predictions):
        if pred.get("status") != "pending":
            continue

        deadline_str = pred.get("verify_deadline", "")
        if not deadline_str:
            continue

        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        if now < deadline:
            continue

        category = pred.get("category", "")
        related_news = []
        if current_news:
            related_news = [n for n in current_news if n.get("category") == category][:5]
        if not related_news:
            related_news = current_news[:3] if current_news else []

        if not related_news:
            logger.info(f"No related news for prediction {pred['id']}, keeping pending")
            results.append(pred)
            continue

        verification = _query_llm_for_verification(pred, related_news, client=client)

        if verification is None:
            results.append(pred)
            continue

        has_evidence = verification.get("has_sufficient_evidence", False)
        if not has_evidence:
            logger.info(f"Insufficient evidence for {pred['id']}, keeping pending")
            results.append(pred)
            continue

        status = verification.get("status", "pending")
        if status not in ("hit", "miss", "partial"):
            status = "pending"

        predictions[i]["status"] = status
        predictions[i]["resolution"] = status
        predictions[i]["resolution_date"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        predictions[i]["resolution_reasoning"] = verification.get("resolution_reasoning", "")
        updated = True
        results.append(predictions[i])
        logger.info(f"Prediction {pred['id']} resolved: {status}")

    if updated:
        _save_predictions(predictions)
        logger.info(f"Verification complete, {len(results)} predictions evaluated")
    else:
        logger.info("No predictions required verification")

    return results


def get_all_predictions() -> list[dict]:
    return _load_predictions()


def compute_winrate(predictions: list[dict] | None = None) -> dict:
    if predictions is None:
        predictions = _load_predictions()

    total_hit = 0
    total_miss = 0
    total_partial = 0
    by_category: dict[str, dict] = {}
    by_confidence_bucket: dict[str, dict] = {}

    for pred in predictions:
        status = pred.get("status", "")
        category = pred.get("category", "Unknown")
        conf = pred.get("confidence_at_creation", 0)

        if category not in by_category:
            by_category[category] = {"hit": 0, "miss": 0, "partial": 0, "total": 0}
        by_category[category]["total"] += 1

        bucket = "low(<70%)"
        if conf >= 80:
            bucket = "high(≥80%)"
        elif conf >= 70:
            bucket = "mid(70-79%)"

        if bucket not in by_confidence_bucket:
            by_confidence_bucket[bucket] = {"hit": 0, "miss": 0, "partial": 0, "total": 0}
        by_confidence_bucket[bucket]["total"] += 1

        if status == "hit":
            total_hit += 1
            by_category[category]["hit"] += 1
            by_confidence_bucket[bucket]["hit"] += 1
        elif status == "miss":
            total_miss += 1
            by_category[category]["miss"] += 1
            by_confidence_bucket[bucket]["miss"] += 1
        elif status == "partial":
            total_partial += 1
            by_category[category]["partial"] += 1
            by_confidence_bucket[bucket]["partial"] += 1

    resolved = total_hit + total_miss + total_partial
    weighted_correct = total_hit + total_partial * 0.5
    overall_winrate = round(weighted_correct / resolved * 100, 1) if resolved > 0 else 0.0

    cat_stats = {}
    for cat, data in by_category.items():
        total = data["hit"] + data["miss"] + data["partial"]
        if total > 0:
            weighted = data["hit"] + data["partial"] * 0.5
            cat_stats[cat] = {
                "winrate": round(weighted / total * 100, 1),
                "hit": data["hit"],
                "miss": data["miss"],
                "partial": data["partial"],
                "total": total,
            }

    conf_stats = {}
    for bucket, data in by_confidence_bucket.items():
        total = data["hit"] + data["miss"] + data["partial"]
        if total > 0:
            weighted = data["hit"] + data["partial"] * 0.5
            conf_stats[bucket] = {
                "actual_winrate": round(weighted / total * 100, 1),
                "hit": data["hit"],
                "miss": data["miss"],
                "partial": data["partial"],
                "total": total,
            }

    pending = [p for p in predictions if p.get("status") == "pending"]
    resolved_list = [p for p in predictions if p.get("status") in ("hit", "miss", "partial")]

    return {
        "overall_winrate": overall_winrate,
        "total_resolved": resolved,
        "total_pending": len(pending),
        "total_predictions": len(predictions),
        "by_category": cat_stats,
        "by_confidence_bucket": conf_stats,
        "pending": pending,
        "resolved": resolved_list,
    }