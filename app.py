from flask import Flask, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta, timezone
import json
import sys # sys 모듈 임포트 (print 플러시용)
import urllib.parse # URL 디코딩을 위해 추가
import time # 시간 측정을 위해 time 모듈 임포트

app = Flask(__name__)

# JSON 파일로부터 지역 → 좌표 정보 로드
# 실제 배포 시에는 이 파일이 프로젝트 루트에 있거나, Render 설정에서 접근 가능한 경로에 있어야 합니다.
try:
    with open("region_coords.json", encoding="utf-8") as f:
        region_coords = json.load(f)
except FileNotFoundError:
    print("Warning: region_coords.json not found. Weather functionality may be limited.")
    sys.stdout.flush()
    region_coords = {} # 파일이 없으면 빈 딕셔너리로 초기화하여 NameError 방지

def get_coords(region_name):
    """지역 이름으로 좌표를 조회합니다."""
    # region_coords 딕셔너리에 '구'나 '시'가 포함된 전체 지역명으로 저장되어 있으므로,
    # 정확한 매칭을 위해 입력된 region_name을 기반으로 찾음
    # 예를 들어, '서울'이 입력되면 '서울특별시 종로구'와 같은 상세 주소를 매핑해야 함.
    # 여기서는 region_coords.json에 저장된 키들을 순회하며 일치하는 지역을 찾습니다."""
    
    # 먼저 정확히 일치하는 지역을 찾음
    if region_name in region_coords:
        return region_coords[region_name]

    # 입력된 지역명이 포함된 더 상세한 지역을 찾음 (예: "서울" -> "서울특별시 종로구" 등)
    # 'region_name'이 'full_region_name'의 일부인 경우 또는 시/도 이름만 입력된 경우를 처리
    for full_region_name, coords in region_coords.items():
        # 예를 들어, region_name이 "서울"일 때 "서울특별시 종로구"를 찾기 위함
        # 또는 region_name이 "종로구"일 때 "서울특별시 종로구"를 찾기 위함
        if region_name in full_region_name:
            print(f"Found partial match for '{region_name}': '{full_region_name}' -> {coords}")
            sys.stdout.flush()
            return coords
            
    print(f"Coords not found for region: {region_name}")
    sys.stdout.flush()
    return None, None


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
    start_time = time.time() # 시작 시간 기록
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
        end_time = time.time() # 종료 시간 기록
        print(f"fetch_rss_news from {rss_url} took {end_time - start_time:.2f} seconds.")
        sys.stdout.flush()
        return news_items
    except Exception as e:
        print(f"Error fetching RSS news from {rss_url}: {e}")
        sys.stdout.flush()
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
    start_time = time.time() # 시작 시간 기록
    url = f"https://www.donga.com/news/search?query={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.donga.com/"
    }
    # try:
    #     res = requests.get(url, headers=headers, timeout=5) # Timeout 5초로 변경
    #     res.raise_for_status() # HTTP 에러 발생 시 예외 발생
    #     soup = BeautifulSoup(res.text, "html.parser")
        
    #     news_items = []
        
    #     # 검색 페이지의 기사 목록 셀렉터 강화
    #     # 'ul.row_list li article'이 가장 흔한 패턴이지만, 다른 가능성도 고려
    #     potential_articles = soup.select("ul.row_list li article")
    #     if not potential_articles:
    #         potential_articles = soup.select("ul.row_list li") # article 태그가 없을 경우 li만 선택

    #     for item in potential_articles[:max_count]:
    #         title_tag = item.select_one("h4")
    #         link_tag = item.select_one("a")
    #         image_tag = item.select_one("img") # 이미지 태그를 좀 더 넓게 찾음
    #         if not image_tag: # 혹시 div 내부에 있을 경우
    #             image_tag = item.select_one("div.thumb img") 
    #         if not image_tag: # 또 다른 흔한 패턴
    #             image_tag = item.select_one("header a div img")


    #         title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
    #         link = link_tag["href"] if link_tag and link_tag.has_attr("href") else "#"
            
    #         # 링크가 상대 경로일 경우 절대 경로로 변환
    #         if link.startswith('//'): 
    #             link = "https:" + link
    #         elif link.startswith('/'):
    #              link = "https://www.donga.com" + link

    #         image = ""
    #         if image_tag:
    #             image = image_tag.get("src") or image_tag.get("data-src") or ""
    #             image = clean_image_url(image)
    #         else:
    #             image = "https://via.placeholder.com/200" # 이미지를 찾지 못하면 플레이스홀더 사용

    #         # 유효한 제목과 링크가 있는 경우에만 추가
    #         if title != "제목 없음" and link != "#": 
    #             news_items.append({
    #                 "title": title,
    #                 "image": image,
    #                 "link": link
    #             })
        
    #     if not news_items and len(potential_articles) > 0:
    #         print(f"Warning: Could not extract valid news items from search page for '{keyword}'. Potentially broken selectors for title/link within found articles/list items. Found {len(potential_articles)} potential items.")
    #         sys.stdout.flush()

    #     end_time = time.time() # 종료 시간 기록
    #     print(f"fetch_donga_search_news for '{keyword}' took {end_time - start_time:.2f} seconds.")
    #     sys.stdout.flush()
    #     return news_items
    # except requests.exceptions.RequestException as e:
    #     print(f"Error fetching Donga search news for '{keyword}': {e}")
    #     sys.stdout.flush()
    #     return []
    # except Exception as e:
    #     print(f"Error parsing Donga search news for '{keyword}': {e}")
    #     sys.stdout.flush()
    #     return []

    """RSS 피드 기반 뉴스 ListCard 응답을 생성합니다."""
    articles = fetch_rss_news('https://rss.donga.com/total.xml')
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

    for item in items[:10]:
        from google import genai

        import base64

        code = 'QUl6YVN5QXdCX0UzZVdPbk1tbzBNWmNHYUlGaXBiM0plcVozMEM4'
        code_bytes = code.encode('ascii')
        
        decoded = base64.b64decode(code_bytes)
        str = decoded.decode('UTF-8')
        
        client = genai.Client(api_key=str)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20", contents=f"{item['title']}과 {keyword} 사이의 연관성을 퍼센테이지로 나타내세요. 퍼센테이지 외에는 아무것도 출력하지 마세요.\n예시: 0%, 10%, 20%, 30%, 40%, 50%, 60%, 70%, 80%, 90%, 100%"
        )
        print(response.text)

        if response.text.rstrip('%') <= 50:
            items.remove(item)
        

    return items[:5]

    # end_time = time.time() # 종료 시간 기록
    # print(f"fetch_donga_search_news for '{keyword}' took {end_time - start_time:.2f} seconds.")
    # sys.stdout.flush()
    # return news_items

