
from flask import Flask, jsonify, request
from storage import save_quiz
import uuid
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "..", "frontend"), static_url_path="")


@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.route("/api/test")
def test():
    return jsonify({
        "message": "QuizRoom сервері жұмыс істеп тұр!"
    })


@app.route("/api/quizzes", methods=["POST"])
def create_quiz():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Деректер жіберілмеді"}), 400

    title = data.get("title", "").strip()
    count = data.get("count", 0)

    if not title:
        return jsonify({"error": "Квиз атауын енгіз!"}), 400

    try:
        count = int(count)
    except (ValueError, TypeError):
        return jsonify({"error": "Сұрақ саны дұрыс емес"}), 400

    if count < 1 or count > 20:
        return jsonify({"error": "Сұрақ саны 1-20 аралығында болуы керек"}), 400

    quiz = {
        "id": str(uuid.uuid4()),
        "title": title,
        "count": count
    }

    save_quiz(quiz)

    return jsonify({
        "message": "Квиз сәтті сақталды!",
        "quiz": quiz
    }), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
