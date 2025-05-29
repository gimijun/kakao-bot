from flask import Flask, jsonify, request
import feedparser
import re

app = Flask(__name__)

def extract_image_from_entry(entry):
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'url' in media:
                return media['url']

    desc = entry.get("summary", "") or entry.get("description", "")
    match = re.search(r'<img[^>]+src="([^">]+)"', desc)
    if match:
        return match.group(1)

    return "https://t1.daumcdn.net/media/img-section/news_card_default.png"

def fetch_rss_news(rss_url, max_count=5):
    feed = feedparser.parse(rss_url)
    news_items = []
    for entry in feed.entries[:max_count]:
        title = re.sub(r'<[^>]+>', '', entry.title)
        image = extract_image_from_entry(entry)
        link = entry.link
        news_items.append({
            "title": title,
            "image": image,
            "link": link
        })
    return news_items

def list_card_response(title, rss_url, web_url):
    articles = fetch_rss_news(rss_url)
    if not articles:
        items = [{
            "title": f"{title} 관련 뉴스를 불러오지 못했습니다.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": { "web": web_url }
        }]
    else:
        items = [{
            "title": a["title"],
            "imageUrl": a["image"],
            "link": { "web": a["link"] }
        } for a in articles]

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [{
                "listCard": {
                    "header": { "title": f"{title} 뉴스 TOP {len(items)}" },
                    "items": items,
                    "buttons": [{
                        "label": "더보기",
                        "action": "webLink",
                        "webLinkUrl": web_url
                    }]
                }
            }]
        }
    })

# 주요 카테고리별 라우트
@app.route("/news/politics", methods=["POST"])
def politics():
    return list_card_response("정치", "https://rss.donga.com/politics.xml", "https://www.donga.com/news/Politics")

@app.route("/news/economy", methods=["POST"])
def economy():
    return list_card_response("경제", "https://rss.donga.com/economy.xml", "https://www.donga.com/news/Economy")

@app.route("/news/society", methods=["POST"])
def society():
    return list_card_response("사회", "https://rss.donga.com/national.xml", "https://www.donga.com/news/National")

@app.route("/news/world", methods=["POST"])
def world():
    return list_card_response("국제", "https://rss.donga.com/international.xml", "https://www.donga.com/news/Inter")

@app.route("/news/science", methods=["POST"])
def science():
    return list_card_response("의학과학", "https://rss.donga.com/science.xml", "https://www.donga.com/news/Science")

@app.route("/news/culture", methods=["POST"])
def culture():
    return list_card_response("문화연예", "https://rss.donga.com/culture.xml", "https://www.donga.com/news/Culture")

@app.route("/news/sports", methods=["POST"])
def sports():
    return list_card_response("스포츠", "https://rss.donga.com/sports.xml", "https://www.donga.com/news/Sports")

@app.route("/news/entertainment", methods=["POST"])
def entertainment():
    return list_card_response("엔터테인먼트", "https://rss.donga.com/sportsdonga/entertainment.xml", "https://sports.donga.com/Entertainment")

@app.route("/", methods=["GET"])
def health():
    return "카카오 뉴스봇(RSS 최적화) 정상 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