def fetch_donga_trending_news(url, max_count=5):
    """동아일보에서 트렌딩 뉴스를 가져옵니다."""
    start_time = time.time() # 시작 시간 기록
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5) # Timeout 5초로 변경
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        news_items = []
        
        # 웹사이트 구조 변경에 대응하기 위해 여러 셀렉터를 시도
        # "많이 본 뉴스"나 "요즘 뜨는 이슈" 페이지는 article 태그가 없는 경우가 많음
        potential_articles = []
        
        # 가장 흔한 뉴스 리스트 패턴들을 순차적으로 시도
        selectors_to_try = [
            "ul.row_list li article", # 기존 검색 페이지에서 사용하던 패턴
            "div.list ul li article",  # 기존 트렌딩 페이지에서 사용하던 패턴
            "ul.article_list_type01 li",
            "div.list_type01 ul li",
            "ul.type_list li",
            "div.news_list li",
            "section.ranking_type01 li", # 랭킹 섹션 패턴
            "ul li" # 최후의 수단으로 가장 넓은 범위
        ]
        
        for selector in selectors_to_try:
            found_items = soup.select(selector)
            if found_items:
                potential_articles = found_items
                print(f"Found articles with selector: {selector}")
                sys.stdout.flush()
                break # 찾았으면 더 이상 시도하지 않음
        
        if not potential_articles:
            print(f"Warning: No potential articles found using any selector for URL: {url}")
            sys.stdout.flush()


        for item in potential_articles[:max_count]:
            title_tag = item.select_one("h4 a") # h4 태그 안에 a 태그가 있을 가능성
            if not title_tag:
                title_tag = item.select_one("a.link_news") # 뉴스 링크 클래스
            if not title_tag:
                title_tag = item.select_one("a") # 가장 일반적인 a 태그

            link_tag = item.select_one("a") # 링크는 보통 a 태그 자체

            image_tag = item.select_one("img") 
            if not image_tag: # 특정 클래스가 있는 이미지 태그를 시도
                image_tag = item.select_one("img.news_thumb") 
            if not image_tag:
                image_tag = item.select_one("div.thumb img") # 썸네일 이미지가 div.thumb 안에 있을 경우
            if not image_tag:
                image_tag = item.select_one("header a img") # 기존 패턴

            title = ""
            if title_tag and not isinstance(title_tag, str): # title_tag가 Tag 객체인지 확인
                title = title_tag.get_text(strip=True)
            else:
                title = "제목 없음"

            link = ""
            if link_tag and hasattr(link_tag, 'get') and link_tag.has_attr("href"): # link_tag가 Tag 객체인지 확인
                link = link_tag["href"]
            else:
                link = "#"
            
            # 링크가 상대 경로일 경우 절대 경로로 변환
            if link.startswith('//'): 
                link = "https:" + link
            elif link.startswith('/'):
                 link = "https://www.donga.com" + link

            image = ""
            if image_tag and hasattr(image_tag, 'get'): # image_tag가 Tag 객체인지 확인
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
            print(f"Warning: Could not extract valid news items from trending page {url}. Potentially broken selectors for title/link within found articles/list items. Found {len(potential_articles)} potential items, but no valid news_items were created.")
            sys.stdout.flush()

        end_time = time.time() # 종료 시간 기록
        print(f"fetch_donga_trending_news from {url} took {end_time - start_time:.2f} seconds.")
        sys.stdout.flush()
        return news_items
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Donga trending news from {url}: {e}")
        sys.stdout.flush()
        return []
    except Exception as e:
        print(f"Error parsing Donga trending news from {url}: {e}. Raw HTML snippet (first 500 chars): {res.text[:500] if res else 'No response'}")
        sys.stdout.flush()
        return []


