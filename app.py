from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# OpenAI API 키
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/kakao", methods=["POST"])
def kakao_chatbot():
    try:
        # 카카오 오픈빌더에서 보낸 메시지 추출
        body = request.get_json()
        user_input = body.get("userRequest", {}).get("utterance", "")

        if not user_input:
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [{
                        "simpleText": {
                            "text": "❗입력된 내용이 없습니다."
                        }
                    }]
                }
            })

        # GPT 응답 생성
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_input}]
        )
        gpt_reply = response.choices[0].message["content"]

        # 카카오톡 응답 포맷
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {
                        "text": gpt_reply
                    }
                }]
            }
        })

    except Exception as e:
        # 예외 발생 시 fallback 응답
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {
                        "text": f"⚠️ 오류 발생: {str(e)}"
                    }
                }]
            }
        })

@app.route("/", methods=["GET"])
def health():
    return "✅ 카카오 GPT 챗봇 서버 작동 중!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
