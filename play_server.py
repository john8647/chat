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
TEST_MODE = True
SERVER_URL = "https://mercury-features-plan-skip.trycloudflare.com:443/api/v1/generate"
character_name = "undefined"
character_profile_changes = ""
    # LoRA lookup table
lora = {
        "Jimmy": "jimmy_f1",
        "Sarah": "sarah_f1",
        "Chloe": "chloe_f1"
        # add more characters here
    }
character_name = "undefined"
persona = ""
mood = ""
outfit = ""
char_location = ""
inventory = []
history = ""
description = ""
pose = ""
age = ""

def generate_image():
    global character_name, outfit, char_location

    # use Lookup LoRA name
    lora_name = lora.get(character_name, "default_lora")

    # Temporary test variables (later moved to profile panel)
    ##person = "farmer, young man"
    # Build the prompt
    image_prompt = (
        "Photorealistic:\n"
        f"{lora_name}, real photo of {description}, {age}yo,\n"
        f"wearing {outfit},\n"
        f"{pose},\n"
        f"scene location: {char_location}"
    )
    return image_prompt

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
    global persona, mood, outfit, char_location, inventory, history, character_name, description, pose, age
    

    filename = f"{character_name}.json"

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                persona = data.get("persona", "")
                mood = data.get("mood", "")
                outfit = data.get("outfit", "")
                char_location = data.get("location", "")
                inventory = data.get("inventory", [])
                description = data.get("description","")
                pose = data.get("pose","")
                age = data.get("age","")

        except Exception as e:
            print(f"Error loading character data: {e}")
    else:
        persona = f"You are {character_name}."
        mood = ""
        outfit = ""
        char_location = ""
        inventory = []
        description = ""
        pose = ""
        age = ""

def save_character_data(new_data):
    global character_profile_changes, persona, mood, outfit, char_location, inventory, character_name, description, pose, age
    # Build update block FIRST
    changes = []
    if "persona" in new_data:
        changes.append("Persona updated.")
    if "mood" in new_data:
        changes.append(f"Mood changed to: {new_data['mood']}")
    if "outfit" in new_data:
        changes.append(f"Outfit changed to: {new_data['outfit']}")
    if "location" in new_data:
        changes.append(f"Location updated is now: {new_data['location']}")
    if "inventory" in new_data:
        changes.append(f"Inventory updated now is: {new_data['inventory']}")
    if "pose" in new_data:
        changes.append(f"new pose is: {new_data['pose']}")

    character_profile_changes = "\n".join(changes) if changes else ""

    # ⭐ NOW SAVE UPDATED CHARACTER DATA TO DISK
    data = {
        "persona": persona,
        "mood": mood,
        "outfit": outfit,
        "location": char_location,
        "inventory": inventory,
        "description": description,
        "pose": pose,
        "age": age
    }

    filename = f"{character_name}.json"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("=== DEBUG: JSON WRITE FAILED ===")
        print("Error:", e)


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
                
        except Exception as e:
            print(f"Error loading history: {e}")
    else:
        history = "Conversation history:\n"

