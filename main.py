# main.py
import json
from datetime import datetime
from scraper import fetch_latest_news
from cleaner import process_and_clean_articles
from llm_reasoner import analyze_articles

def run_pipeline():
    print("🚀 启动 AI 资讯二阶推演 Pipeline...")

    # 1. 抓取
    raw_articles = fetch_latest_news(max_items_per_source=2)
    print(f"📥 成功抓取到 {len(raw_articles)} 条原始资讯。")

    # 2. 清洗
    cleaned_articles = process_and_clean_articles(raw_articles)
    print(f"🧹 清洗去重后剩余 {len(cleaned_articles)} 条有效资讯。")

    # 3. LLM 二阶推演
    cards = analyze_articles(cleaned_articles)
    print(f"🧠 Gemini 完成 {len(cards)} 条推演卡片的生成。")

    # 4. 打包输出
    output_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "cards": cards
    }

    # 5. 保存 JSON
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("💾 结果已成功更新保存至 results.json")

if __name__ == "__main__":
    run_pipeline()
