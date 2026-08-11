import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

RSS_FEEDS = [
    {"name": "MIT Technology Review - AI", "url": "https://www.technologyreview.com/feed/", "category": "基础模型"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "category": "AI应用"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "category": "具身智能"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "category": "LLM"},
    {"name": "Ars Technica AI", "url": "https://arstechnica.com/feed/", "category": "AI基础设施"},
    {"name": "AI News (Chinese)", "url": "https://www.aibase.com/rss", "category": "AI应用"},
]

FALLBACK_NEWS = [
    {
        "title": "Apple Reportedly Developing On-Device LLM for iPhone",
        "link": "https://www.reuters.com/technology/apple-developing-on-device-llm-iphone-sources-say/",
        "published": "2026-08-10T08:00:00Z",
        "summary": "Apple is reportedly working on a large language model that runs entirely on-device for iPhone, potentially reducing reliance on cloud APIs and improving privacy.",
        "category": "基础模型",
    },
    {
        "title": "Tesla Optimus Gen3 Enters Mass Production Line",
        "link": "https://electrek.co/2026/08/08/tesla-optimus-gen3-production/",
        "published": "2026-08-08T12:00:00Z",
        "summary": "Tesla has confirmed that its Optimus Gen3 humanoid robot has entered mass production, with initial units destined for Tesla's own manufacturing facilities before broader commercial availability.",
        "category": "具身智能",
    },
    {
        "title": "BlackRock Launches AI-Driven Financial Agent Platform",
        "link": "https://www.blackrock.com/corporate/ai-financial-agents",
        "published": "2026-08-07T16:00:00Z",
        "summary": "BlackRock has launched a new AI-driven financial agent platform that can autonomously execute multi-step investment research, portfolio rebalancing, and compliance checking.",
        "category": "金融Agent",
    },
    {
        "title": "NVIDIA Blackwell Ultra Chip Begins Shipping to Cloud Providers",
        "link": "https://nvidianews.nvidia.com/news/blackwell-ultra-ships",
        "published": "2026-08-05T10:00:00Z",
        "summary": "NVIDIA has begun shipping its Blackwell Ultra GPU chips to major cloud providers, promising 4x inference performance over the previous generation at the same power envelope.",
        "category": "AI基础设施",
    },
    {
        "title": "OpenAI o3 Surpasses Human Benchmarks on Multistep Reasoning",
        "link": "https://openai.com/index/o3-surpasses-human",
        "published": "2026-08-03T14:00:00Z",
        "summary": "OpenAI's o3 model has surpassed human expert benchmarks on multistep mathematical and logical reasoning tasks, marking a potential inflection point for AI research automation.",
        "category": "LLM",
    },
]

CATEGORY_KEYWORDS = {
    "具身智能": ["robot", "embodied", "humanoid", "optimus", "robotics", "具身", "人形", "机器人"],
    "金融Agent": ["finance", "trading", "investment", "fintech", "banking", "agent", "金融", "交易", "投资"],
    "基础模型": ["foundation model", "base model", "pretraining", "pre-training", "foundation", "基础模型", "预训练"],
    "LLM": ["llm", "large language", "gpt", "language model", "chatbot", "大模型", "语言模型"],
    "AI应用": ["application", "product", "app", "enterprise", "customer", "应用", "产品", "企业"],
    "AI基础设施": ["chip", "gpu", "tpu", "infrastructure", "training", "data center", "芯片", "算力", "基础设施"],
    "AI安全": ["safety", "alignment", "red team", "risk", "regulation", "安全", "对齐", "监管"],
    "多模态": ["multimodal", "vision", "image", "video", "audio", "多模态", "视觉", "图像"],
}

DEFAULT_CATEGORY = "AI应用"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

GEMINI_MODEL = "gemini-2.0-flash"
MAX_NEWS_ITEMS = 15
SUMMARY_MAX_LEN = 300
PREDICTIONS_FILE = "predictions.json"
RESULTS_FILE = "results.json"
ALPHA_RESULTS_FILE = "alpha_results.json"