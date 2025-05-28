from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or "57d7009cb3534e669e1028d974b01ea8"  

def fetch_news(keyword, count=5):
    url = f"https://newsapi.org/v2/everything?q={keyword}&pageSize={count}&sortBy=publishedAt&language=ko&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url, timeout=5)
        print("✅ 상태 코드:", res.status_code)
        print("✅ 응답 본문:", res.text)
        articles = res.json().get("articles", [])
    except Exception as e:
        print("❌ 오류 발생:", e)
        return []

    news_items = []
    for article in articles:
        news_items.append({
            "title": article.get("title", "제목 없음"),
            "description": article.get("description", ""),
            "link": article.get("url", "#"),
            "image": article.get("urlToImage") or "https://via.placeholder.com/200"
        })
    return news_items

def list_card_response(category):
    articles = fetch_news(category)
    if not articles:
        items = [{
            "title": f"{category} 관련 뉴스를 불러오지 못했습니다.",
            "description": "잠시 후 다시 시도해 주세요.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": { "web": "https://news.naver.com" }
        }]
    else:
        items = [{
            "title": news["title"],
            "description": news["description"][:50],  # 너무 길면 자름
            "imageUrl": news["image"],
            "link": { "web": news["link"] }
        } for news in articles[:5]]  # 최대 5개

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "listCard": {
                        "header": { "title": f"{category} 뉴스 TOP 5" },
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

# 카테고리별 라우팅
@app.route("/news/politics", methods=["POST"])
def news_politics():
    return list_card_response("정치")

@app.route("/news/economy", methods=["POST"])
def news_economy():
    return list_card_response("경제")

@app.route("/news/society", methods=["POST"])
def news_society():
    return list_card_response("사회")

@app.route("/news/culture", methods=["POST"])
def news_culture():
    return list_card_response("문화")

@app.route("/news/it", methods=["POST"])
def news_it():
    return list_card_response("IT")

@app.route("/news/world", methods=["POST"])
def news_world():
    return list_card_response("국제")

@app.route("/news/sports", methods=["POST"])
def news_sports():
    return list_card_response("스포츠")

@app.route("/news/entertainment", methods=["POST"])
def news_entertainment():
    return list_card_response("연예")

@app.route("/", methods=["GET"])
def health():
    return "카카오 뉴스봇 서버 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
