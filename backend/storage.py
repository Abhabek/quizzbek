import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "quizzes.json"


def save_quiz(quiz):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                quizzes = json.load(file)
        except json.JSONDecodeError:
            quizzes = []
    else:
        quizzes = []

    quizzes.append(quiz)

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(quizzes, file, ensure_ascii=False, indent=4)

    return quiz