def common_quick_replies(topic=None): 
    """모든 뉴스 응답에서 공통으로 사용될 Quick Replies를 생성합니다."""
    quick_replies_list = [
        {
            "label": "알림받기",
            "action": "block",
            "blockId": "6848b46a938bdf47fcf3b4dc", 
            "context": { # 컨텍스트 추가
                "name": "news_alarm_context", # 컨텍스트 이름
                "lifeSpan": 3, # 3턴 동안 유지
                "params": {
                    "topic": topic # 컨텍스트에 topic 저장
                }
            }
        },
        {"label": "검색", "action": "message", "messageText": "검색", "blockId": "6840fd4cc5b310190b70166a"},
        {"label": "정치", "action": "message", "messageText": "정치", "blockId": "683596834df7f67fcdd66b62"},
        {"label": "경제", "action": "message", "messageText": "경제", "blockId": "683596b798b6403c8dad6138"},
        {"label": "사회", "action": "message", "messageText": "사회", "blockId": "683596c0e7598b00aa7e6eec"},
        {"label": "문화", "action": "message", "messageText": "문화", "blockId": "683596e8d9c3e21ccc39943b"},
        {"label": "국제", "action": "message", "messageText": "국제", "blockId": "683597142c50e1482b1e05db"},
        {"label": "IT 과학", "action": "message", "messageText": "IT 과학", "blockId": "68359701d9c3e21ccc399440"},
        {"label": "스포츠", "action": "message", "messageText": "스포츠", "blockId": "68359725938bdf47fcf0d8a4"},
        {"label": "연예", "action": "message", "messageText": "연예", "blockId": "683597362c50e1482b1e05df"} 
    ]
    return quick_replies_list


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
            }],
            "quickReplies": common_quick_replies(topic=title) 
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
        },
        "quickReplies": common_quick_replies(topic=title) 
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
            }],
            "quickReplies": common_quick_replies(topic=keyword) 
        }
    })

# --- 날씨 관련 함수 및 라우트 ---

