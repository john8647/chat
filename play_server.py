from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import random
import requests
import json
import os


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

SERVER_URL = "https://baby-rack-rocky-ratio.trycloudflare.com:443/api/v1/generate"
##character_name = "Jimmy"
character_name = "Chloe"
lora = {"Chloe": "chloe_f1"}

TEST_MODE = False

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

# Persona
persona = f"""
You are {character_name}, You are a farmer with some sheep.
You like to talk to John about nothing much.
You only work when the sunshines.
"""

# ---------------------------------------------------------
# Save / Load History
# ---------------------------------------------------------

def history_filename():
    return f"{character_name}_history.json"

def save_history():
    try:
        with open(history_filename(), "w", encoding="utf-8") as f:
            json.dump({"history": history}, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

def load_history():
    global history
    filename = history_filename()

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                history = data.get("history", history)
                print(f"Loaded history from {filename}")
        except Exception as e:
            print(f"Error loading history: {e}")
    else:
        print(f"No saved history found for {character_name}, using default.")




# Conversation memory
history = persona + "Conversation history:\n"
load_history()


# Character state
character_state = {
    "outfit": "black jumper, black trousers and brown shoes",
    "location": "living room",
    "time": "late afternoon",
    "mood": "calm"
}



# ---------------------------------------------------------
# Utility functions
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
    save_history()
    return reply

def illustrate_scene():
    recent = get_clean_recent_context(history, persona, character_name)
    lora_raw = lora.get(character_name, "")
    lora_name = f"Include this LoRA name: {lora_raw}" if lora_raw else ""

    prompt = f"""
Write a prompt for a realistic photographic scene.
{lora_name}
Subject:
A person named {character_name}, wearing: {character_state['outfit']}

Environment:
The scene takes place in the location: {character_state['location']}

Time and Mood:
The time of day is {character_state['time']} and the mood is {character_state['mood']}.

Recent Actions:
\"\"\"{recent}\"\"\"
"""

    if TEST_MODE:
        return f"[TEST MODE — Prompt Sent]\n\n{prompt}"

    response = requests.post(SERVER_URL, json={"prompt": prompt})
    data = response.json()
    return data["results"][0]["text"].strip()

# ---------------------------------------------------------
# FastAPI server
# ---------------------------------------------------------

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    reply = send_message(req.message)
    return {"reply": reply}

@app.get("/history")
def get_history():
    return {"history": history}

@app.get("/image")
def get_image():
    return {"image_prompt": illustrate_scene()}

@app.get("/state")
def get_state():
    return character_state

@app.post("/reset")
def reset():
    global history
    history = persona + "Conversation history:\n"

    # Delete saved file
    try:
        os.remove(history_filename())
    except FileNotFoundError:
        pass

    save_history()
    return {"status": "reset", "character": character_name}

@app.post("/character/select")
def select_character(req: dict):
    global character_name, history

    new_name = req.get("name")
    if not new_name:
        return {"error": "No character name provided"}

    character_name = new_name

    # Reload persona and history
    history = persona + "Conversation history:\n"
    load_history()

    return {"status": "ok", "character": character_name}


# ---------------------------------------------------------
# Run server
# ---------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)


@app.get("/")
def root():
    return {"status": "Python game server running"}


@app.get("/favicon.ico")
def favicon():
    return {}


@app.get("/character")
def get_character():
    return {"name": character_name}
