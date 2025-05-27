from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/kakao", methods=["POST"])
def kakao_webhook():
    try:
        # 카카오 오픈빌더 요청 JSON 받기
        body = request.get_json()
        user_input = body.get("userRequest", {}).get("utterance", "(입력 없음)")

        # 입력 로그 확인용 출력
        print(f"[사용자 입력] {user_input}")

        # 더미 응답 구성 (실제 처리 로직은 나중에 추가 예정)
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"✅ 입력 잘 받았습니다!\n\n입력 내용: {user_input}"
                        }
                    }
                ]
            }
        })
    except Exception as e:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"⚠️ 오류 발생: {str(e)}"
                        }
                    }
                ]
            }
        })

@app.route("/", methods=["GET"])
def home():
    return "카카오 챗봇 Flask 서버 작동 중!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
