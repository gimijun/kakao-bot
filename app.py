from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or "57d7009cb3534e669e1028d974b01ea8"

def fetch_news(keyword, count=5):
    url = f"https://newsapi.org/v2/everything?q={keyword}&pageSize={count}&sortBy=publishedAt&language=ko&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url, timeout=3)
        articles = res.json().get("articles", [])
    except Exception:
        return []

    news_items = []
    for article in articles:
        news_items.append({
            "title": article.get("title", "제목 없음"),
            "link": article.get("url", "#"),
            "image": article.get("urlToImage") or "https://via.placeholder.com/640"
        })
    return news_items

def news_route(keyword, more_keywords):
    if request.args.get("more") == "true":
        cards = []
        for kw in more_keywords:
            articles = fetch_news(kw, 1)
            if articles:
                article = articles[0]
                cards.append({
                    "title": kw,
                    "description": article["title"],
                    "thumbnail": {
                        "imageUrl": article["image"]
                    },
                    "buttons": [
                        {
                            "action": "webLink",
                            "label": "기사 보기",
                            "webLinkUrl": article["link"]
                        }
                    ]
                })
    else:
        articles = fetch_news(keyword)

        if not articles:
            articles = [{
                "title": f"{keyword} 관련 뉴스를 불러오지 못했습니다.",
                "link": "https://news.naver.com/",
                "image": "https://via.placeholder.com/640"
            }]

        cards = [{
            "title": article["title"],
            "description": "",
            "thumbnail": {
                "imageUrl": article["image"]
            },
            "buttons": [
                {
                    "action": "webLink",
                    "label": "기사 보기",
                    "webLinkUrl": article["link"]
                }
            ]
        } for article in articles]

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": cards
                    }
                }
            ]
        }
    })

# 카테고리별 라우팅
@app.route("/news/politics", methods=["POST"])
def news_politics():
    return news_route("정치", ["선거", "정당", "정책", "국회", "대통령실"])

@app.route("/news/economy", methods=["POST"])
def news_economy():
    return news_route("경제", ["금리", "환율", "부동산", "주식", "무역"])

@app.route("/news/society", methods=["POST"])
def news_society():
    return news_route("사회", ["교육", "범죄", "노동", "복지", "주거"])

@app.route("/news/culture", methods=["POST"])
def news_culture():
    return news_route("문화", ["공연", "전시", "문학", "예술", "축제"])

@app.route("/news/it", methods=["POST"])
def news_it():
    return news_route("IT", ["AI", "반도체", "메타버스", "모바일", "스타트업"])

@app.route("/news/world", methods=["POST"])
def news_world():
    return news_route("국제", ["미국", "중국", "러시아", "유럽", "일본"])

@app.route("/news/sports", methods=["POST"])
def news_sports():
    return news_route("스포츠", ["축구", "야구", "농구", "배구", "올림픽"])

@app.route("/news/entertainment", methods=["POST"])
def news_entertainment():
    return news_route("연예", ["아이돌", "배우", "드라마", "예능", "음악"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
