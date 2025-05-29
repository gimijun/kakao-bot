from flask import Flask, jsonify, request
import feedparser
import re

app = Flask(__name__)

# 메모리 캐시 (Render에서는 디스크 캐시는 비권장)
image_cache = {}

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

def extract_image(description, fallback="https://via.placeholder.com/200"):
    match = re.search(r'<img[^>]+src="([^">]+)"', description)
    return match.group(1) if match else fallback

def fetch_rss_news(category_key, max_count=5):
    category = CATEGORY_INFO[category_key]
    feed = feedparser.parse(category["rss"])
    news_items = []

    for entry in feed.entries[:max_count]:
        title = entry.title.strip()
        desc = getattr(entry, "summary", "").strip()
        url = entry.link

        # 이미지 캐싱
        if url in image_cache:
            image = image_cache[url]
        else:
            image = extract_image(desc)
            image_cache[url] = image

        news_items.append({
            "title": title,
            "description": desc[:60],
            "link": url,
            "image": image
        })

    return news_items

def list_card_response(category_key):
    category = CATEGORY_INFO[category_key]
    articles = fetch_rss_news(category_key)

    if not articles:
        items = [{
            "title": f"{category['title']} 뉴스를 불러올 수 없습니다.",
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
    return "카카오 뉴스봇 RSS + 이미지 캐싱 정상 작동 중입니다."

@app.route("/news/<category>", methods=["POST"])
def news_category(category):
    if category not in CATEGORY_INFO:
        return jsonify({"error": "카테고리 없음"}), 404
    return list_card_response(category)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
