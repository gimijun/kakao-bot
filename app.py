from flask import Flask, jsonify, request
import feedparser

app = Flask(__name__)

def fetch_naver_rss_news(category_url, max_count=5):
    feed = feedparser.parse(category_url)
    news_items = []
    for entry in feed.entries[:max_count]:
        news_items.append({
            "title": entry.title,
            "description": entry.summary if hasattr(entry, "summary") else "",
            "link": entry.link,
            "image": "https://via.placeholder.com/200"
        })
    return news_items

def list_card_response(title, category_url):
    articles = fetch_naver_rss_news(category_url)
    if not articles:
        items = [{
            "title": f"{title} 관련 뉴스를 불러오지 못했습니다.",
            "description": "잠시 후 다시 시도해 주세요.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": { "web": "https://news.naver.com" }
        }]
    else:
        items = [{
            "title": news["title"],
            "description": news["description"][:50],
            "imageUrl": news["image"],
            "link": { "web": news["link"] }
        } for news in articles]

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "listCard": {
                        "header": { "title": f"{title} 뉴스 TOP {len(items)}" },
                        "items": items,
                        "buttons": [
                            {
                                "label": "전체 뉴스 보기",
                                "action": "webLink",
                                "webLinkUrl": category_url
                            }
                        ]
                    }
                }
            ]
        }
    })

# 카테고리별 라우트 정의
@app.route("/news/politics", methods=["POST"])
def news_politics():
    return list_card_response("정치", "https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=100&viewType=rss")

@app.route("/news/economy", methods=["POST"])
def news_economy():
    return list_card_response("경제", "https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=101&viewType=rss")

@app.route("/news/society", methods=["POST"])
def news_society():
    return list_card_response("사회", "https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=102&viewType=rss")

@app.route("/news/culture", methods=["POST"])
def news_culture():
    return list_card_response("문화", "https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=103&viewType=rss")

@app.route("/news/world", methods=["POST"])
def news_world():
    return list_card_response("세계", "https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=104&viewType=rss")

@app.route("/news/it", methods=["POST"])
def news_it():
    return list_card_response("IT/과학", "https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=105&viewType=rss")

@app.route("/news/entertainment", methods=["POST"])
def news_entertainment():
    return list_card_response("연예", "https://entertain.naver.com/rss")

@app.route("/news/sports", methods=["POST"])
def news_sports():
    return list_card_response("스포츠", "https://sports.news.naver.com/rss/news.nhn")

# 헬스체크
@app.route("/", methods=["GET"])
def health():
    return "네이버 RSS 기반 뉴스봇 정상 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
