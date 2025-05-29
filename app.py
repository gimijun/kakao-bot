from flask import Flask, jsonify, request
import feedparser

app = Flask(__name__)

CATEGORY_INFO = {
    "politics": {
        "title": "정치",
        "rss": "https://rss.donga.com/politics.xml",
        "link": "https://www.donga.com/news/Politics"
    },
    "economy": {
        "title": "경제",
        "rss": "https://rss.donga.com/economy.xml",
        "link": "https://www.donga.com/news/Economy"
    },
    "society": {
        "title": "사회",
        "rss": "https://rss.donga.com/society.xml",
        "link": "https://www.donga.com/news/Society"
    },
    "culture": {
        "title": "문화",
        "rss": "https://rss.donga.com/culture.xml",
        "link": "https://www.donga.com/news/Culture"
    },
    "world": {
        "title": "국제",
        "rss": "https://rss.donga.com/international.xml",
        "link": "https://www.donga.com/news/Inter"
    },
    "it": {
        "title": "IT/과학",
        "rss": "https://rss.donga.com/it.xml",
        "link": "https://www.donga.com/news/It"
    },
    "entertainment": {
        "title": "연예",
        "rss": "https://rss.donga.com/entertainment.xml",
        "link": "https://www.donga.com/news/Entertainment"
    },
    "sports": {
        "title": "스포츠",
        "rss": "https://rss.donga.com/sports.xml",
        "link": "https://www.donga.com/news/Sports"
    }
}

def fetch_rss_news(category_key, max_count=5):
    category = CATEGORY_INFO[category_key]
    feed = feedparser.parse(category["rss"])
    news_items = []
    for entry in feed.entries[:max_count]:
        news_items.append({
            "title": entry.title.strip(),
            "description": getattr(entry, "summary", "").strip()[:60],
            "link": entry.link,
            "image": "https://via.placeholder.com/200"  # 추후 이미지 크롤링 적용 가능
        })
    return news_items

def list_card_response(category_key):
    category = CATEGORY_INFO[category_key]
    articles = fetch_rss_news(category_key)
    if not articles:
        items = [{
            "title": f"{category['title']} 관련 뉴스를 불러오지 못했습니다.",
            "description": "잠시 후 다시 시도해 주세요.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": {"web": category["link"]}
        }]
    else:
        items = [{
            "title": a["title"],
            "description": a["description"],
            "imageUrl": a["image"],
            "link": {"web": a["link"]}
        } for a in articles]

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [{
                "listCard": {
                    "header": {"title": f"{category['title']} 뉴스 TOP {len(items)}"},
                    "items": items,
                    "buttons": [{
                        "label": "더보기",
                        "action": "webLink",
                        "webLinkUrl": category["link"]
                    }]
                }
            }]
        }
    })

@app.route("/", methods=["GET"])
def health():
    return "카카오 뉴스봇(RSS) 작동 중"

# 카테고리별 라우터 생성
for cat_key in CATEGORY_INFO:
    endpoint = f"/news/{cat_key}"
    app.add_url_rule(endpoint, endpoint, lambda cat=cat_key: list_card_response(cat), methods=["POST"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
