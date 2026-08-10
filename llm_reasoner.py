# llm_reasoner.py
import os
import json
import google.generativeai as genai
from config import LLM_CONFIG

SYSTEM_PROMPT = """
你是一位顶尖的科技与 AI 产业链分析师。
请针对给定的新闻/技术进展，提取核心【事实摘要】，并深入分析其【一阶直接影响】与【二阶推演传导】。

你必须严格返回以下 JSON 数组格式（不要包含 markdown 代码块标记）：
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
    if not api_key:
        print("⚠️ 未找到 GEMINI_API_KEY，跳过 AI 推演分析。")
        return []

    if not articles:
        return []

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=LLM_CONFIG["model_name"],
        system_instruction=SYSTEM_PROMPT
    )

    input_text = "请分析以下最新 AI 资讯:\n\n"
    for i, a in enumerate(articles, 1):
        input_text += f"{i}. [{a.get('source_name', '未知源')}] {a.get('title', '')}\n原始摘要: {a.get('summary', '')}\n\n"

    try:
        response = model.generate_content(input_text)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        reasoned_data = json.loads(clean_text)
        return reasoned_data
    except Exception as e:
        print(f"❌ Gemini 推理分析生成失败: {str(e)}")
        return []
