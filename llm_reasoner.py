# llm_reasoner.py
# 负责将清洗后的新闻发送给 Gemini 大模型进行“二阶思维”投资推演

import os
import json
import google.generativeai as genai
from config import LLM_CONFIG

# 结构化推演 Prompt 模板
SYSTEM_PROMPT = """
你是一位资深的科技与金融投资分析师，擅长使用二阶思维（Second-Order Thinking）推演科技突破与政策事件。
请对输入的 AI 领域新闻进行深度分析，并严格按照指定的 JSON 格式输出结果。

必须包含以下字段：
1. event_summary: 1句精炼的事实摘要（去除任何公关夸大修饰）。
2. direct_impact: 一阶直接影响（直接利好或利空谁）。
3. second_order_chain: 二阶产业链传导推演（分析上下游、供需关系、替代路线或 Jevons 悖论影响）。
4. target_impact: 受益与受损的相关标的或技术路线列表（包含 winners 和 losers）。
5. signal_level: 信号重要级别（High / Medium / Low）。

请仅输出标准的 JSON 格式字符串，不要包含 Markdown 标记（如 ```json）。
"""

def analyze_with_gemini(cleaned_articles, api_key=None):
    """
    调用 Gemini 3.6 Flash 对新闻列表进行二阶推演
    """
    # 获取 API Key（优先从环境变量读取，也可以直接传入）
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        print("⚠️ 未找到 GEMINI_API_KEY，跳过大模型推演阶段。")
        return []

    # 配置 Gemini API
    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        model_name=LLM_CONFIG["model_name"],
        system_instruction=SYSTEM_PROMPT
    )

    reasoning_results = []
    print("\n🧠 正在调用 Gemini 3.6 Flash 进行二阶投资逻辑推演...")

    for article in cleaned_articles:
        prompt_input = f"""
        [新闻标题]: {article.get('title')}
        [来源机构]: {article.get('source_name')}
        [文章摘要/正文]: {article.get('summary')}
        """
        
        try:
            # 调用 Gemini 生成分析
            response = model.generate_content(prompt_input)
            response_text = response.text.strip()
            
            # 清理可能包含的 Markdown 标记
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            analysis_json = json.loads(response_text)
            
            # 将原始新闻信息与推演结果合并
            combined_result = {
                "source_name": article.get("source_name"),
                "title": article.get("title"),
                "link": article.get("link"),
                "published": article.get("published"),
                "reasoning": analysis_json
            }
            reasoning_results.append(combined_result)
            print(f"✨ 成功推演: {article.get('title')[:25]}...")
            
        except Exception as e:
            print(f"❌ 推演 {article.get('title')[:15]}... 时出错: {str(e)}")

    print(f"✅ 推演完成！共生成 {len(reasoning_results)} 条结构化推演卡片。")
    return reasoning_results

# 单独测试逻辑
if __name__ == "__main__":
    test_cleaned = [{
        "source_name": "OpenAI",
        "title": "API Price Reduced by 90%",
        "link": "[https://openai.com](https://openai.com)",
        "published": "Today",
        "summary": "OpenAI announces a massive price cut for API inference."
    }]
    # 模拟运行
    print("代码结构加载正常。")
