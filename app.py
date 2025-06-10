from flask import Flask, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# JSON 파일로부터 지역 → 좌표 정보 로드 (Render 배포 환경에 맞게 경로 조정 필요)
# 실제 배포 시에는 이 파일이 프로젝트 루트에 있거나, Render 설정에서 접근 가능한 경로에 있어야 합니다.
try:
    with open("region_coords.json", encoding="utf-8") as f:
        region_coords = json.load(f)
except FileNotFoundError:
    print("Warning: region_coords.json not found. Weather functionality may be limited.")
    region_coords = {}

# SERVICE_KEY는 fetch_weather_data 함수 내부에 직접 하드코딩 (사용자 요청)

def extract_image_from_entry(entry):
    """RSS 엔트리에서 이미지 URL을 추출합니다."""
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
    return "https://t1.daumcdn.net/media/img-section/news_card_default.png"

def fetch_rss_news(rss_url, max_count=5):
    """지정된 RSS URL에서 뉴스 항목을 가져옵니다."""
    try:
        feed = feedparser.parse(rss_url)
        news_items = []
        for entry in feed.entries[:max_count]:
            # HTML 태그 제거 및 제목 정리
            title = re.sub(r'<[^>]+>', '', entry.title)
            image = extract_image_from_entry(entry)
            link = entry.link
            news_items.append({
                "title": title,
                "image": image,
                "link": link
            })
        return news_items
    except Exception as e:
        print(f"Error fetching RSS news from {rss_url}: {e}")
        return []

def clean_image_url(image):
    """상대 경로 이미지 URL을 절대 경로로 변환합니다."""
    if image.startswith("//"):
        return "https:" + image
    elif image.startswith("/"):
        # 동아일보 특정 도메인에 대한 처리
        return "https://www.donga.com" + image
    return image

def fetch_donga_search_news(keyword, max_count=5):
    """동아일보에서 키워드 검색 뉴스를 가져옵니다."""
    url = f"https://www.donga.com/news/search?query={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.donga.com/"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status() # HTTP 에러 발생 시 예외 발생
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select("ul.row_list li article")
        news_items = []

        for item in articles[:max_count]:
            title_tag = item.select_one("h4")
            link_tag = item.select_one("a")
            image_tag = item.select_one("header a div img") # 이미지 태그 경로 확인

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
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Donga search news for '{keyword}': {e}")
        return []
    except Exception as e:
        print(f"Error parsing Donga search news for '{keyword}': {e}")
        return []

