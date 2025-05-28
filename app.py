from flask import Flask, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def extract_image_from_article(article_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(article_url, timeout=5, headers=headers)
        if res.status_code != 200:
            return None
        soup = BeautifulSoup(res.text, "html.parser")
        tag = soup.find("meta", property="og:image")
        if tag and tag.get("content"):
            return tag["content"]
    except:
        pass
    return "https://via.placeholder.com/120x90.png?text=No+Image"

def fetch_rss_news(category_url, max_count=5):
    feed = feedparser.parse(category_url)
    news_items = []
    for entry in feed.entries[:max_count]:
        title = entry.title.strip().replace("\n", " ")
        short_title = title if len(title) <= 40 else title[:37] + "..."
        image_url = extract_image_from_article(entry.link)
        news_items.append({
            "title": short_title,
            "link": entry.link,
            "image": image_url
        })
    return news_items

def list_card_response(title, category_url, more_url):
    articles = fetch_rss_news(category_url)
    items = [{
        "title": a["title"],
        "description": "",
        "imageUrl": a["image"],
        "link": {"web": a["link"]}
    } for a in articles]

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [{
                "listCard": {
                    "header": {"title": f"{title} 뉴스"},
                    "items": items,
                    "buttons": [
                        {
                            "label": f"{title} 이슈 더보기",
                            "action": "webLink",
                            "webLinkUrl": more_url
                        },
                        {
                            "label": "뉴스 더보기",
                            "action": "webLink",
                            "webLinkUrl": category_url
                        }
                    ]
                }
            }]
        }
    })

@app.route("/news/politics", methods=["POST"])
def news_politics():
    return list_card_response(
        "정치",
        "https://rss.donga.com/politics.xml",
        "https://www.donga.com/news/Politics"
    )

@app.route("/", methods=["GET"])
def health():
    return "정상 작동 중"

if __name__ == "__main__":
    # 설치 필요: pip install flask feedparser requests beautifulsoup4
    app.run(host="0.0.0.0", port=5000)
