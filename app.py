from flask import Flask, jsonify, request
import feedparser
import aiohttp
import asyncio

app = Flask(__name__)

# 비동기 RSS 파싱 함수
async def fetch_rss_async(category_url, max_count=5):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(category_url, timeout=3) as resp:
                content = await resp.text()
        except Exception:
            return []  # 타임아웃 등 예외 시 빈 리스트

    feed = feedparser.parse(content)
    news_items = []
    for entry in feed.entries[:max_count]:
        # 이미지 추출 (media:content 우선)
        image_url = "https://via.placeholder.com/200"
        if hasattr(entry, "media_content"):
            try:
                image_url = entry.media_content[0]["url"]
            except Exception:
                pass
        news_items.append({
            "title": entry.title,
            "description": getattr(entry, "summary", "")[:50],
            "link": entry.link,
            "image": image_url
        })
    return news_items

# 비동기 라우트 처리
async def list_card_response(title, category_url):
    articles = await fetch_rss_async(category_url)
    if not articles:
        items = [{
            "title": f"{title} 뉴스를 불러오지 못했습니다.",
            "description": "잠시 후 다시 시도해 주세요.",
            "imageUrl": "https://via.placeholder.com/200",
            "link": {"web": "https://www.donga.com/"}
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

# -----------------------
# 각 뉴스 카테고리 라우트
# -----------------------

@app.route("/news/politics", methods=["POST"])
async def news_politics():
    return await list_card_response("정치", "https://rss.donga.com/politics.xml")

@app.route("/news/economy", methods=["POST"])
async def news_economy():
    return await list_card_response("경제", "https://rss.donga.com/economy.xml")

@app.route("/news/society", methods=["POST"])
async def news_society():
    return await list_card_response("사회", "https://rss.donga.com/society.xml")

@app.route("/news/culture", methods=["POST"])
async def news_culture():
    return await list_card_response("문화", "https://rss.donga.com/culture.xml")

@app.route("/news/world", methods=["POST"])
async def news_world():
    return await list_card_response("국제", "https://rss.donga.com/international.xml")

@app.route("/news/it", methods=["POST"])
async def news_it():
    return await list_card_response("IT", "https://rss.donga.com/it.xml")

@app.route("/news/entertainment", methods=["POST"])
async def news_entertainment():
    return await list_card_response("연예", "https://rss.donga.com/entertainment.xml")

@app.route("/news/sports", methods=["POST"])
async def news_sports():
    return await list_card_response("스포츠", "https://rss.donga.com/sports.xml")

# 헬스체크
@app.route("/", methods=["GET"])
def health():
    return "RSS 비동기 뉴스봇 작동 중입니다."

if __name__ == "__main__":
    import os
    import nest_asyncio
    nest_asyncio.apply()  # Jupyter나 일부 환경에서 필요
    import asyncio
    asyncio.run(app.run(host="0.0.0.0", port=5000))
