"""
本地测试脚本 —— 无需 GEMINI_API_KEY 即可验证 main.py 全链路逻辑。

工作原理：
  1. 将 mock_gemini 模块注入 sys.modules["google.generativeai"]
  2. 设置环境变量 GEMINI_API_KEY="mock-key-for-testing" 激活 LLM 路径
  3. 运行 main.py 的 run_pipeline()
  4. 打印最终 results.json 的关键字段供人工检查

用法：
  python run_local_test.py

验证点：
  ✓ scraper 能抓取/回退新闻
  ✓ cleaner 能清洗 HTML 并截断摘要
  ✓ llm_reasoner 走 LLM 路径（非 fallback），正确解析 JSON
  ✓ _strip_markdown_fence 能处理 ```json 围栏
  ✓ 字段补全逻辑（summary 为空时兜底、source_url 缺失时补全）
  ✓ main.py 空数据保底机制
  ✓ results.json 写入带 updated_at 时间戳
"""

import sys
import os
import json

# ============================================================
# 第一步：在 import 任何项目模块之前，注入 mock Gemini 模块
# ============================================================
import mock_gemini

# 将 mock 模块注册为 google.generativeai
# 这样 llm_reasoner.py 中 `import google.generativeai as genai` 会拿到 mock
sys.modules["google.generativeai"] = mock_gemini

# ============================================================
# 第二步：设置环境变量，激活 LLM 路径（绕过 fallback）
# ============================================================
os.environ["GEMINI_API_KEY"] = "mock-key-for-testing"

# ============================================================
# 第三步：运行 pipeline
# ============================================================
print("=" * 60)
print("  LOCAL TEST: main.py pipeline with mock Gemini API")
print("=" * 60)
print()

# 需要重新 import config，因为它在模块加载时读取环境变量
# 由于 config 可能已被其他模块缓存，我们用 importlib 重新加载
import importlib
import config
importlib.reload(config)

# 同样重新加载依赖 config 的模块
import scraper
importlib.reload(scraper)
import cleaner
importlib.reload(cleaner)
import llm_reasoner
importlib.reload(llm_reasoner)
import main
importlib.reload(main)

print("\n[1/4] Running scraper...")
raw_items = scraper.scrape_all()
print(f"  -> Scraped {len(raw_items)} items")
for item in raw_items[:3]:
    print(f"     • [{item.get('category', '?')}] {item.get('title', '?')[:60]}")

print("\n[2/4] Running cleaner...")
cleaned = cleaner.clean_all(raw_items)
print(f"  -> Cleaned {len(cleaned)} items")

print("\n[3/4] Running llm_reasoner (LLM path)...")
reasoned = llm_reasoner.reason_all(cleaned)
print(f"  -> Reasoned {len(reasoned)} cards")

# 验证：检查是否有 LLM 路径的卡片（is_fallback=False）
llm_cards = [c for c in reasoned if not c.get("is_fallback", True)]
fallback_cards = [c for c in reasoned if c.get("is_fallback", True)]
print(f"  -> LLM path cards: {len(llm_cards)}")
print(f"  -> Fallback cards: {len(fallback_cards)}")

if llm_cards:
    print("\n  --- Sample LLM card ---")
    sample = llm_cards[0]
    print(f"  title:              {sample.get('title', '')[:70]}")
    print(f"  summary:            {sample.get('summary', '')[:70]}")
    print(f"  category:           {sample.get('category', '')}")
    print(f"  first_order_impact: {sample.get('first_order_impact', '')[:70]}")
    print(f"  second_order:       {sample.get('second_order_reasoning', '')[:70]}")
    print(f"  source_url:         {sample.get('source_url', '')[:70]}")
    print(f"  is_fallback:        {sample.get('is_fallback')}")

print("\n[4/4] Running main.run_pipeline() (writes results.json)...")
cards = main.run_pipeline()

# ============================================================
# 第四步：验证 results.json 输出
# ============================================================
print()
print("=" * 60)
print("  VERIFICATION: results.json")
print("=" * 60)

results_path = "results.json"
if os.path.exists(results_path):
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"  updated_at:  {data.get('updated_at', 'MISSING')}")
    print(f"  total:       {data.get('total', 'MISSING')}")
    print(f"  cards count: {len(data.get('cards', []))}")

    cards = data.get("cards", [])
    if cards:
        print(f"\n  --- First card fields check ---")
        c = cards[0]
        required_fields = ["title", "summary", "first_order_impact",
                           "second_order_reasoning", "source_url", "category"]
        for field in required_fields:
            val = c.get(field, "")
            status = "✓" if val else "✗ EMPTY"
            print(f"  {status} {field:25s}: {str(val)[:60]}")

        # 统计分类分布
        cats = {}
        for card in cards:
            cat = card.get("category", "Unknown")
            cats[cat] = cats.get(cat, 0) + 1
        print(f"\n  --- Category distribution ---")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"     {cat}: {count}")

        # 统计 fallback vs LLM
        llm_count = sum(1 for c in cards if not c.get("is_fallback", True))
        fb_count = sum(1 for c in cards if c.get("is_fallback", True))
        print(f"\n  --- Path distribution ---")
        print(f"     LLM path:      {llm_count}")
        print(f"     Fallback path: {fb_count}")
else:
    print(f"  ✗ results.json not found!")

print()
print("=" * 60)
if llm_cards:
    print("  ✓ TEST PASSED: LLM path is working with mock Gemini API")
else:
    print("  ✗ TEST FAILED: No LLM path cards generated")
print("=" * 60)
