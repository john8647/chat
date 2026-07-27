import sys
import random
import requests

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

SERVER_URL = "https://interact-italia-knitting-repository.trycloudflare.com:443/api/v1/generate"
character_name = "Jimmy"
lora = {"Jimmy": "Jimmy_0303"}

# Test replies
test_replies = [
    f"{character_name} nods thoughtfully.",
    f"{character_name} adjusts his straw hat.",
    f"{character_name} looks around the farmyard.",
    f"{character_name} smiles warmly.",
    f"{character_name} takes a slow breath and continues.",
    f"{character_name} steps closer and speaks softly."
]

def test_requests(payload):
    return {
        "results": [
            {"text": random.choice(test_replies)}
        ]
    }

TEST_MODE = True

# Persona
persona = f"""
You are {character_name}, an old farmer..
You only wear farm clothes.
You enjoy when John looks after you. Only talk about yourself.
"""

# Conversation memory
history = persona + "Conversation history:\n"

# Character state
character_state = {
    "outfit": "black jumper, black trousers and brown shoes",
    "location": "living room",
    "time": "late afternoon",
    "mood": "calm"
}

# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------

def get_clean_recent_context(history, persona, character_name,
                             min_length=20, max_lines=6):

    history_lines = history.strip().split("\n")
    recent_lines = history_lines[-max_lines:] if len(history_lines) >= max_lines else history_lines
    recent_text = "\n".join(recent_lines)

    persona_words = persona.strip().split()
    if len(persona_words) >= 2:
        persona_tail = " ".join(persona_words[-2:])
    else:
        persona_tail = persona_words[-1] if persona_words else ""

    if persona_tail and persona_tail in recent_text:
        recent_text = recent_text.split(persona_tail, 1)[1].strip()

    lines = recent_text.split("\n")

    cleaned = []
    TRIPLE_DQ = '"""'
    TRIPLE_SQ = "'''"

    for line in reversed(lines):
        if line.startswith("User:"):
            line = line.replace("User:", "").strip()
        elif line.startswith(f"{character_name}:"):
            line = line.replace(f"{character_name}:", "").strip()

        line = line.replace(TRIPLE_DQ, "").replace(TRIPLE_SQ, "").strip()

        if len(line) < min_length:
            continue

        cleaned.append(line)

        if len(cleaned) >= max_lines:
            break

    cleaned.reverse()
    return "\n".join(cleaned)

# ---------------------------------------------------------
# Core chat handler
# ---------------------------------------------------------

def send_message(user_input):
    global history

    history += f"User: {user_input}\n{character_name}: "

    payload = {
        "prompt": history,
        "max_length": 200,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop_sequence": ["User:", f"{character_name}:"]
    }

    if TEST_MODE:
        data = test_requests(payload)
    else:
        response = requests.post(SERVER_URL, json=payload)
        data = response.json()

    reply = data["results"][0]["text"].strip()

    history += reply + "\n"
    reply_with_char = f"{character_name}: {reply}"
    return reply_with_char

# ---------------------------------------------------------
# API entry point for Node.js
# ---------------------------------------------------------

if __name__ == "__main__":
    # Node passes the user message as argv[1]
    user_input = sys.argv[1] if len(sys.argv) > 1 else ""

    # Produce reply using your full chat engine
    reply = send_message(user_input)

    # Print ONLY the reply so Node can read it
    print(reply)
