from flask import Flask, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def extract_image_from_entry(entry):
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
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

def clean_image_url(image):
    if image.startswith("//"):
        return "https:" + image
    elif image.startswith("/"):
        return "https://www.donga.com" + image
    return image

def fetch_donga_search_news(keyword, max_count=5):
    url = f"https://www.donga.com/news/search?query={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.donga.com/"
    }
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code != 200:
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    articles = soup.select("ul.row_list li article")
    news_items = []

    for item in articles[:max_count]:
        title_tag = item.select_one("h4")
        link_tag = item.select_one("a")
        image_tag = item.select_one("header a img")

        title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
        link = "https:" + link_tag["href"] if link_tag and link_tag.has_attr("href") else "#"

        image = ""
        if image_tag:
            image = image_tag.get("src") or image_tag.get("data-src") or ""
            image = clean_image_url(image)

        news_items.append({
            "title": title,
            "image": image,
            "link": link
        })

    return news_items

def fetch_donga_trending_news(url, max_count=5):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code != 200:
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    articles = soup.select("div.list ul li article")
    news_items = []

    for item in articles[:max_count]:
        title_tag = item.select_one("h4")
        link_tag = item.select_one("a")
        image_tag = item.select_one("header a img")

        title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
        link = "https:" + link_tag["href"] if link_tag and link_tag.has_attr("href") else "#"

        image = ""
        if image_tag:
            image = image_tag.get("src") or image_tag.get("data-src") or ""
            image = clean_image_url(image)

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

def trending_card_response(title, web_url):
    articles = fetch_donga_trending_news(web_url)
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
                    "header": {"title": f"{title} TOP {len(items)}"},
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

def search_news_response(keyword, max_count=5):
    articles = fetch_donga_search_news(keyword, max_count=max_count)
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

@app.route("/news/ask_keyword", methods=["POST"])
def search_by_user_input():
    body = request.get_json()
    keyword = body.get("action", {}).get("params", {}).get("keyword", "").strip()

    if not keyword:
        keyword = body.get("userRequest", {}).get("utterance", "").strip()

    if not keyword:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {"text": "검색어를 찾을 수 없습니다. 다시 입력해 주세요."}
                }]
            }
        })

    return search_news_response(keyword, max_count=5)

# 카테고리별 뉴스 라우터
@app.route("/news/politics", methods=["POST"])
def news_politics(): return list_card_response("정치", "https://rss.donga.com/politics.xml", "https://www.donga.com/news/Politics")

@app.route("/news/economy", methods=["POST"])
def news_economy(): return list_card_response("경제", "https://rss.donga.com/economy.xml", "https://www.donga.com/news/Economy")

@app.route("/news/society", methods=["POST"])
def news_society(): return list_card_response("사회", "https://rss.donga.com/national.xml", "https://www.donga.com/news/National")

@app.route("/news/world", methods=["POST"])
def news_world(): return list_card_response("국제", "https://rss.donga.com/international.xml", "https://www.donga.com/news/Inter")

@app.route("/news/science", methods=["POST"])
def news_science(): return list_card_response("IT/과학", "https://rss.donga.com/science.xml", "https://www.donga.com/news/It")

@app.route("/news/culture", methods=["POST"])
def news_culture(): return list_card_response("문화연예", "https://rss.donga.com/culture.xml", "https://www.donga.com/news/Culture")

@app.route("/news/sports", methods=["POST"])
def news_sports(): return list_card_response("스포츠", "https://rss.donga.com/sports.xml", "https://www.donga.com/news/Sports")

@app.route("/news/entertainment", methods=["POST"])
def news_entertainment(): return list_card_response("연예", "https://rss.donga.com/entertainment.xml", "https://www.donga.com/news/Entertainment")

@app.route("/news/trending", methods=["POST"])
def trending_daily(): return trending_card_response("요즘 뜨는 뉴스", "https://www.donga.com/news/TrendNews/daily")

@app.route("/news/popular", methods=["POST"])
def trending_monthly(): return trending_card_response("많이 본 뉴스", "https://www.donga.com/news/TrendNews/monthly")

@app.route("/", methods=["GET"])
def health():
    return "카카오 뉴스봇 정상 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
