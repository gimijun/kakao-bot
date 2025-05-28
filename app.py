from flask import Flask, jsonify, request
import feedparser
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ✅ RSS에서 제목/링크/이미지만 추출 (빠르고 안정적)
def fetch_rss_news(category_url, max_count=5):
    feed = feedparser.parse(category_url)
    news_items = []
    for entry in feed.entries[:max_count]:
        title = entry.title.strip().replace("\n", " ")
        short_title = title if len(title) <= 40 else title[:37] + "..."

        image_url = None
        if "media_content" in entry and entry.media_content:
            image_url = entry.media_content[0].get("url")

        news_items.append({
            "title": short_title,
            "link": entry.link,
            "image": image_url or "https://via.placeholder.com/120x90.png?text=No+Image"
        })
    return news_items

# ✅ 카카오톡 listCard 응답 포맷 생성
def list_card_response(title, category_url):
    articles = fetch_rss_news(category_url)
    if not articles:
        items = [{
            "title": f"{title} 관련 뉴스를 불러오지 못했습니다.",
            "description": "잠시 후 다시 시도해 주세요.",
            "imageUrl": "https://via.placeholder.com/120x90.png?text=No+Image",
            "link": {"web": "https://news.donga.com/"}
        }]
    else:
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

# ✅ 카테고리별 엔드포인트
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
    return list_card_response("국제", "https://rss.donga.com/international.xml")

@app.route("/news/it", methods=["POST"])
def news_it():
    return list_card_response("IT/과학", "https://rss.donga.com/it.xml")

@app.route("/news/entertainment", methods=["POST"])
def news_entertainment():
    return list_card_response("연예", "https://rss.donga.com/entertainment.xml")

@app.route("/news/sports", methods=["POST"])
def news_sports():
    return list_card_response("스포츠", "https://rss.donga.com/sports.xml")

# ✅ 헬스 체크용
@app.route("/", methods=["GET"])
def health():
    return "RSS 기반 뉴스봇 정상 작동 중입니다."

# ✅ 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