def fetch_donga_trending_news(url, max_count=5):
    """동아일보에서 트렌딩 뉴스를 가져옵니다."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        news_items = []
        
        # 웹사이트 구조 변경에 대응하기 위해 여러 셀렉터를 시도
        # 우선 'article' 태그를 직접 찾습니다.
        potential_articles = soup.find_all("article")
        
        if not potential_articles:
            # article 태그가 없으면, 뉴스 리스트에 흔히 사용되는 ul/li 패턴을 시도합니다.
            # 웹사이트 구조가 변경되었을 가능성이 높으므로, 다양한 패턴을 시도해봅니다.
            potential_articles = soup.select("ul.article_list_type01 li") # 흔한 뉴스 리스트 클래스
        if not potential_articles:
            potential_articles = soup.select("div.list_type01 ul li") # 또 다른 흔한 패턴
        if not potential_articles:
            potential_articles = soup.select("ul.type_list li") # 일반적인 리스트 타입
        if not potential_articles:
            potential_articles = soup.select("div.news_list li") # news_list div 내의 li
        if not potential_articles:
            # 마지막으로 가장 넓은 범위의 ul li를 시도 (관련 없는 항목도 포함될 수 있음)
            potential_articles = soup.select("ul li")


        for item in potential_articles[:max_count]:
            title_tag = item.select_one("h4")
            link_tag = item.select_one("a")
            # 이미지 태그를 찾습니다. news_thumb, thumbnail_image 등 흔히 사용되는 클래스를 고려
            image_tag = item.select_one("img") 
            if not image_tag: # 특정 클래스가 있는 이미지 태그를 시도
                image_tag = item.select_one("img.news_thumb") 
            if not image_tag:
                image_tag = item.select_one("div.thumb img") # 썸네일 이미지가 div.thumb 안에 있을 경우


            title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
            link = link_tag["href"] if link_tag and link_tag.has_attr("href") else "#"
            
            # 링크가 상대 경로일 경우 절대 경로로 변환
            if link.startswith('//'): 
                link = "https:" + link
            elif link.startswith('/'):
                 link = "https://www.donga.com" + link

            image = ""
            if image_tag:
                image = image_tag.get("src") or image_tag.get("data-src") or ""
                image = clean_image_url(image)
            else:
                image = "https://via.placeholder.com/200" # 이미지를 찾지 못하면 플레이스홀더 사용

            # 유효한 제목과 링크가 있는 경우에만 추가
            if title != "제목 없음" and link != "#": 
                news_items.append({
                    "title": title,
                    "image": image,
                    "link": link
                })
        
        if not news_items and len(potential_articles) > 0:
            print(f"Warning: Could not extract valid news items from trending page {url}. Potentially broken selectors for title/link within found articles/list items.")

        return news_items
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Donga trending news from {url}: {e}")
        return []
    except Exception as e:
        print(f"Error parsing Donga trending news from {url}: {e}")
        return []


def list_card_response(title, rss_url, web_url):
    """RSS 피드 기반 뉴스 ListCard 응답을 생성합니다."""
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
    """트렌딩 뉴스 ListCard 응답을 생성합니다."""
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
    """키워드 검색 뉴스 ListCard 응답을 생성합니다."""
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

# --- 라우트 정의 ---

@app.route("/news/ask_keyword", methods=["POST"])
def search_by_user_input():
    """사용자 입력 키워드로 뉴스를 검색합니다."""
    body = request.get_json()
    # 'keyword' 파라미터 우선 확인
    keyword = body.get("action", {}).get("params", {}).get("keyword", "").strip()

    # 파라미터에 'keyword'가 없으면 사용자 발화를 직접 검색어로 사용
    if not keyword:
        keyword = body.get("userRequest", {}).get("utterance", "").strip()

    if not keyword:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {"text": "검색어를 찾을 수 없습니다."}
                }]
            }
        })
    return search_news_response(keyword, max_count=5)

# 카테고리별 뉴스 라우트
@app.route("/news/politics", methods=["POST"])
def news_politics():
    """정치 뉴스 요청을 처리합니다."""
    return list_card_response("정치", "https://rss.donga.com/politics.xml", "https://www.donga.com/news/Politics")

@app.route("/news/economy", methods=["POST"])
def news_economy():
    """경제 뉴스 요청을 처리합니다."""
    return list_card_response("경제", "https://rss.donga.com/economy.xml", "https://www.donga.com/news/Economy")

@app.route("/news/society", methods=["POST"])
def news_society():
    """사회 뉴스 요청을 처리합니다."""
    return list_card_response("사회", "https://rss.donga.com/national.xml", "https://www.donga.com/news/National")

@app.route("/news/world", methods=["POST"])
def news_world():
    """국제 뉴스 요청을 처리합니다."""
    return list_card_response("국제", "https://rss.donga.com/international.xml", "https://www.donga.com/news/Inter")

@app.route("/news/science", methods=["POST"])
def news_science():
    """IT/과학 뉴스 요청을 처리합니다."""
    return list_card_response("IT/과학", "https://rss.donga.com/science.xml", "https://www.donga.com/news/It")

@app.route("/news/culture", methods=["POST"])
def news_culture():
    """문화연예 뉴스 요청을 처리합니다."""
    return list_card_response("문화연예", "https://rss.donga.com/culture.xml", "https://www.donga.com/news/Culture")

@app.route("/news/sports", methods=["POST"])
def news_sports():
    """스포츠 뉴스 요청을 처리합니다."""
    return list_card_response("스포츠", "https://rss.donga.com/sports.xml", "https://www.donga.com/news/Sports")

@app.route("/news/entertainment", methods=["POST"])
def news_entertainment():
    """연예 뉴스 요청을 처리합니다."""
    return list_card_response("연예", "https://rss.donga.com/entertainment.xml", "https://www.donga.com/news/Entertainment")

# 트렌딩 뉴스 라우트
@app.route("/news/trending", methods=["POST"])
def trending_daily():
    """'요즘 뜨는 뉴스' 요청을 처리합니다."""
    return trending_card_response("요즘 뜨는 뉴스", "https://www.donga.com/news/TrendNews/daily")

@app.route("/news/popular", methods=["POST"])
def trending_monthly():
    """'많이 본 뉴스' 요청을 처리합니다."""
    return trending_card_response("많이 본 뉴스", "https://www.donga.com/news/TrendNews/monthly")

# 날씨 정보 라우트 (기존 /weather/change-region 유지)
@app.route("/weather/change-region", methods=["POST"])
def weather_by_region():
    """사용자가 선택한 지역의 날씨 정보를 제공합니다."""
    body = request.get_json()
    region = body.get("action", {}).get("params", {}).get("sys_location", "서울") # 기본값 서울
    nx, ny = get_coords(region)

    if not nx or not ny:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {"text": f"'{region}' 지역의 날씨 정보를 찾을 수 없습니다. 다시 입력해 주세요."}
                }]
            }
        })
    
    # 미세먼지 데이터를 위해 시도 이름을 fetch_weather_data에 전달
    weather_data = fetch_weather_data(nx, ny, sido_name=region) 
    weather_card = create_weather_card(region, weather_data, "https://www.weather.go.kr/w/weather/forecast/short-term.do")

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [weather_card]
        }
    })

# /news/weather 라우트 추가 (기존 /news/briefing 대체)
@app.route("/news/weather", methods=["POST"])
def news_weather_route():
    """날씨 정보만 제공합니다 (기본 지역 서울 또는 사용자 지정 지역)."""
    body = request.get_json()
    # 'sys_location' 파라미터가 있다면 해당 지역을 사용, 없으면 '서울'을 기본값으로 사용
    region = body.get("action", {}).get("params", {}).get("sys_location", "서울")
    
    nx, ny = get_coords(region)

    if not nx or not ny:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {"text": f"'{region}' 지역의 날씨 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요."}
                }]
            }
        })
    
    # 미세먼지 데이터를 위해 시도 이름을 fetch_weather_data에 전달
    weather_data = fetch_weather_data(nx, ny, sido_name=region)
    # create_weather_card 함수가 이미지처럼 ListCard를 생성하고 버튼 포함
    weather_card = create_weather_card(region, weather_data, "https://www.weather.go.kr/w/weather/forecast/short-term.do")

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [weather_card]
        }
    })

# 헬스 체크 라우트
@app.route("/", methods=["GET"])
def health():
    """서버 상태를 확인하는 헬스 체크 라우트입니다."""
    return "카카오 뉴스봇 정상 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