def get_fine_dust_level(pm_value, is_pm25=False):
    """미세먼지/초미세먼지 농도에 따른 5단계 등급과 메시지를 반환합니다."""
    try:
        pm = float(pm_value)
        if is_pm25: # 초미세먼지 (PM2.5) 기준
            if pm <= 8:
                return "매우좋음", "매우 청정하고 상쾌해요!"
            elif pm <= 15:
                return "좋음", "맑은 공기 마시며 활동하기 좋아요."
            elif pm <= 35:
                return "보통", "보통 수준의 공기 질입니다."
            elif pm <= 75:
                return "나쁨", "실외 활동 시 마스크 착용을 권장해요."
            else:
                return "매우나쁨", "모든 연령대 실외 활동 자제!"
        else: # 미세먼지 (PM10) 기준
            if pm <= 15:
                return "매우좋음", "매우 청정하고 상쾌해요!"
            elif pm <= 30:
                return "좋음", "야외 활동하기 좋아요."
            elif pm <= 80:
                return "보통", "보통 수준의 공기 질입니다."
            elif pm <= 150:
                return "나쁨", "마스크 착용을 권장해요."
            else:
                return "매우나쁨", "모든 연령대 야외 활동 자제!"
    except (ValueError, TypeError):
        return "정보 없음", "미세먼지 정보를 불러올 수 없습니다."


def get_humidity_level(reh_value):
    """습도에 따른 5단계 등급과 메시지를 반환합니다."""
    try:
        reh = float(reh_value)
        if reh <= 30:
            return "매우낮음", "건조한 날씨! 피부 보습에 신경 써주세요."
        elif reh <= 40:
            return "낮음", "피부가 건조해질 수 있어요."
        elif reh <= 60:
            return "보통", "쾌적한 습도입니다."
        elif reh <= 75:
            return "높음", "습한 날씨가 예상됩니다."
        else:
            return "매우높음", "불쾌지수가 높을 수 있어요. 제습에 신경 쓰세요!"
    except (ValueError, TypeError):
        return "정보 없음", "습도 정보를 불러올 수 없습니다."

def get_sky_condition(sky_code, pty_code):
    """하늘 상태(SKY)와 강수 형태(PTY) 코드를 한글 설명으로 변환합니다."""
    sky_dict = {
        "1": "맑음",
        "3": "구름많음",
        "4": "흐림"
    }
    pty_dict = {
        "0": "", # 강수 없음
        "1": "비",
        "2": "비/눈",
        "3": "눈",
        "4": "소나기",
        "5": "빗방울",
        "6": "빗방울/눈날림",
        "7": "눈날림"
    }
    
    sky_desc = sky_dict.get(str(sky_code), "알 수 없음")
    pty_desc = pty_dict.get(str(pty_code), "")

    if pty_desc:
        return pty_desc # 강수 형태가 있으면 강수 형태 우선
    return sky_desc # 강수 형태가 없으면 하늘 상태

