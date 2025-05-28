from flask import Flask, jsonify, request

app = Flask(__name__)

# 더미 뉴스 카드 생성 함수
def dummy_news_cards(category):
    return [{
        "title": f"[더미뉴스] {category} 테스트 #{i+1}",
        "description": f"{category} 테스트 입니다.",
        "thumbnail": {
            "imageUrl": "https://via.placeholder.com/640"
        },
        "buttons": [
            {
                "action": "webLink",
                "label": "기사 보기",
                "webLinkUrl": "https://news.naver.com"
            }
        ]
    } for i in range(5)]

# 공통 라우터
def respond_with_dummy_news(category):
    cards = dummy_news_cards(category)
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

# 카테고리별 엔드포인트
@app.route("/news/politics", methods=["POST"])
def politics():
    return respond_with_dummy_news("정치")

@app.route("/news/economy", methods=["POST"])
def economy():
    return respond_with_dummy_news("경제")

@app.route("/news/society", methods=["POST"])
def society():
    return respond_with_dummy_news("사회")

@app.route("/news/culture", methods=["POST"])
def culture():
    return respond_with_dummy_news("문화")

@app.route("/news/it", methods=["POST"])
def it():
    return respond_with_dummy_news("IT")

@app.route("/news/world", methods=["POST"])
def world():
    return respond_with_dummy_news("국제")

@app.route("/news/sports", methods=["POST"])
def sports():
    return respond_with_dummy_news("스포츠")

@app.route("/news/entertainment", methods=["POST"])
def entertainment():
    return respond_with_dummy_news("연예")

@app.route("/", methods=["GET"])
def health():
    return "뉴스봇 서버 작동 중입니다."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
