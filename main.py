# main.py
# 数据管道（Pipeline）总指挥控制入口

import os
import json
from scraper import fetch_latest_news
from cleaner import process_and_clean_articles
from llm_reasoner import analyze_with_gemini

def run_pipeline():
    print("=" * 50)
    print("🤖 AI 降噪与二阶决策推演系统 启动运行...")
    print("=" * 50)

    # 第一步：抓取 RSS 原始数据（每个源暂定抓取最新 2 条）
    raw_articles = fetch_latest_news(max_items_per_source=2)
    if not raw_articles:
        print("❌ 未获取到任何新闻数据，程序终止。")
        return

    # 第二步：规则数据清洗与降噪
    cleaned_articles = process_and_clean_articles(raw_articles)
    if not cleaned_articles:
        print("❌ 经过降噪后没有有效高信号数据，程序终止。")
        return

    # 第三步：调用 Gemini 进行二阶推演
    # 提示：可以在环境变量中设置 GEMINI_API_KEY，或直接在下面填入字符串测试
    api_key = os.environ.get("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY_HERE"
    
    final_cards = analyze_with_gemini(cleaned_articles, api_key=api_key)

    # 第四步：输出并打印推演卡片 JSON 结果
    print("\n" + "=" * 50)
    print("📊 最终生成的结构化推演卡片 (JSON):")
    print("=" * 50)
    
    output_json = json.dumps(final_cards, ensure_ascii=False, indent=2)
    print(output_json)

    # 也可以将结果保存为本地的 results.json 文件
    with open("results.json", "w", encoding="utf-8") as f:
        f.write(output_json)
    print("\n💾 结果已成功保存至 results.json")

if __name__ == "__main__":
    run_pipeline()