def get_latest_base_time(current_time):
    """
    기상청 초단기실황 API의 base_time을 계산합니다.
    API는 10분 단위로 자료가 생산되며, 정시 기준 40분 후 발표됩니다.
    (예: 09시 20분 자료는 10시 00분에 발표)
    """
    # 40분 전 시간 계산 (현재 시각으로부터 40분을 뺀 시각이 실제 관측 시각이 됨)
    adjusted_time = current_time - timedelta(minutes=40)
    
    # 분을 10분 단위로 내림 (예: 05:52 -> 05:50)
    base_minute = (adjusted_time.minute // 10) * 10
    
    # 초와 마이크로초는 0으로 설정하여 정확한 base_time (HHMM)을 만듭니다.
    base_datetime = adjusted_time.replace(minute=base_minute, second=0, microsecond=0)
    
    return base_datetime.strftime("%Y%m%d"), base_datetime.strftime("%H%M")


def fetch_weather_data(nx, ny, region_full_name="서울"):
    """
    기상청 API에서 날씨 데이터를 가져오고, 에어코리아 API에서 미세먼지 데이터를 가져옵니다.
    """
    start_time = time.time() # 시작 시간 기록
    # 기상청 API 서비스 키 (디코딩된 키 사용)
    # 이 부분을 발급받으신 API 키로 교체해주세요!
    weather_service_key_encoded = "N%2FRBXLEXYr%2FO1xxA7qcJZY5LK63c1D44dWsoUszF%2BDHGpY%2Bn2xAea7ruByvKh566Qf69vLarJBgGRXdVe4DlkA%3D%3D"
    weather_service_key = urllib.parse.unquote(weather_service_key_encoded) # 명시적 디코딩
    
    # 에어코리아 API 서비스 키 (디코딩된 키 사용)
    # 이 부분을 발급받으신 API 키로 교체해주세요!
    airkorea_service_key_encoded = "N%2FRBXLEXYr%2FO1xxA7qcJZY5LK63c1D44dWsoUszF%2BDHGpY%2Bn2xAea7ruByvKh566Qf69vLarJBgGRXdVe4DlkA%3D%3D"
    airkorea_service_key = urllib.parse.unquote(airkorea_service_key_encoded) # 명시적 디코딩

    weather = {}

    print(f"--- Starting fetch_weather_data for region: {region_full_name} ---")
    sys.stdout.flush()

    # requests session을 사용하여 SSL 문제 회피 시도
    session = requests.Session()
    # 에어코리아 문서를 기반으로 SSL 인증서 검증 비활성화 유지
    session.verify = False 

    try:
        # 1. 기상청 초단기 실황 API 호출
        # Render 서버가 UTC로 설정되어 있을 가능성이 높으므로, KST로 변환
        KST = timezone(timedelta(hours=9))
        now_kst = datetime.now(KST)

        base_date, base_time = get_latest_base_time(now_kst.replace(tzinfo=None)) # get_latest_base_time에 naive datetime 전달

        weather_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
        weather_params = {
            "serviceKey": weather_service_key, 
            "pageNo": "1",
            "numOfRows": "100",
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny
        }

        print(f"Calling KMA API with base_date={base_date}, base_time={base_time}, nx={nx}, ny={ny}")
        sys.stdout.flush()
        kma_api_start_time = time.time()
        weather_res = session.get(weather_url, params=weather_params, timeout=5) # Timeout 5초로 변경
        kma_api_end_time = time.time()
        print(f"KMA API call took {kma_api_end_time - kma_api_start_time:.2f} seconds. Status Code: {weather_res.status_code}")
        sys.stdout.flush()
        weather_res.raise_for_status() # HTTP 에러 발생 시 예외 발생
        weather_data_json = weather_res.json()

        if weather_data_json.get('response', {}).get('header', {}).get('resultCode') == '00':
            weather_items = weather_data_json['response']['body']['items']['item']
            for item in weather_items:
                category = item['category']
                value = item['obsrValue']
                if category in ["T1H", "REH", "SKY", "PTY"]: 
                    weather[category] = value
            print(f"Successfully fetched KMA weather data: {weather}")
            sys.stdout.flush()
        else:
            error_msg = weather_data_json.get('response', {}).get('header', {}).get('resultMsg', '알 수 없는 기상청 오류')
            print(f"KMA API error: {error_msg}. Full Response: {json.dumps(weather_data_json, indent=2)}")
            sys.stdout.flush()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data from KMA API: {e}")
        sys.stdout.flush()
    except Exception as e:
        print(f"Error processing KMA weather data: {e}")
        sys.stdout.flush()

    try:
        # 2. 에어코리아 대기오염정보 조회 API 호출 (시도별 실시간 측정정보)
        # sidoName을 위한 매핑: region_full_name에서 광역 시도명 추출
        main_sido_part = region_full_name.split(' ')[0]
        sido_mapping = {
            "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
            "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
            "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
            "강원특별자치도": "강원", "충청북도": "충북", "충청남도": "충남",
            "전라북도": "전북", "전라남도": "전남", "경상북도": "경북",
            "경상남도": "경남", "제주특별자치도": "제주"
        }
        # 매핑된 시도명 사용, 없으면 원본에서 추출한 광역 시도명 그대로 사용 (혹시모를 예외처리)
        airkorea_sido_name = sido_mapping.get(main_sido_part, main_sido_part)
        
        # region_coords.json에 있는 "서울특별시 종로구" 같은 상세 이름이 들어올 경우
        # airkorea_sido_name에 "서울"만 들어가도록 다시 한번 확인
        # 이 부분은 sido_mapping으로 충분할 수 있지만, 혹시 모를 경우를 대비
        if "특별시" in airkorea_sido_name or "광역시" in airkorea_sido_name or "특별자치시" in airkorea_sido_name or "도" in airkorea_sido_name:
            if "서울" in airkorea_sido_name: airkorea_sido_name = "서울"
            elif "부산" in airkorea_sido_name: airkorea_sido_name = "부산"
            elif "대구" in airkorea_sido_name: airkorea_sido_name = "대구"
            elif "인천" in airkorea_sido_name: airkorea_sido_name = "인천"
            elif "광주" in airkorea_sido_name: airkorea_sido_name = "광주"
            elif "대전" in airkorea_sido_name: airkorea_sido_name = "대전"
            elif "울산" in airkorea_sido_name: airkorea_sido_name = "울산"
            elif "세종" in airkorea_sido_name: airkorea_sido_name = "세종"
            elif "경기" in airkorea_sido_name: airkorea_sido_name = "경기"
            elif "강원" in airkorea_sido_name: airkorea_sido_name = "강원"
            elif "충북" in airkorea_sido_name: airkorea_sido_name = "충북"
            elif "충남" in airkorea_sido_name: airkorea_sido_name = "충남"
            elif "전북" in airkorea_sido_name: airkorea_sido_name = "전북"
            elif "전남" in airkorea_sido_name: airkorea_sido_name = "전남"
            elif "경북" in airkorea_sido_name: airkorea_sido_name = "경북"
            elif "경남" in airkorea_sido_name: airkorea_sido_name = "경남"
            elif "제주" in airkorea_sido_name: airkorea_sido_name = "제주"

        # 에어코리아 API URL을 HTTP로 변경 (SSL 호환성 문제 해결 시도)
        airkorea_url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
        airkorea_params = {
            "serviceKey": airkorea_service_key, # 디코딩된 키 사용
            "returnType": "json",
            "numOfRows": "1", 
            "pageNo": "1",
            "sidoName": airkorea_sido_name, # 정확히 매핑된 시도명 사용
            "ver": "1.3" 
        }
        
        print(f"Calling Airkorea API with sidoName={airkorea_sido_name}")
        sys.stdout.flush()
        airkorea_api_start_time = time.time()
        airkorea_res = session.get(airkorea_url, params=airkorea_params, timeout=5) # Timeout 5초로 변경
        airkorea_api_end_time = time.time()
        print(f"Airkorea API call took {airkorea_api_end_time - airkorea_api_start_time:.2f} seconds. Status Code: {airkorea_res.status_code}")
        sys.stdout.flush()
        airkorea_res.raise_for_status() # HTTP 에러 발생 시 예외 발생
        airkorea_data_json = airkorea_res.json()

        if airkorea_data_json.get('response', {}).get('header', {}).get('resultCode') == '00':
            airkorea_items = airkorea_data_json['response']['body']['items']
            if airkorea_items:
                # 에어코리아 API는 시도 내 여러 측정소를 반환할 수 있으므로, 첫 번째 측정소 데이터를 사용합니다.
                # 더 정확하게 하려면, 해당 시도 내에서 가장 가까운 측정소를 찾아야 합니다.
                first_station_data = airkorea_items[0] 
                weather['PM10'] = first_station_data.get('pm10Value')
                weather['PM25'] = first_station_data.get('pm25Value')
                print(f"Successfully fetched Airkorea data: PM10={weather.get('PM10')}, PM25={weather.get('PM25')}")
                sys.stdout.flush()
            else:
                print(f"No air quality data found for sidoName: {airkorea_sido_name}. Check API response structure or data availability for this region.")
                sys.stdout.flush()
        else:
            error_msg = airkorea_data_json.get('response', {}).get('header', {}).get('resultMsg', '알 수 없는 에어코리아 오류')
            print(f"Airkorea API error: {error_msg}. Full Response: {json.dumps(airkorea_data_json, indent=2)}")
            sys.stdout.flush()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching airkorea data: {e}")
        sys.stdout.flush()
    except Exception as e:
        print(f"Error processing airkorea data: {e}")
        sys.stdout.flush()

    end_time = time.time() # 함수 종료 시간 기록
    print(f"--- Finished fetch_weather_data. Total time: {end_time - start_time:.2f} seconds. Final weather dict: {weather} ---")
    sys.stdout.flush()
    return weather


def create_weather_card(region_name, weather_data, web_url):
    """날씨 데이터를 기반으로 카카오톡 ListCard를 생성합니다."""
    print(f"--- Starting create_weather_card for region: {region_name} ---")
    sys.stdout.flush()
    print(f"Received weather_data in create_weather_card: {weather_data}")
    sys.stdout.flush()

    # 기온 데이터가 없거나, 날씨 정보가 제대로 파싱되지 않았다면 실패로 간주
    if not weather_data or not weather_data.get("T1H"): 
        print(f"Weather data incomplete or missing for {region_name}. Returning error message.")
        sys.stdout.flush()
        return {
            "simpleText": {"text": f"'{region_name}' 지역의 날씨 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요."}
        }

    TMP = weather_data.get("T1H", "-")
    REH = weather_data.get("REH", "-")
    PM10 = weather_data.get("PM10", "-")
    PM25 = weather_data.get("PM25", "-") 
    SKY = weather_data.get("SKY", "1") 
    PTY = weather_data.get("PTY", "0") 

    # 날씨 상태 문자열 생성
    weather_condition = get_sky_condition(SKY, PTY)
    
    # 미세먼지 등급 및 메시지
    pm10_level, pm10_msg = get_fine_dust_level(PM10, is_pm25=False)
    pm25_level, pm25_msg = get_fine_dust_level(PM25, is_pm25=True)
    
    # 습도 등급 및 메시지
    reh_level, reh_msg = get_humidity_level(REH)

    print(f"Generated weather card content for {region_name}")
    sys.stdout.flush()
    return {
        "listCard": {
            "header": {"title": f"☀️ '{region_name}' 현재 날씨"},
            "items": [
                # 기온 항목: 기온과 날씨 상태 함께 표시
                {"title": f"기온 {TMP}℃, {weather_condition}", "description": ""},
                # 미세먼지 항목: PM10과 PM25 등급 및 메시지 함께 표시
                {"title": f"미세먼지: {pm10_level} / 초미세먼지: {pm25_level}", "description": f"PM10: {pm10_msg}\nPM2.5: {pm25_msg}"},
                # 습도 항목: 등급과 퍼센트 함께 표시
                {"title": f"습도 {reh_level} ({REH}%)", "description": reh_msg},
            ],
            "buttons": [
                {"label": "다른 지역 보기", "action": "message", "messageText": "지역 변경하기"},
                {
                    "label": "기상청 전국 날씨",
                    "action": "webLink",
                    "webLinkUrl": "https://www.weather.go.kr/w/weather/forecast/short-term.do" # 고정된 URL 사용
                }
            ]
        }
    }


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
    # 사용자 요청에 따라 "IT 과학"으로 레이블 변경
    return list_card_response("IT 과학", "https://rss.donga.com/science.xml", "https://www.donga.com/news/It")

@app.route("/news/culture", methods=["POST"])
def news_culture():
    """문화 뉴스 요청을 처리합니다."""
    # 사용자 요청에 따라 "문화"로 레이블 변경 및 RSS/웹링크도 문화로 변경 필요
    # 동아일보 RSS에 '문화' 단독 피드는 보이지 않으므로, '문화연예' 피드를 사용하고 레이블만 '문화'로 표시
    return list_card_response("문화", "https://rss.donga.com/culture.xml", "https://www.donga.com/news/Culture")

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
    print(f"Received webhook body for /weather/change-region: {json.dumps(body, indent=2)}") # 웹훅 바디 로깅 추가
    sys.stdout.flush()

    # 'detailParams'에서 'region_name'을 먼저 시도하고, 없으면 'params'에서 시도
    region = body.get("action", {}).get("detailParams", {}).get("region_name", {}).get("origin", "").strip()
    if not region: # detailParams.origin이 비어있을 경우 params.region_name 확인
        region = body.get("action", {}).get("params", {}).get("region_name", "서울").strip()

    print(f"Extracted region for /weather/change-region: {region}") # 추출된 지역명 로깅 추가
    sys.stdout.flush()

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
    weather_data = fetch_weather_data(nx, ny, region_full_name=region) 
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
    print(f"Received webhook body for /news/weather: {json.dumps(body, indent=2)}") # 웹훅 바디 로깅 추가
    sys.stdout.flush()

    # 'detailParams'에서 'region_name'을 먼저 시도하고, 없으면 'params'에서 시도
    region = body.get("action", {}).get("detailParams", {}).get("region_name", {}).get("origin", "").strip()
    if not region: # detailParams.origin이 비어있을 경우 params.region_name 확인
        region = body.get("action", {}).get("params", {}).get("region_name", "서울").strip()

    print(f"Extracted region for /news/weather: {region}") # 추출된 지역명 로깅 추가
    sys.stdout.flush()
    
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
    weather_data = fetch_weather_data(nx, ny, region_full_name=region)
    # create_weather_card 함수가 이미지처럼 ListCard를 생성하고 버튼 포함
    weather_card = create_weather_card(region, weather_data, "https://www.weather.go.kr/w/weather/forecast/short-term.do")

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [weather_card]
        }
    })

