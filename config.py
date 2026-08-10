# config.py
# 存储核心官方 RSS 信息源及最新模型配置

RSS_SOURCES = [
    {
        "id": "openai",
        "name": "OpenAI News & Research",
        "category": "Model Vendor",
        "url": "https://openai.com/news/rss.xml"
    },
    {
        "id": "anthropic",
        "name": "Anthropic News",
        "category": "Model Vendor",
        "url": "https://www.anthropic.com/rss.xml"
    },
    {
        "id": "google_deepmind",
        "name": "Google DeepMind Blog",
        "category": "Model Vendor",
        "url": "https://deepmind.google/blog/rss.xml"
    },
    {
        "id": "xai",
        "name": "xAI (Grok) News",
        "category": "Model Vendor",
        "url": "https://rsshub.app/xai/news"
    },
    {
        "id": "nvidia",
        "name": "NVIDIA Technical Blog",
        "category": "Hardware & Infrastructure",
        "url": "https://developer.nvidia.com/blog/feed/"
    },
    {
        "id": "meta_ai",
        "name": "Meta AI Blog",
        "category": "Open Source Models",
        "url": "https://ai.meta.com/blog/rss/"
    },
    {
        "id": "huggingface",
        "name": "Hugging Face Blog",
        "category": "Ecosystem & Models",
        "url": "https://huggingface.co/blog/feed.xml"
    }
    # 💡 以后想加新源，直接在这里按同样格式粘贴新的大括号即可
]

LLM_CONFIG = {
    "provider": "gemini",
    "model_name": "gemini-3.6-flash"
}
