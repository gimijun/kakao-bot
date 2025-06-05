from flask import Flask, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# 이미지 추출 (RSS에서 media_content 우선, 없으면 기본 이미지)
def extract_image_from_entry(entry):
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
    return "https://t1.daumcdn.net/media/img-section/news_card_default.png"

# RSS 뉴스 가져오기
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

# 검색 뉴스 가져오기 (동아일보 검색 결과 크롤링)
def fetch_donga_search_news(keyword, max_count=5):
    url = f"https://www.donga.com/news/search?query={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)

    if res.status_code != 200:
        print(f"❌ 검색 요청 실패: {res.status_code}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    articles = soup.select("div.searchCont > div.searchList > ul > li")
    news_items = []

    for item in articles[:max_count]:
        title_tag = item.select_one("a.tit")
        image_tag = item.select_one("img")

        title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
        link = title_tag["href"] if title_tag else "#"
        image = image_tag["src"] if image_tag else "https://t1.daumcdn.net/media/img-section/news_card_default.png"

        news_items.append({
            "title": title,
            "image": image,
            "link": link
        })
    return news_items

# listCard JSON 응답 생성 (카테고리용)
def list_card_response(title, rss_url, web_url):
    articles = fetch_rss_news(rss_url)
    if not articles:
        items = [{
            "title": f"{title} 관련 뉴스를 불러오지 못했습니다.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": {"web": web_url}
        }]
    else:
        items = [{
            "title": a["title"],
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
                        "label": "전체 보기",
                        "action": "webLink",
                        "webLinkUrl": web_url
                    }]
                }
            }]
        }
    })

# listCard JSON 응답 생성 (검색어용)
def search_news_response(keyword):
    articles = fetch_donga_search_news(keyword)
    if not articles:
        items = [{
            "title": f"'{keyword}' 관련 뉴스를 불러오지 못했습니다.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": {"web": f"https://www.donga.com/news/search?query={keyword}"}
        }]
    else:
        items = [{
            "title": a["title"],
            "imageUrl": a["image"],
            "link": {"web": a["link"]}
        } for a in articles]

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [{
                "listCard": {
                    "header": {"title": f"'{keyword}' 검색 결과"},
                    "items": items,
                    "buttons": [{
                        "label": "동아일보에서 더보기",
                        "action": "webLink",
                        "webLinkUrl": f"https://www.donga.com/news/search?query={keyword}"
                    }]
                }
            }]
        }
    })

# 카테고리별 라우팅
@app.route("/news/politics", methods=["POST"])
def news_politics():
    return list_card_response("정치", "https://rss.donga.com/politics.xml", "https://www.donga.com/news/Politics")

@app.route("/news/economy", methods=["POST"])
def news_economy():
    return list_card_response("경제", "https://rss.donga.com/economy.xml", "https://www.donga.com/news/Economy")

@app.route("/news/society", methods=["POST"])
def news_society():
    return list_card_response("사회", "https://rss.donga.com/national.xml", "https://www.donga.com/news/National")

@app.route("/news/world", methods=["POST"])
def news_world():
    return list_card_response("국제", "https://rss.donga.com/international.xml", "https://www.donga.com/news/Inter")

@app.route("/news/science", methods=["POST"])
def news_science():
    return list_card_response("IT/과학", "https://rss.donga.com/science.xml", "https://www.donga.com/news/It")

@app.route("/news/culture", methods=["POST"])
def news_culture():
    return list_card_response("문화연예", "https://rss.donga.com/culture.xml", "https://www.donga.com/news/Culture")

@app.route("/news/sports", methods=["POST"])
def news_sports():
    return list_card_response("스포츠", "https://rss.donga.com/sports.xml", "https://www.donga.com/news/Sports")

@app.route("/news/entertainment", methods=["POST"])
def news_entertainment():
    return list_card_response("연예", "https://rss.donga.com/entertainment.xml", "https://www.donga.com/news/Entertainment")

# 검색 라우팅
@app.route("/news/search", methods=["POST"])
def news_search():
    body = request.get_json()
    print("[DEBUG] 받은 body:", body)  # 디버깅용 로그
    if not body:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {"text": "검색 요청 본문이 없습니다."}
                }]
            }
        })

    keyword = body.get("검색어", "").strip()
    print("[DEBUG] keyword:", keyword)

    if not keyword:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {"text": "검색어를 입력해 주세요."}
                }]
            }
        })
    return search_news_response(keyword)

# 헬스 체크
@app.route("/", methods=["GET"])
def health():
    return "카카오 뉴스봇(RSS + 검색) 정상 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
