# cleaner.py
# 负责对抓取到的 RSS 内容进行噪音过滤与清洗

import re

# 排除关键词列表（如果标题或摘要包含这些词，说明是噪音，直接过滤）
NOISE_KEYWORDS = [
    "hiring", "careers", "job opening", "we're hiring",  # 招聘类
    "sponsorship", "sponsor",                            # 赞助/广告类
    "meetup", "webinar", "office hours",                 # 线下/线上小活动
    "terms of service", "privacy policy"                 # 协议更新类
]

def clean_html_tags(raw_html):
    """
    去除 RSS 摘要里的 HTML 标签（如 <p>, <a>, <img> 等），只保留纯文本
    """
    if not raw_html:
        return ""
    # 使用正则表达式匹配并替换掉所有 HTML 标签
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    # 替换多个连续空格或换行
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def is_high_signal(article):
    """
    判断一条资讯是否属于高质量的“高信号”内容
    :param article: 包含 title 和 summary 的字典
    :return: True (保留) 或 False (过滤掉)
    """
    title = article.get("title", "").lower()
    summary = article.get("summary", "").lower()
    combined_text = f"{title} {summary}"

    # 1. 检查是否包含噪音关键词
    for keyword in NOISE_KEYWORDS:
        if keyword in combined_text:
            print(f"🧹 过滤噪音内容 [{keyword}]: {article.get('title')}")
            return False

    # 2. 检查内容长度：如果标题加正文太短（小于 20 个字符），可能是空数据或无效数据
    if len(combined_text) < 20:
        return False

    return True

def process_and_clean_articles(articles):
    """
    对抓取到的文章列表进行批量清洗和过滤
    """
    cleaned_list = []
    print("\n🧼 开始进行数据清洗与降噪...")

    for item in articles:
        # 清洗 HTML 标签，还原为纯文本
        item["summary"] = clean_html_tags(item.get("summary", ""))
        
        # 检验是否为有效高信号数据
        if is_high_signal(item):
            cleaned_list.append(item)

    print(f"✅ 清洗完成！原始数据 {len(articles)} 条，保留高质量数据 {len(cleaned_list)} 条。")
    return cleaned_list

# 单独测试 cleaner.py 的逻辑
if __name__ == "__main__":
    test_articles = [
        {"title": "OpenAI is hiring for Safety Team", "summary": "Apply now!"},
        {"title": "GPT-5 Release Announcement", "summary": "<p>We are excited to launch...<p>"}
    ]
    result = process_and_clean_articles(test_articles)
    print("测试结果:", result)
