from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import random
import requests
import json
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware



# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

SERVER_URL = "https://baby-rack-rocky-ratio.trycloudflare.com:443/api/v1/generate"
character_name = "undefined"
character_profile_changes = ""
lora = {"Chloe": "chloe_f1"}
character_name = "undefined"
persona = ""
mood = ""
outfit = ""
char_location = ""
inventory = []
history = "Conversation history:\n"


TEST_MODE = True



def test_requests(payload):
    # Log cleaned history for debugging
    cleaned_history = payload.get("prompt", "")

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "cleaned_history": cleaned_history
    }

    with open("Jimmy_test_clean_history.json", "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=4)

    # Test replies
    test_replies = [
    f"{character_name} nods thoughtfully.",
    f"{character_name} adjusts his straw hat.",
    f"{character_name} looks around the farmyard.",
    f"{character_name} smiles warmly.",
    f"{character_name} takes a slow breath and continues.",
    f"{character_name} steps closer and speaks softly."
    ]
    return {
        "results": [
            {"text": random.choice(test_replies)}
        ]
    }

# Persona and data
def load_character_data():
    global persona, mood, outfit, char_location, inventory, history, character_name
    

    filename = f"{character_name}.json"
    print(f"[LOAD] persona = {persona}")
    print(f"[LOAD] mood = {mood}")
    print(f"[LOAD] outfit = {outfit}")
    print(f"[LOAD] location = {char_location}")
    print(f"[LOAD] inventory = {inventory}")
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                print("[LOAD] RAW JSON:", data)
                persona = data.get("persona", "")
                mood = data.get("mood", "")
                outfit = data.get("outfit", "")
                char_location = data.get("location", "")
                inventory = data.get("inventory", [])

                print(f"Loaded data for {character_name}")
        except Exception as e:
            print(f"Error loading character data: {e}")
    else:
        print(f"No data file found for {character_name}, using fallback.")
        persona = f"You are {character_name}."
        mood = ""
        outfit = ""
        char_location = ""
        inventory = []

    # Reset history header using new start.
    history = "\nConversation history:\n"

def save_character_data(new_data):
    global character_profile_changes, persona, mood, outfit, char_location, inventory, character_name

    data = {
        "persona": persona,
        "mood": mood,
        "outfit": outfit,
        "location": char_location,
        "inventory": inventory
    }
    
    with open(f"{character_name}.json", "w") as f:
        json.dump(data, f, indent=4)
       
    changes = []

    if "mood" in new_data:
        changes.append(f"Mood changed to: {new_data['mood']}")

    if "location" in new_data:
        changes.append(f"Location updated to: {new_data['location']}")

    if "weather" in new_data:
        changes.append(f"Weather now: {new_data['weather']}")

    if "task" in new_data:
        changes.append(f"Current task: {new_data['task']}")

    # Add more fields as needed...

    if changes:
        character_profile_changes = "\n".join(changes)
    else:
        character_profile_changes = ""

# ---------------------------------------------------------
# Save / Load History
# ---------------------------------------------------------

def history_filename():
    global character_name
    return f"{character_name}_history.json"

def save_history():
    try:
        with open(history_filename(), "w", encoding="utf-8") as f:
            json.dump({"history": history}, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

def load_history():
    global history, character_name
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




# Conversation and persona memory
# history = persona + "Conversation history:\n"
load_character_data()
load_history()

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------
def clean_history_for_prompt(history, character_name):
    lines = history.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 1. Remove image markers entirely
        if "[IMAGE:" in line:
            continue

        # 2. Always keep character messages (they matter for persona)
        if line.startswith(f"{character_name}:"):
            cleaned.append(line)
            continue

        # 3. User messages: keep only if >= 18 characters
        if line.startswith("User:"):
            msg = line.replace("User:", "").strip()
            if len(msg) >= 18:
                cleaned.append(line)
            # short user messages are skipped
            continue

        # 4. Fallback: keep everything else
        cleaned.append(line)

    return "\n".join(cleaned)



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
    global history, character_name, persona

    parts = user_input.lower().strip().split()

    # IMAGE COMMAND
    if len(parts) == 2 and parts[0] == "image":
        imagename = parts[1]
        filename = f"{imagename}.png"

        # Save image marker in REAL history (not persona)
        history += f"{character_name}: [IMAGE:{filename}]\n"
        save_history()

        return {
            "type": "image",
            "filename": filename,
            "caption": f"{character_name}'s {imagename} today."
        }

    # Append new user message to REAL history
    history += f"User: {user_input}\n{character_name}: "

    # Build cleaned history (strip short messages, remove image markers)
    cleaned_history = clean_history_for_prompt(history, character_name)

    # ⭐ PREPEND PERSONA HERE — NOT IN SAVED HISTORY
    # Build prompt dynamically
    if character_profile_changes.strip():
        prompt = (
        persona
        + "\n\nRecent Updates:\n"
        + character_profile_changes
        + "\n\nConversation history:\n"
        + cleaned_history
        )
    else:
        prompt = persona + "\n\nConversation history:\n" + cleaned_history


    payload = {
        "prompt": prompt,
        "max_length": 200,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop_sequence": ["User:", f"{character_name}:"]
    }

    # Model call
    if TEST_MODE:
        data = test_requests(payload)
    else:
        response = requests.post(SERVER_URL, json=payload)
        data = response.json()

    reply = data["results"][0]["text"].strip()

    # Append reply to REAL history
    history += reply + "\n"
    save_history()

    return reply



def illustrate_scene():
    global character_name, character_state
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    global character_name, history, mood, outfit, char_location, inventory
    
    new_name = req.get("name")
    if not new_name:
        return {"error": "No character name provided"}

    character_name = new_name

    load_character_data()
    load_history()
    print("[SELECT] Sending persona =", persona)
    print("[SELECT] Sending location =", char_location)

    return {
        "status": "ok",
        "character": character_name,
        "persona": persona,
        "mood": mood,
        "outfit": outfit,
        "location": char_location,
        "inventory": inventory
    }



@app.post("/character/update")
def update_character(req: dict):
    global persona, mood, outfit, char_location, inventory, character_name

    print("[UPDATE] Received update:", req)

    # Track changes
    new_data = {}

    # Persona
    new_persona = req.get("persona", persona)
    if new_persona != persona:
        new_data["persona"] = new_persona

    # Mood
    new_mood = req.get("mood", mood)
    if new_mood != mood:
        new_data["mood"] = new_mood

    # Outfit
    new_outfit = req.get("outfit", outfit)
    if new_outfit != outfit:
        new_data["outfit"] = new_outfit

    # Location
    new_location = req.get("location", char_location)
    if new_location != char_location:
        new_data["location"] = new_location

    # Inventory
    new_inventory = req.get("inventory", inventory)
    if new_inventory != inventory:
        new_data["inventory"] = new_inventory

    # Only save if something changed
    if new_data:
        save_character_data(new_data)

    # Now update the actual globals
    persona = new_persona
    mood = new_mood
    outfit = new_outfit
    char_location = new_location
    inventory = new_inventory

    print("[UPDATE] Saved new values:")
    print(" persona =", persona)
    print(" mood =", mood)
    print(" outfit =", outfit)
    print(" location =", char_location)
    print(" inventory =", inventory)

    return {"status": "ok"}




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
