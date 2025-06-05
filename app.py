from flask import Flask, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup
import re
import datetime
import json
import os

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
        image_tag = item.select_one("header a div img")

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
                        "label": "더보기",
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
                        "label": "더보기",
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
                        "label": "더보기",
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

@app.route("/news/briefing", methods=["POST"])
def news_briefing():
    from flask import Flask, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup
import re
import datetime
import json
import os

app = Flask(__name__)

# ... (기존 RSS 뉴스 처리 함수들 유지)

@app.route("/news/briefing", methods=["POST"])
def news_briefing():
    def fetch_weather_listcard():
        service_key = os.getenv("WEATHER_API_KEY") or "N%2FRBXLEXYr%2FO1xxA7qcJZY5LK63c1D44dWsoUszF%2BDHGpY%2Bn2xAea7ruByvKh566Qf69vLarJBgGRXdVe4DlkA%3D%3D"
        base_date = datetime.datetime.now().strftime("%Y%m%d")
        base_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        if datetime.datetime.now().minute < 40:
            base_time -= datetime.timedelta(hours=1)
        base_time = base_time.strftime("%H%M")

        url = (
            f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?"
            f"serviceKey={service_key}&numOfRows=1000&pageNo=1&dataType=JSON"
            f"&base_date={base_date}&base_time={base_time}&nx=60&ny=127"
        )

        try:
            res = requests.get(url, timeout=10)
            items = res.json()['response']['body']['items']['item']
        except Exception:
            return {"simpleText": {"text": "날씨 정보를 불러오지 못했습니다."}}

        data = {item['category']: item['fcstValue'] for item in items}

        def evaluate_dust(value):
            try:
                v = int(value)
                if v <= 15: return "매우 좋음", "대기 상태 최상, 마스크 불필요"
                elif v <= 30: return "좋음", "야외활동에 지장 없습니다."
                elif v <= 80: return "보통", "가벼운 마스크 착용 권장"
                elif v <= 150: return "나쁨", "외출 시 주의하세요."
                else: return "매우 나쁨", "실내 활동 권장, 외출 자제"
            except:
                return "정보 없음", "측정 정보 없음"

        def evaluate_uv(value):
            try:
                v = float(value)
                if v < 2: return "매우 낮음", "자외선 위험도 매우 낮음"
                elif v < 5: return "낮음", "야외활동 지장 없음"
                elif v < 7: return "보통", "선크림 권장"
                elif v < 10: return "높음", "모자/선글라스 착용 필요"
                else: return "매우 높음", "장시간 야외활동 자제"
            except:
                return "정보 없음", "측정 정보 없음"

        def evaluate_sky(value):
            return {
                "1": "맑음",
                "3": "구름 많음",
                "4": "흐림"
            }.get(value, "정보 없음")

        def evaluate_rain(value):
            return {
                "0": "강수 없음",
                "1": "비",
                "2": "비/눈",
                "3": "눈",
                "4": "소나기"
            }.get(value, "정보 없음")

        def evaluate_humidity(value):
            try:
                v = int(value)
                if v < 30: return "매우 낮음"
                elif v < 50: return "낮음"
                elif v < 70: return "보통"
                elif v < 85: return "높음"
                else: return "매우 높음"
            except:
                return "정보 없음"

        temp = data.get('TMP', '?')
        sky = evaluate_sky(data.get('SKY', '?'))
        rain = evaluate_rain(data.get('PTY', '?'))
        weather_desc = f"{sky}, {rain}" if rain != "강수 없음" else sky

        pm10_status, pm10_msg = evaluate_dust(data.get('PM10', '?'))
        pm25_status, pm25_msg = evaluate_dust(data.get('PM25', '?'))
        uv_status, uv_msg = evaluate_uv(data.get('UV', '0'))
        humidity_val = data.get('REH', '?')
        humidity = evaluate_humidity(humidity_val)

        return {
            "listCard": {
                "header": {"title": "☀️ '서울특별시' 현재 날씨"},
                "items": [
                    {"title": f"기온 {temp}℃", "description": weather_desc},
                    {"title": f"미세먼지 {pm10_status}", "description": pm10_msg},
                    {"title": f"초미세먼지 {pm25_status}", "description": pm25_msg},
                    {"title": f"자외선 {uv_status}", "description": uv_msg},
                    {"title": f"습도 {humidity_val}%", "description": humidity}
                ],
                "buttons": [
                    {"label": "지역 변경하기", "action": "message", "messageText": "지역 변경하기"},
                    {"label": "전국날씨 보기", "action": "message", "messageText": "전국 날씨 보기"}
                ]
            }
        }

    def fetch_news_section(title, url):
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.select("section ul li article")
            news_items = []
            for item in articles[:3]:
                h_tag = item.select_one("div h4 a")
                img_tag = item.select_one("header a div img")
                link = h_tag['href'] if h_tag and h_tag.has_attr('href') else "#"
                title_text = h_tag.get_text(strip=True) if h_tag else "제목 없음"
                img_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else "https://via.placeholder.com/200"
                news_items.append({"title": title_text, "imageUrl": img_url, "link": {"web": link}})
            return {
                "listCard": {
                    "header": {"title": f"{title} TOP {len(news_items)}"},
                    "items": news_items,
                    "buttons": [{"label": "전체 보기", "action": "webLink", "webLinkUrl": url}]
                }
            }
        except:
            return {
                "simpleText": {"text": f"{title} 섹션을 불러오지 못했습니다."}
            }

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                fetch_weather_listcard(),
                fetch_news_section("실시간 뉴스", "https://www.donga.com/news/List"),
                fetch_news_section("연예", "https://www.donga.com/news/Entertainment/List"),
                fetch_news_section("스포츠", "https://www.donga.com/news/Sports/List"),
                fetch_news_section("문화", "https://www.donga.com/news/Culture/List")
            ]
        }
    })


@app.route("/", methods=["GET"])
def health():
    return "카카오 뉴스봇 정상 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
