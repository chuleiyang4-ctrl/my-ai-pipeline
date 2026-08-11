import json
import re
import logging
from datetime import datetime, timezone

from config import GEMINI_API_KEY, GEMINI_MODEL, CATEGORY_KEYWORDS, DEFAULT_CATEGORY

logger = logging.getLogger(__name__)


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


def _fallback_reason(item: dict) -> dict:
    title = item.get("title", "")
    summary = item.get("summary", "")

    if not summary:
        sentences = re.split(r'(?<=[.!?])\s+', title)
        summary = " ".join(sentences[:2]) if len(sentences) >= 2 else title

    category = _infer_category(title, summary)

    return {
        "title": title,
        "summary": summary,
        "first_order_impact": f"Direct market movement expected for entities related to: {category}",
        "second_order_reasoning": f"Ripple effects across the {category} value chain may create new opportunities or risks for adjacent sectors.",
        "source_url": item.get("link", ""),
        "category": category,
        "reasoned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "is_fallback": True,
    }


def _build_prompt(item: dict) -> str:
    return f"""You are a senior AI industry analyst. Analyze this news and output a JSON object with the EXACT fields specified below.

NEWS TITLE: {item.get('title', '')}
NEWS SUMMARY: {item.get('summary', '')}
NEWS LINK: {item.get('link', '')}

Output a JSON object with these fields:
- "summary": A concise 2-3 sentence factual summary of the news. THIS FIELD IS MANDATORY — never leave it empty. If the news is too brief, extract the first 1-2 sentences from the title/summary as a fallback.
- "first_order_impact": The immediate direct impact of this news (1-2 sentences).
- "second_order_reasoning": The longer-term ripple effects and second-order consequences (2-3 sentences).
- "category": Classify the news into ONE of these categories: 具身智能, 金融Agent, 基础模型, LLM, AI应用, AI基础设施, AI安全, 多模态.
- "source_url": The original news link.

Rules:
- Output ONLY valid JSON, no markdown code blocks, no explanations.
- All content must be in English.
- Keep each field concise and analytical.
- "summary" MUST NOT be empty — if information is insufficient, construct a reasonable summary from available text.
"""


def _strip_markdown_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def _try_parse_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def reason_item(item: dict, client=None) -> dict:
    if not GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not configured, using fallback reasoning")
        return _fallback_reason(item)

    try:
        if client is None:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            client = genai.GenerativeModel(GEMINI_MODEL)

        prompt = _build_prompt(item)
        response = client.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )

        raw_text = response.text.strip()
        raw_text = _strip_markdown_fence(raw_text)
        parsed = _try_parse_json(raw_text)

        if parsed is None:
            logger.warning(f"Failed to parse JSON from LLM response, using fallback for: {item.get('title', 'N/A')}")
            return _fallback_reason(item)

        title = parsed.get("summary", "")
        if not title:
            parsed["summary"] = item.get("summary", "") or item.get("title", "")

        if not parsed.get("source_url"):
            parsed["source_url"] = item.get("link", "")

        if not parsed.get("category") or parsed.get("category") not in [
            "具身智能", "金融Agent", "基础模型", "LLM", "AI应用", "AI基础设施", "AI安全", "多模态"
        ]:
            parsed["category"] = _infer_category(item.get("title", ""), parsed.get("summary", ""))

        parsed["title"] = item.get("title", "")
        parsed["reasoned_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        parsed["is_fallback"] = False
        return parsed

    except Exception as e:
        logger.warning(f"LLM reasoning failed for '{item.get('title', 'N/A')}': {e}")
        return _fallback_reason(item)


def reason_all(items: list[dict]) -> list[dict]:
    results: list[dict] = []
    client = None

    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            client = genai.GenerativeModel(GEMINI_MODEL)
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")

    for item in items:
        try:
            result = reason_item(item, client=client)
            results.append(result)
        except Exception as e:
            logger.warning(f"Error reasoning item '{item.get('title', 'N/A')}': {e}")
            results.append(_fallback_reason(item))

    logger.info(f"Reasoned {len(results)} items")
    return results