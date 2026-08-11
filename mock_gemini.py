"""
Mock Gemini API 模块 —— 用于本地无 API Key 时模拟 LLM 响应。

工作原理：
  在 import llm_reasoner 之前，将本模块注入 sys.modules["google.generativeai"]，
  这样 llm_reasoner.py 中的 `import google.generativeai as genai` 会拿到 mock 对象，
  从而走完整的 LLM 路径（而非 fallback 路径），验证 JSON 解析、字段补全等逻辑。

用法：
  python run_local_test.py
"""

import json
import re
import logging
from datetime import datetime, timezone

logger = logging.getLogger("mock_gemini")

# 分类关键词映射（与 config.py 保持一致）
_CATEGORY_KEYWORDS = {
    "具身智能": ["robot", "embodied", "humanoid", "optimus", "robotics", "具身", "人形", "机器人"],
    "金融Agent": ["finance", "trading", "investment", "fintech", "banking", "agent", "金融", "交易", "投资"],
    "基础模型": ["foundation model", "base model", "pretraining", "pre-training", "foundation", "基础模型", "预训练"],
    "LLM": ["llm", "large language", "gpt", "language model", "chatbot", "大模型", "语言模型"],
    "AI应用": ["application", "product", "app", "enterprise", "customer", "应用", "产品", "企业"],
    "AI基础设施": ["chip", "gpu", "tpu", "infrastructure", "training", "data center", "芯片", "算力", "基础设施"],
    "AI安全": ["safety", "alignment", "red team", "risk", "regulation", "安全", "对齐", "监管"],
    "多模态": ["multimodal", "vision", "image", "video", "audio", "多模态", "视觉", "图像"],
}

_DEFAULT_CATEGORY = "AI应用"


def _infer_category(title: str, summary: str) -> str:
    text = (title + " " + summary).lower()
    scores: dict[str, int] = {}
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return _DEFAULT_CATEGORY


def _extract_field(prompt: str, field_name: str) -> str:
    """从 prompt 中提取 NEWS TITLE / NEWS SUMMARY / NEWS LINK 的值"""
    pattern = rf"{field_name}:\s*(.*?)(?:\n[A-Z]+:|\n\n|$)"
    match = re.search(pattern, prompt, re.DOTALL)
    return match.group(1).strip() if match else ""


# 各分类对应的模拟分析模板
_TEMPLATES = {
    "具身智能": {
        "first_order_impact": "Direct impact on robotics manufacturers and supply chain partners; potential labor cost reduction in manufacturing facilities.",
        "second_order_reasoning": "Mass deployment of humanoid robots could reshape global labor markets, triggering policy responses and creating new service economies around robot maintenance, training, and insurance.",
    },
    "金融Agent": {
        "first_order_impact": "Immediate efficiency gains for asset management firms; potential fee compression in traditional advisory services.",
        "second_order_reasoning": "Institutional adoption of autonomous financial agents may trigger regulatory scrutiny and reshape competitive dynamics between traditional banks and AI-native fintech entrants.",
    },
    "基础模型": {
        "first_order_impact": "Direct reduction in cloud API dependency; improved data privacy for end users; potential cost savings for developers.",
        "second_order_reasoning": "On-device or open foundation models could democratize AI access, shift power from cloud providers to edge device makers, and enable new privacy-preserving application categories.",
    },
    "LLM": {
        "first_order_impact": "Reasoning capability breakthrough may disrupt knowledge-intensive sectors including legal, medical, and scientific research workflows.",
        "second_order_reasoning": "If AI reasoning surpasses human experts consistently, it could trigger fundamental reevaluation of knowledge work economics and accelerate AI integration in enterprise decision-making pipelines.",
    },
    "AI应用": {
        "first_order_impact": "New AI application launches expand addressable market; enterprise adoption curve may accelerate for AI-powered workflows.",
        "second_order_reasoning": "Broad application adoption creates data feedback loops that improve model quality, potentially establishing winner-take-all dynamics in vertical AI SaaS categories.",
    },
    "AI基础设施": {
        "first_order_impact": "Performance leap gives cloud providers significant inference cost advantage; GPU supplier extends market dominance.",
        "second_order_reasoning": "Infrastructure performance jumps enable previously infeasible AI workloads, potentially reshaping cloud provider competitive dynamics and triggering new capital expenditure cycles.",
    },
    "AI安全": {
        "first_order_impact": "Regulatory pressure creates immediate demand for AI governance, compliance, and auditing tools.",
        "second_order_reasoning": "Compliance requirements may create a new AI governance market category and raise barriers to entry for smaller AI startups lacking compliance resources.",
    },
    "多模态": {
        "first_order_impact": "Multimodal capabilities unlock new application scenarios in content creation, accessibility, and visual understanding.",
        "second_order_reasoning": "Convergence of text, image, and video understanding may become table stakes for enterprise AI, accelerating consolidation of single-modal providers.",
    },
}


class MockResponse:
    """模拟 Gemini API 的响应对象"""

    def __init__(self, text: str):
        self.text = text


class MockGenerativeModel:
    """模拟 Gemini GenerativeModel 客户端"""

    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name
        self._call_count = 0

    def generate_content(self, prompt: str, generation_config: dict | None = None) -> MockResponse:
        self._call_count += 1

        # 验证 generation_config 是否正确传入
        if generation_config and generation_config.get("response_mime_type") != "application/json":
            logger.warning("Mock: generation_config.response_mime_type is not application/json")

        # 从 prompt 解析新闻信息
        title = _extract_field(prompt, "NEWS TITLE")
        summary = _extract_field(prompt, "NEWS SUMMARY")
        link = _extract_field(prompt, "NEWS LINK")

        category = _infer_category(title, summary)
        template = _TEMPLATES.get(category, _TEMPLATES[_DEFAULT_CATEGORY])

        # 构造模拟的 JSON 响应
        mock_result = {
            "summary": f"{title}. {summary}" if summary else title,
            "first_order_impact": template["first_order_impact"],
            "second_order_reasoning": template["second_order_reasoning"],
            "category": category,
            "source_url": link,
        }

        # 偶尔模拟带 markdown 围栏的返回（测试 _strip_markdown_fence 逻辑）
        if self._call_count % 5 == 0:
            raw_text = f"```json\n{json.dumps(mock_result, ensure_ascii=False)}\n```"
        else:
            raw_text = json.dumps(mock_result, ensure_ascii=False)

        logger.info(f"Mock Gemini response #{self._call_count} for: {title[:50]}...")

        return MockResponse(raw_text)


class MockGenAIModule:
    """模拟 google.generativeai 模块入口"""

    def __init__(self):
        self._configured = False
        self._api_key = None

    def configure(self, api_key: str = "", **kwargs):
        self._configured = True
        self._api_key = api_key
        logger.info(f"Mock genai.configure() called with api_key={'***' + api_key[-4:] if api_key else 'EMPTY'}")

    def GenerativeModel(self, model_name: str = "mock-model", **kwargs) -> MockGenerativeModel:
        if not self._configured:
            logger.warning("Mock: GenerativeModel() called before configure()")
        return MockGenerativeModel(model_name)


# 创建模块级单例，供 sys.modules 注入使用
_instance = MockGenAIModule()

# 暴露 configure 和 GenerativeModel 作为模块级函数（模拟 google.generativeai 的接口）
def configure(api_key: str = "", **kwargs):
    _instance.configure(api_key, **kwargs)

def GenerativeModel(model_name: str = "mock-model", **kwargs) -> MockGenerativeModel:
    return _instance.GenerativeModel(model_name, **kwargs)
