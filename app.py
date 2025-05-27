from flask import Flask, request, jsonify
import openai
import os

openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)

@app.route("/kakao", methods=["POST"])
def kakao_chatbot():
    user_input = request.json["userRequest"]["utterance"]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{ "role": "user", "content": user_input }]
    )
    gpt_reply = response.choices[0].message["content"]

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                { "simpleText": { "text": gpt_reply } }
            ]
        }
    })

@app.route("/")
def health():
    return "카카오 GPT 챗봇 서버 작동 중!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)