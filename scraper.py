# scraper.py
# 负责从 config.py 里的 RSS 链接提取最新新闻标题与长文内容

import feedparser
from config import RSS_SOURCES

def fetch_latest_news(max_items_per_source=3):
    """
    遍历 config.py 里的 RSS 链接，抓取最新的文章列表
    :param max_items_per_source: 每个源只取最新的几条，避免重复和 token 浪费
    """
    all_articles = []

    print("🚀 开始抓取最新的 AI 官方资讯...")
    
    for source in RSS_SOURCES:
        url = source["url"]
        print(f"📡 正在抓取: {source['name']} ({url})")
        
        try:
            # 解析 RSS Feed
            feed = feedparser.parse(url)
            
            # 如果抓取到的列表为空，跳过
            if not feed.entries:
                print(f"⚠️  {source['name']} 暂无新更新或抓取失败。")
                continue
                
            # 只截取最新的前 N 条（例如前 3 条）
            for entry in feed.entries[:max_items_per_source]:
                article = {
                    "source_id": source["id"],
                    "source_name": source["name"],
                    "category": source["category"],
                    "title": entry.get("title", "无标题"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", entry.get("updated", "未知时间")),
                    # 获取正文或摘要内容
                    "summary": entry.get("summary", entry.get("description", ""))
                }
                all_articles.append(article)
                
        except Exception as e:
            print(f"❌ 抓取 {source['name']} 时出错: {str(e)}")

    print(f"✅ 抓取完成！共获取到 {len(all_articles)} 条最新资讯。")
    return all_articles

# 用于单独测试 scraper.py 是否正常工作的入口
if __name__ == "__main__":
    articles = fetch_latest_news(max_items_per_source=1)
    for a in articles:
        print(f"\n[{a['source_name']}] {a['title']}\n链接: {a['link']}")
