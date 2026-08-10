# llm_reasoner.py
import os
import json
import re
import google.generativeai as genai
from config import LLM_CONFIG

SYSTEM_PROMPT = """
你是一位顶尖的科技与 AI 产业链分析师。
请针对给定的新闻/技术进展，提取核心【事实摘要】，并深入分析其【一阶直接影响】与【二阶推演传导】。

你必须严格返回 JSON 数组格式：
[
  {
    "title": "新闻标题/核心事件",
    "source_name": "信息源名称",
    "published_at": "发布时间",
    "summary": "事实摘要（用 1-2 句话精准概括该新闻发生的硬核事实本身）",
    "first_order_impact": "一阶直接影响（直接受益/受损的厂商、技术或业务领域）",
    "second_order_reasoning": "二阶推演（上游供应链、竞争格局变化、下游应用生态及潜在商业/投资传导）"
  }
]
"""

def analyze_articles(articles):
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # 兜底逻辑：若无 API Key 或 API 异常时保底生成结构化推演
    if not api_key or not articles:
        print("⚠️ 未找到 GEMINI_API_KEY 或资讯为空，使用结构化推演规则生成卡片...")
        fallback_cards = []
        for a in articles:
            fallback_cards.append({
                "title": a.get("title", "AI 核心技术进展"),
                "source_name": a.get("source_name", "AI 产业链观察"),
                "published_at": a.get("published_at", "最新"),
                "summary": a.get("summary", "该技术或战略动作标志着 AI 产业链基础设施与应用落地进入全新阶段。"),
                "first_order_impact": f"直接推动 {a.get('source_name', '相关厂商')} 在算力、软件生态与垂直场景的部署落地，直接赋能生态合作伙伴。",
                "second_order_reasoning": "将加速产业链上下游配套（算力/数据/高客单场景 Agent）的资本开支与商业化渗透，倒逼传统工作流重构。"
            })
        return fallback_cards

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=LLM_CONFIG.get("model_name", "gemini-1.5-flash"),
            system_instruction=SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json"}
        )

        input_text = "请分析以下最新 AI 资讯:\n\n"
        for i, a in enumerate(articles, 1):
            input_text += f"{i}. [{a.get('source_name', '未知源')}] {a.get('title', '')}\n摘要: {a.get('summary', '')}\n\n"

        response = model.generate_content(input_text)
        text = response.text.strip()
        
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        
        reasoned_data = json.loads(text.strip())
        return reasoned_data
    except Exception as e:
        print(f"❌ Gemini 推理分析生成异常 ({str(e)})，触发保底结构化卡片...")
        fallback_cards = []
        for a in articles:
            fallback_cards.append({
                "title": a.get("title", "AI 核心技术进展"),
                "source_name": a.get("source_name", "AI 产业链观察"),
                "published_at": a.get("published_at", "最新"),
                "summary": a.get("summary", "技术进展快速演进中。"),
                "first_order_impact": "直接赋能垂直领域核心厂商，提升计算效率与交互体验。",
                "second_order_reasoning": "重构上游算力与下游应用商业模式，加速企业级 Agent 采购落地。"
            })
        return fallback_cards
