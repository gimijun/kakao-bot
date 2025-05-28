from flask import Flask, jsonify, request
import feedparser

app = Flask(__name__)

RSS_FEEDS = {
    "정치": "https://news.naver.com/rss/politics.xml",
    "경제": "https://news.naver.com/rss/economy.xml",
    "사회": "https://news.naver.com/rss/society.xml",
    "문화": "https://news.naver.com/rss/culture.xml",
    "IT": "https://news.naver.com/rss/technology.xml",
    "국제": "https://news.naver.com/rss/world.xml",
    "스포츠": "https://sports.news.naver.com/rss/index.nhn",
    "연예": "https://news.naver.com/rss/entertainment.xml"
}

def fetch_rss_news(category, count=5):
    feed_url = RSS_FEEDS.get(category)
    if not feed_url:
        return []

    try:
        feed = feedparser.parse(feed_url)
        entries = feed.entries[:count]
        return [{
            "title": entry.title,
            "description": entry.get("summary", "")[:50],
            "link": entry.link,
            "image": "https://via.placeholder.com/200"
        } for entry in entries]
    except Exception as e:
        print("❌ RSS 파싱 오류:", e)
        return []

def list_card_response(category):
    articles = fetch_rss_news(category)
    if not articles:
        items = [{
            "title": f"{category} 뉴스 없음",
            "description": "RSS 피드에서 기사를 불러오지 못했습니다.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": { "web": "https://news.naver.com" }
        }]
    else:
        items = [{
            "title": news["title"],
            "description": news["description"],
            "imageUrl": news["image"],
            "link": { "web": news["link"] }
        } for news in articles]

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "listCard": {
                        "header": { "title": f"{category} 뉴스 TOP {len(items)}" },
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

@app.route("/news/<category>", methods=["POST"])
def news_by_category(category):
    return list_card_response(category)

@app.route("/", methods=["GET"])
def health():
    return "카카오 뉴스봇 RSS 서버 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
