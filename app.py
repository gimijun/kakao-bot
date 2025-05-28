from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# 뉴스 검색 및 추출 함수
def fetch_news(keyword, count=5):
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    news_items = []
    for item in soup.select(".list_news .news_area")[:count]:
        title_tag = item.select_one(".news_tit")
        img_tag = item.select_one(".dsc_thumb img")
        title = title_tag['title'] if title_tag else "제목 없음"
        link = title_tag['href'] if title_tag else "#"
        image = img_tag['src'] if img_tag else "https://via.placeholder.com/640"
        news_items.append({
            "title": title,
            "link": link,
            "image": image
        })
    return news_items

# 공통 응답 포맷 함수
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

# 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
