from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/news/politics", methods=["POST"])
def test_news():
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "테스트 뉴스 응답입니다."
                    }
                }
            ]
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