# # 새로운 알림 초기화 메시지 처리 엔드포인트
# @app.route("/news/handle_alarm_init", methods=["POST"])
# def handle_alarm_init_message():
#     """
#     카카오톡 챗봇 빌더의 '알림받기' 블록에서 호출되는 웹훅입니다.
#     컨텍스트를 통해 전달받은 topic 파라미터를 사용하여 동적인 메시지를 생성합니다.
#     """
#     body = request.get_json()
#     print(f"Received webhook body for /news/handle_alarm_init: {json.dumps(body, indent=2)}")
#     sys.stdout.flush()

#     topic = ""
#     # 1. userRequest.contexts에서 "news_alarm_context"를 찾아 topic 추출 (최우선)
#     if body.get("userRequest", {}).get("contexts"):
#         for context in body["userRequest"]["contexts"]:
#             # context.get("name")으로 컨텍스트 이름을 안전하게 확인
#             if context.get("name") == "news_alarm_context" and "topic" in context.get("params", {}):
#                 topic = context["params"]["topic"].strip()
#                 print(f"Parsed topic from context ('news_alarm_context'): {topic}")
#                 sys.stdout.flush()
#                 break # 찾았으면 더 이상 검색하지 않음
    
#     # 2. action.params에서 시도 (블록 파라미터가 웹훅으로 매핑된 경우 - 컨텍스트 유입이 잘 안될 경우의 대비책)
#     if not topic:
#         topic = body.get("action", {}).get("params", {}).get("topic", "").strip()
#         if topic:
#             print(f"Parsed topic from action.params: {topic}")
#             sys.stdout.flush()