# Conversation and persona memory
# history = persona + "Conversation history:\n"
load_character_data()
load_history()

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------
def clean_history_for_prompt(history, character_name):
    shortest_message = 18
    last_short_lines_kept_in = 4

    lines = [line.strip() for line in history.split("\n") if line.strip()]
    cleaned = []

    # We need to know which lines are the last N lines
    total_lines = len(lines)
    cutoff_index = total_lines - last_short_lines_kept_in

    for i, line in enumerate(lines):
        # 1. Remove image markers entirely
        if "[IMAGE:" in line:
            continue

        # 2. Always keep the last N lines (even if short)
        if i >= cutoff_index:
            cleaned.append(line)
            continue

        # 3. For older lines: keep only long messages
        #    Applies to BOTH user and character
        if line.startswith("User:"):
            msg = line.replace("User:", "").strip()
            if len(msg) >= shortest_message:
                cleaned.append(line)
            continue

        if line.startswith(f"{character_name}:"):
            msg = line.replace(f"{character_name}:", "").strip()
            if len(msg) >= shortest_message:
                cleaned.append(line)
            continue

        # 4. Fallback: keep only long non‑tagged lines
        if len(line) >= shortest_message:
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

    # ⭐ Only IMAGE Generator COMMAND INTERCEPT
    if len(parts) == 1 and parts[0] == "show":
        image_prompt = generate_image()
        return f"generate_image() says | {image_prompt} | Later on we will use ComfyUI to make it!"

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
        + character_profile_changes + "\n"
        + cleaned_history
        )
    else:
        prompt = persona + "\n" + cleaned_history

    payload = {
        "prompt": prompt,
        "max_length": 200,
        "temperature": 0.8,
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
    global character_name, history, mood, outfit, char_location, inventory, description, pose, age
    
    new_name = req.get("name")
    if not new_name:
        return {"error": "No character name provided"}

    character_name = new_name

    load_character_data()
    load_history()

    return {
        "status": "ok",
        "character": character_name,
        "persona": persona,
        "mood": mood,
        "outfit": outfit,
        "location": char_location,
        "inventory": inventory,
        "description": description,
        "pose": pose,
        "age": age
    }

@app.post("/character/update")
def update_character(req: dict):
    global persona, mood, outfit, char_location, inventory, character_name, description, pose, age
    new_data = {}

    # Detect changes
    new_persona = req.get("persona", persona)
    if new_persona != persona:
        new_data["persona"] = new_persona

    new_mood = req.get("mood", mood)
    if new_mood != mood:
        new_data["mood"] = new_mood

    new_outfit = req.get("outfit", outfit)
    if new_outfit != outfit:
        new_data["outfit"] = new_outfit

    new_location = req.get("location", char_location)
    if new_location != char_location:
        new_data["location"] = new_location


# --- INVENTORY NORMALIZATION ---
    raw_inventory = req.get("inventory", inventory)

    if raw_inventory != inventory:
    # Normalize inventory
        if isinstance(raw_inventory, str):
        # Convert "Shears, Bucket" → ["Shears", "Bucket"]
            new_inventory = [item.strip() for item in raw_inventory.split(",") if item.strip()]
        else:
            new_inventory = raw_inventory
    else:
        new_inventory = inventory


    # --- DESCRIPTION NORMALIZATION ---
    raw_description = req.get("description", description)

    if raw_description != description:
        # Normalize description
        if isinstance(raw_description, list):
        # Convert ["a young man a farmer"] → "a young man a farmer"
            new_description = " ".join(raw_description)
        else:
            new_description = raw_description
    else:
    # No change → keep existing
        new_description = description

    # --- POSE ---
    raw_pose = req.get("pose", pose)

    if raw_pose != pose:
        if isinstance(raw_pose, list):
            new_pose = " ".join(raw_pose)
        else:
            new_pose = raw_pose
    else:
        new_pose = pose


    # --- AGE ---
    raw_age = req.get("age", age)

    if raw_age != age:
        if isinstance(raw_age, list):
            new_age = " ".join(raw_age)
        else:
            new_age = raw_age
    else:
        new_age = age
    # Test area.
    print("\n=== UPDATE_CHARACTER CALLED ===")
    print("Incoming request:", req)
    print("Current globals BEFORE update:")
    print(" persona =", persona)
    print(" mood =", mood)
    print(" outfit =", outfit)
    print(" location =", char_location)
    print(" inventory =", inventory, type(inventory))
    print(" description =", description, type(description))
    print(" pose =", pose, type(pose))
    print(" age =", age, type(age))

    # ⭐ FIX: Update globals FIRST
    persona = new_persona
    mood = new_mood
    outfit = new_outfit
    char_location = new_location
    inventory = new_inventory
    description = new_description
    pose = new_pose
    age = new_age
    # ⭐ THEN save to JSON
    if new_data:
        save_character_data(new_data)

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
