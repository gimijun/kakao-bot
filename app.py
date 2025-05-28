from flask import Flask, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def extract_image_from_article(article_url):
    try:
        res = requests.get(article_url, timeout=5, headers={
            "User-Agent": "Mozilla/5.0"
        })
        if res.status_code != 200:
            return None
        soup = BeautifulSoup(res.text, "html.parser")
        img_tag = soup.find("meta", property="og:image")
        if img_tag and img_tag.get("content"):
            return img_tag["content"]
        return None
    except Exception:
        return None

def fetch_rss_news(category_url, max_count=5):
    feed = feedparser.parse(category_url)
    news_items = []
    for entry in feed.entries[:max_count]:
        image_url = extract_image_from_article(entry.link) or "https://via.placeholder.com/200"
        news_items.append({
            "title": entry.title,
            "description": getattr(entry, "summary", "")[:50],
            "link": entry.link,
            "image": image_url
        })
    return news_items

def list_card_response(title, category_url):
    articles = fetch_rss_news(category_url)
    if not articles:
        items = [{
            "title": f"{title} 관련 뉴스를 불러오지 못했습니다.",
            "description": "잠시 후 다시 시도해 주세요.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": {"web": "https://news.donga.com/"}
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
                    "header": {"title": f"{title} 뉴스 TOP {len(items)}"},
                    "items": items,
                    "buttons": [{
                        "label": "전체 뉴스 보기",
                        "action": "webLink",
                        "webLinkUrl": category_url
                    }]
                }
            }]
        }
    })

@app.route("/news/politics", methods=["POST"])
def news_politics():
    return list_card_response("정치", "https://rss.donga.com/politics.xml")

@app.route("/news/economy", methods=["POST"])
def news_economy():
    return list_card_response("경제", "https://rss.donga.com/economy.xml")

@app.route("/news/society", methods=["POST"])
def news_society():
    return list_card_response("사회", "https://rss.donga.com/society.xml")

@app.route("/news/culture", methods=["POST"])
def news_culture():
    return list_card_response("문화", "https://rss.donga.com/culture.xml")

@app.route("/news/world", methods=["POST"])
def news_world():
    return list_card_response("세계", "https://rss.donga.com/international.xml")

@app.route("/news/it", methods=["POST"])
def news_it():
    return list_card_response("IT/과학", "https://rss.donga.com/it.xml")

@app.route("/news/entertainment", methods=["POST"])
def news_entertainment():
    return list_card_response("연예", "https://rss.donga.com/entertainment.xml")

@app.route("/news/sports", methods=["POST"])
def news_sports():
    return list_card_response("스포츠", "https://rss.donga.com/sports.xml")

@app.route("/", methods=["GET"])
def health():
    return "RSS 기반 뉴스봇 정상 작동 중입니다."

if __name__ == "__main__":
    # 필요 패키지 설치: pip install flask feedparser requests beautifulsoup4
    app.run(host="0.0.0.0", port=5000)
