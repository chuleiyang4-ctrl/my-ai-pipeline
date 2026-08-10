# daily_alpha.py
# 专门生成【标的胜率追踪池】与【商业化创业启发】深度报告

import os
import json
import google.generativeai as genai
from config import LLM_CONFIG
from scraper import fetch_latest_news
from cleaner import process_and_clean_articles

PRO_SYSTEM_PROMPT = """
你是一位兼具二级市场顶尖分析师与 AI 领域连续创业者视野的决策智囊。
请针对给定的最新技术与新闻列表，提炼出具有商业落地的深度分析。

请严格返回以下结构的 JSON 数据（不要包含 markdown 代码块标记）：
{
  "market_targets": [
    {
      "target_name": "标的名称/技术路线/产业链环节 (例如: 边缘算力芯片 / Jetson / 气象数据 API 供应商)",
      "direction": "Bullish / Bearish",
      "time_horizon": "短期(1-3个月) / 中长期(6-12个月)",
      "confidence_score": 85,
      "core_logic": "一句话硬核逻辑推演",
      "validation_metric": "未来用于验证该推演是否成功的真实指标 (例如: 某股票涨幅 / GitHub Star 增长率 / 某 API 掉量)"
    }
  ],
  "startup_inspirations": [
    {
      "tech_trigger": "技术源头 (例如: Google WeatherNext 预测模型)",
      "product_concept": "具体的商业化产品形态 (例如: 针对农业保险/航海货运的专业级高频天气微服务)",
      "target_customers": "付费客户群体 (例如: 跨境物流公司、高尔夫球场运营方)",
      "monetization_model": "商业化变现模式 (例如: 按 API 调用量订阅 / SaaS 月费)",
      "mvp_difficulty": "Low / Medium / High"
    }
  ]
}
"""

def generate_daily_alpha():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ 未找到 GEMINI_API_KEY，跳过 Alpha 分析。")
        return

    raw = fetch_latest_news(max_items_per_source=2)
    cleaned = process_and_clean_articles(raw)
    
    # 拼接所有的简报供一次性全局推理
    summary_text = "\n".join([f"- [{a['source_name']}] {a['title']}: {a['summary'][:200]}" for a in cleaned])

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=LLM_CONFIG["model_name"],
        system_instruction=PRO_SYSTEM_PROMPT
    )

    print("\n🚀 正在生成【标的胜率追踪】与【商业化创业启发】深度报告...")
    try:
        response = model.generate_content(f"以下是今日 AI 领域最新核心突破:\n{summary_text}")
        text = response.text.strip().replace("```json", "").replace("```", "")
        alpha_data = json.loads(text)

        # 存入专门供深度栏目使用的 alpha_results.json
        with open("alpha_results.json", "w", encoding="utf-8") as f:
            json.dump(alpha_data, f, ensure_ascii=False, indent=2)
        print("💾 深度 Alpha 报告已保存至 alpha_results.json")
    except Exception as e:
        print(f"❌ Alpha 分析生成失败: {str(e)}")

if __name__ == "__main__":
    generate_daily_alpha()
