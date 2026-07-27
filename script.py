import sys
import json
import os

# Toggle this to True when testing without Node
TEST_MODE = True

def load_input():
    if TEST_MODE:
        # Load JSON from file instead of stdin
        with open(r"C:\scripts\chat\test_input.json", "r") as f:
            return json.load(f)
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            return {}
        return json.loads(raw)

data = load_input()
action = data.get("action")



# Example quiz questions
QUESTIONS = {
    1: {"question": "What is 2 + 2?", "answer": "4"},
    2: {"question": "What is 3 + 5?", "answer": "8"},
    3: {"question": "What is 10 - 3?", "answer": "7"}
}

def next_challenge(data):
    level = data.get("level", 1)
    answer = data.get("answer")
    
    
    print (level)
    current_question = data.get("current_question", 1)
    score = data.get("score", 0)

    # Treat empty or missing answer as None
    if not answer:
        answer = None
        print("You didn't provide an answer yet")

    # Check answer if provided
    if answer is not None:
        correct_answer = QUESTIONS[current_question]["answer"]
        correct = (answer == correct_answer)
        if correct:
            score += 10
            current_question += 1
            level += 1
        else:
            correct = False

    # If we reached the end
    if current_question not in QUESTIONS:
        return {
            "correct": True,
            "new_level": level,
            "new_score": score,
            "finished": True,
            "message": "Quiz complete!"
        }

    # Return next question
    return {
        "correct": True,
        "new_level": level,
        "new_score": score,
        "finished": False,
        "next_question_number": current_question,
        "next_question": QUESTIONS[current_question]["question"]
    }

# Dispatcher
actions = {
    "next_challenge": next_challenge
}

if action in actions:
    result = actions[action](data)
else:
    result = {"error": "Unknown action"}

print(json.dumps(result))
