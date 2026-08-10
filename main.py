# main.py
import os
import json
from datetime import datetime, timezone, timedelta
from scraper import fetch_latest_news
from cleaner import process_and_clean_articles
from llm_reasoner import analyze_with_gemini

def run_pipeline():
    print("=" * 50)
    print("🤖 AI 决策与二阶推演系统 启动运行...")
    print("=" * 50)

    # 抓取与清洗
    raw_articles = fetch_latest_news(max_items_per_source=2)
    if not raw_articles:
        print("❌ 未获取到任何新闻数据。")
        return

    cleaned_articles = process_and_clean_articles(raw_articles)
    if not cleaned_articles:
        print("❌ 降噪后没有有效高信号数据。")
        return

    # 调用 Gemini 推演
    api_key = os.environ.get("GEMINI_API_KEY")
    final_cards = analyze_with_gemini(cleaned_articles, api_key=api_key)

    # 计算当前北京时间 (UTC+8) 并构建最终包含元数据的 JSON 数据结构
    beijing_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    
    output_data = {
        "updated_at": f"{beijing_time} (UTC+8)",
        "total_cards": len(final_cards),
        "cards": final_cards
    }

    # 保存 JSON
    output_json = json.dumps(output_data, ensure_ascii=False, indent=2)
    with open("results.json", "w", encoding="utf-8") as f:
        f.write(output_json)
        
    print(f"\n💾 结果已成功保存至 results.json | 更新时间: {beijing_time}")

if __name__ == "__main__":
    run_pipeline()
