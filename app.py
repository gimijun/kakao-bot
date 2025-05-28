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
            "image": "https://via.placeholder.com/200"  # RSS에 이미지 없음
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
                                "webLinkUrl": "https://news.naver.com"
                            }
                        ]
                    }
                }
            ]
        }
    })

# 예: 정치 뉴스
@app.route("/news/politics", methods=["POST"])
def news_politics():
    rss_url = "https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=100&viewType=rss"
    return list_card_response("정치", rss_url)

# 헬스 체크용
@app.route("/", methods=["GET"])
def health():
    return "네이버 RSS 기반 뉴스봇 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
