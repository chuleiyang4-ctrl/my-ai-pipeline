import json
from datetime import datetime
from scraper import fetch_latest_news
from cleaner import process_and_clean_articles
from llm_reasoner import analyze_articles

def run_pipeline():
    print("🚀 启动 AI 资讯二阶推演 Pipeline...")

    # 1. 抓取
    raw_articles = fetch_latest_news(max_items_per_source=2)
    print(f"📥 成功获取到 {len(raw_articles)} 条资讯。")

    # 2. 清洗
    cleaned_articles = process_and_clean_articles(raw_articles)
    if not cleaned_articles:
        cleaned_articles = raw_articles
    print(f"🧹 清洗后有效资讯: {len(cleaned_articles)} 条。")

    # 3. LLM 二阶推演
    cards = analyze_articles(cleaned_articles)

    # 4. 终极兜底机制：若 AI 推演为空（API Key 未配置或限制），自动将资讯生成卡片
    if not cards and cleaned_articles:
        print("⚠️ 未收到 AI 推演结果，自动启动基础资讯兜底填充...")
        cards = []
        for item in cleaned_articles:
            cards.append({
                "title": item.get("title", "最新 AI 科技进展"),
                "source_name": item.get("source_name", "AI 产业链观察"),
                "published_at": item.get("published_at", datetime.now().strftime("%Y-%m-%d")),
                "summary": item.get("summary", "最新 AI 产业链动态与硬核进展。"),
                "first_order_impact": f"直接影响 {item.get('source_name', '相关厂商')} 的产品研发、场景落地与计算资源调配。",
                "second_order_reasoning": "将进一步推动上游算力基础设施需求与下游企业级 Agent 场景的深度融合。"
            })

    print(f"🧠 最终生成 {len(cards)} 条卡片数据。")

    # 5. 打包输出
    output_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "cards": cards
    }

    # 6. 保存 JSON
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("💾 结果已成功更新保存至 results.json")

if __name__ == "__main__":
    run_pipeline()
