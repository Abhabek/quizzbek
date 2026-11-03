
import json
import uuid
from pathlib import Path
from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
DATA_DIR = BASE_DIR / "data"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
)

QUIZZES_FILE = DATA_DIR / "quizzes.json"
ROOMS_FILE = DATA_DIR / "rooms.json"


def read_json(path):
    DATA_DIR.mkdir(exist_ok=True)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def write_json(path, data):
    DATA_DIR.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def find_room(pin):
    rooms = read_json(ROOMS_FILE)
    return rooms, next((r for r in rooms if r["pin"] == pin), None)


@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.route("/join")
def join_page():
    return app.send_static_file("join.html")


@app.route("/play")
def play_page():
    return app.send_static_file("play.html")


@app.route("/host")
def host_page():
    return app.send_static_file("host.html")


@app.route("/api/quizzes")
def get_quizzes():
    return jsonify(read_json(QUIZZES_FILE))


@app.route("/api/quizzes", methods=["POST"])
def create_quiz():
    data = request.get_json(silent=True) or {}
    questions = data.get("questions", [])

    quiz = {
        "id": str(uuid.uuid4()),
        "title": data.get("title", "Жаңа квиз"),
        "questions": questions,
        "count": len(questions)
    }

    quizzes = read_json(QUIZZES_FILE)
    quizzes.append(quiz)
    write_json(QUIZZES_FILE, quizzes)

    return jsonify({"quiz": quiz}), 201


@app.route("/api/rooms", methods=["POST"])
def create_room():
    data = request.get_json(silent=True) or {}
    quiz_id = data.get("quiz_id")

    quizzes = read_json(QUIZZES_FILE)
    quiz = next(
        (q for q in quizzes if q.get("id") == quiz_id and "questions" in q),
        None
    )

    if not quiz:
        return jsonify({"error": "Квиз табылмады"}), 404

    rooms = read_json(ROOMS_FILE)

    pin = str(uuid.uuid4().int)[:6]
    while any(r["pin"] == pin for r in rooms):
        pin = str(uuid.uuid4().int)[:6]

    room = {
        "pin": pin,
        "quiz_id": quiz_id,
        "players": [],
        "status": "waiting",
        "current_question": 0,
        "answers": {}
    }

    rooms.append(room)
    write_json(ROOMS_FILE, rooms)

    return jsonify({"room": room}), 201


@app.route("/api/rooms/<pin>")
def room_info(pin):
    rooms, room = find_room(pin)

    if not room:
        return jsonify({"error": "Бөлме табылмады"}), 404

    return jsonify({
        "pin": room["pin"],
        "players": room["players"],
        "status": room["status"],
        "current_question": room["current_question"]
    })


@app.route("/api/rooms/<pin>/join", methods=["POST"])
def join_room(pin):
    rooms, room = find_room(pin)

    if not room:
        return jsonify({"error": "PIN қате немесе бөлме табылмады"}), 404

    if room["status"] != "waiting":
        return jsonify({"error": "Ойын басталып кетті"}), 400

    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()

    if not name:
        return jsonify({"error": "Атыңды енгіз"}), 400

    if any(p["name"].lower() == name.lower() for p in room["players"]):
        return jsonify({"error": "Бұл ат бұрын тіркелген"}), 400

    player = {
        "id": str(uuid.uuid4()),
        "name": name,
        "score": 0
    }

    room["players"].append(player)
    write_json(ROOMS_FILE, rooms)

    return jsonify({"player": player}), 201


@app.route("/api/rooms/<pin>/start", methods=["POST"])
def start_room(pin):
    rooms, room = find_room(pin)

    if not room:
        return jsonify({"error": "Бөлме табылмады"}), 404

    if not room["players"]:
        return jsonify({"error": "Әзірге ойыншы жоқ"}), 400

    room["status"] = "playing"
    room["current_question"] = 0
    write_json(ROOMS_FILE, rooms)

    return jsonify({"message": "Ойын басталды!"})


@app.route("/api/rooms/<pin>/question")
def get_question(pin):
    rooms, room = find_room(pin)

    if not room:
        return jsonify({"error": "Бөлме табылмады"}), 404

    if room["status"] != "playing":
        return jsonify({"status": room["status"]})

    quizzes = read_json(QUIZZES_FILE)
    quiz = next((q for q in quizzes if q.get("id") == room["quiz_id"]), None)

    if not quiz:
        return jsonify({"error": "Квиз табылмады"}), 404

    index = room["current_question"]
    questions = quiz["questions"]

    if index >= len(questions):
        return jsonify({"status": "finished"})

    q = questions[index]

    return jsonify({
        "status": "playing",
        "number": index + 1,
        "total": len(questions),
        "question": q["question"],
        "options": q["options"]
    })


@app.route("/api/rooms/<pin>/answer", methods=["POST"])
def submit_answer(pin):
    rooms, room = find_room(pin)

    if not room or room["status"] != "playing":
        return jsonify({"error": "Ойын жүріп жатқан жоқ"}), 400

    data = request.get_json(silent=True) or {}
    player_id = data.get("player_id")
    answer = data.get("answer")

    player = next(
        (p for p in room["players"] if p["id"] == player_id),
        None
    )

    if not player:
        return jsonify({"error": "Ойыншы табылмады"}), 404

    question_key = str(room["current_question"])

    if question_key in room["answers"] and player_id in room["answers"][question_key]:
        return jsonify({"error": "Жауап беріп қойдың"}), 400

    quizzes = read_json(QUIZZES_FILE)
    quiz = next((q for q in quizzes if q.get("id") == room["quiz_id"]), None)
    question = quiz["questions"][room["current_question"]]

    correct = answer == question["correct"]

    if question_key not in room["answers"]:
        room["answers"][question_key] = []

    room["answers"][question_key].append(player_id)

    if correct:
        player["score"] += 100

    write_json(ROOMS_FILE, rooms)

    return jsonify({
        "correct": correct,
        "score": player["score"]
    })


@app.route("/api/rooms/<pin>/next", methods=["POST"])
def next_question(pin):
    rooms, room = find_room(pin)

    if not room or room["status"] != "playing":
        return jsonify({"error": "Ойын жүріп жатқан жоқ"}), 400

    quizzes = read_json(QUIZZES_FILE)
    quiz = next((q for q in quizzes if q.get("id") == room["quiz_id"]), None)

    room["current_question"] += 1

    if room["current_question"] >= len(quiz["questions"]):
        room["status"] = "finished"

    write_json(ROOMS_FILE, rooms)

    return jsonify({"status": room["status"]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