#     # 3. userRequest.utterance에서 "뉴스알림설정:TOPIC" 패턴을 파싱 (fallback - 혹시 모를 대비)
#     if not topic:
#         utterance = body.get("userRequest", {}).get("utterance", "").strip()
#         if utterance.startswith("뉴스알림설정:"):
#             topic = utterance.split(":", 1)[1].strip()
#             print(f"Parsed topic from utterance (fallback): {topic}")
#             sys.stdout.flush()
#         else:
#             print(f"Utterance does not match '뉴스알림설정:' pattern (fallback): {utterance}")
#             sys.stdout.flush()

#     # 4. userRequest.action.extra에서 시도 (과거 extra 전달 방식, fallback - 혹시 모를 대비)
#     if not topic:
#         topic = body.get("userRequest", {}).get("action", {}).get("extra", {}).get("topic", "").strip()
#         if topic:
#             print(f"Parsed topic from userRequest.action.extra (fallback): {topic}")
#             sys.stdout.flush()


#     if not topic:
#         print("Warning: 'topic' parameter not found in webhook request for /news/handle_alarm_init after all attempts.")
#         sys.stdout.flush()
#         response_text = "알림 주제를 알 수 없습니다. 다시 시도해 주세요."
#     else:
#         response_text = f"언제 `{topic}` 뉴스를 보내드릴까요?\n원하는 방법을 선택해 주세요."
#         print(f"Generated alarm init message for topic: {topic}")
#         sys.stdout.flush()

#     return jsonify({
#         "version": "2.0",
#         "template": {
#             "outputs": [{
#                 "simpleText": {"text": response_text}
#             }]
#         }
#     })

# 헬스 체크 라우트
@app.route("/", methods=["GET"])
def health():
    """서버 상태를 확인하는 헬스 체크 라우트입니다."""
    return "카카오 뉴스봇 정상 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
