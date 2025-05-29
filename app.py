from flask import Flask, jsonify, request
import feedparser

app = Flask(__name__)

def fetch_rss_news(rss_url, max_count=5):
    feed = feedparser.parse(rss_url)
    news_items = []
    for entry in feed.entries[:max_count]:
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "image": "https://t1.daumcdn.net/media/img-section/news_card_default.png"  # 카카오 기본 이미지 사용
        })
    return news_items

def list_card_response(title, rss_url):
    articles = fetch_rss_news(rss_url)
    if not articles:
        items = [{
            "title": f"{title} 관련 뉴스를 불러오지 못했습니다.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": { "web": "https://news.daum.net/" }
        }]
    else:
        items = [{
            "title": article["title"],
            "imageUrl": article["image"],
            "link": { "web": article["link"] }
        } for article in articles]

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
                        "webLinkUrl": rss_url.replace(".xml", "")  # 예: RSS 링크 제거한 뉴스 페이지
                    }]
                }
            }]
        }
    })

@app.route("/news/politics", methods=["POST"])
def politics(): return list_card_response("정치", "https://rss.donga.com/politics.xml")

@app.route("/news/economy", methods=["POST"])
def economy(): return list_card_response("경제", "https://rss.donga.com/economy.xml")

@app.route("/news/society", methods=["POST"])
def society(): return list_card_response("사회", "https://rss.donga.com/society.xml")

@app.route("/news/culture", methods=["POST"])
def culture(): return list_card_response("문화", "https://rss.donga.com/culture.xml")

@app.route("/news/world", methods=["POST"])
def world(): return list_card_response("국제", "https://rss.donga.com/international.xml")

@app.route("/news/it", methods=["POST"])
def it(): return list_card_response("IT/과학", "https://rss.donga.com/it.xml")

@app.route("/news/entertainment", methods=["POST"])
def entertainment(): return list_card_response("연예", "https://rss.donga.com/entertainment.xml")

@app.route("/news/sports", methods=["POST"])
def sports(): return list_card_response("스포츠", "https://rss.donga.com/sports.xml")

@app.route("/", methods=["GET"])
def health(): return "카카오 뉴스봇(RSS) 정상 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
