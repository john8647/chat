from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import random
import requests
import json
import os
import uuid
import time
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
TEST_MODE = True
TEST_MODE_IMAGE = True
SERVER_URL = ""
IMAGE_GEN_SERVER_URL = ""

def evaluate_test_mode():
    global TEST_MODE, TEST_MODE_IMAGE, SERVER_URL, IMAGE_GEN_SERVER_URL
    TEST_MODE = not SERVER_URL or not SERVER_URL.strip()
    TEST_MODE_IMAGE = not IMAGE_GEN_SERVER_URL or not IMAGE_GEN_SERVER_URL.strip()
    print("TEST_MODE =", TEST_MODE)
    print("TEST_MODE_IMAGE =", TEST_MODE_IMAGE)

# ---------------------------------------------------------
# Character globals
# ---------------------------------------------------------
character_name = "undefined"
character_profile_changes = ""

lora = {
    "Jimmy": "jimmy_f1",
    "Sarah": "sarah_f1",
    "Chloe": "chloe_f1"
}

persona = ""
mood = ""
outfit = ""
char_location = ""
inventory = []
history = ""
description = ""
pose = ""
age = ""

# ---------------------------------------------------------
# Image generation helpers
# ---------------------------------------------------------
def normalize_queue_item(item):
    if isinstance(item, list) and len(item) > 0 and isinstance(item[0], dict):
        return item[0]
    if isinstance(item, dict):
        return item
    return None

def comfyui_alive():
    try:
        r = requests.get(f"{IMAGE_GEN_SERVER_URL}/system_stats", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def generate_image(prompt):
    global character_name
    if not comfyui_alive():
        print("ComfyUI server is NOT alive or unreachable.")
        return None

    workflow_path = "resources/comfyui_api/image_workflow.json"
    with open(workflow_path, "r") as f:
        workflow = json.load(f)

    workflow["6"]["inputs"]["text"] = prompt
    random_prefix = str(uuid.uuid4())
    workflow["78"]["inputs"]["filename_prefix"] = random_prefix

    workflow["28"]["inputs"]["lora_1"]["on"] = "true" if character_name == "Chloe" else "false"

    resp = requests.post(f"{IMAGE_GEN_SERVER_URL}/prompt", json={"prompt": workflow})
    data = resp.json()
    prompt_id = data["prompt_id"]

    result = None
    initialwait = True
    start_time = time.time()
    MAX_WAIT = 300

    while True:
        if time.time() - start_time > MAX_WAIT:
            print("ERROR: Image generation timed out.")
            return None

        if initialwait:
            time.sleep(20)
            initialwait = False
            continue

        queue = requests.get(f"{IMAGE_GEN_SERVER_URL}/queue").json()
        all_items = (
            queue.get("queue_pending", []) +
            queue.get("queue_running", []) +
            queue.get("queue_done", [])
        )

        if not all_items:
            history_data = requests.get(f"{IMAGE_GEN_SERVER_URL}/history/{prompt_id}").json()
            result = history_data
            break

        for raw_item in all_items:
            item = normalize_queue_item(raw_item)
            if not item:
                continue
            if item.get("prompt_id") == prompt_id:
                status = item.get("status")
                if status in ("completed", "success", "done") or "outputs" in item:
                    result = item
                    break

        if result is not None:
            break

        time.sleep(1)

    prompt_result = result[prompt_id]
    output_node = prompt_result["outputs"]["78"]
    filename = output_node["images"][0]["filename"]

    img_data = requests.get(f"{IMAGE_GEN_SERVER_URL}/view?filename={filename}").content

    IMAGE_OUTPUT_DIR = "G:/images"
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
    save_path = os.path.join(IMAGE_OUTPUT_DIR, filename)

    with open(save_path, "wb") as f:
        f.write(img_data)

    return filename

# ---------------------------------------------------------
# Character data loading/saving
# ---------------------------------------------------------
def load_character_data():
    global persona, mood, outfit, char_location, inventory, description, pose, age, character_name

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
                description = data.get("description", "")
                pose = data.get("pose", "")
                age = data.get("age", "")
        except Exception as e:
            print("Error loading character data:", e)
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
    global persona, mood, outfit, char_location, inventory, description, pose, age, character_name

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
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---------------------------------------------------------
# History
# ---------------------------------------------------------
def history_filename():
    return f"{character_name}_history.json"

def save_history():
    with open(history_filename(), "w", encoding="utf-8") as f:
        json.dump({"history": history}, f, indent=2)

def load_history():
    global history
    filename = history_filename()
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                history = data.get("history", "")
        except Exception as e:
            print("Error loading history:", e)
    else:
        history = "Conversation history:\n"

load_character_data()
load_history()

# ---------------------------------------------------------
# Chat logic
# ---------------------------------------------------------
def send_message(user_input):
    global history, character_name, persona, character_profile_changes

    parts = user_input.lower().strip().split()

    if len(parts) == 2 and parts[0] == "image":
        imagename = parts[1]
        filename = f"{imagename}.png"
        history += f"{character_name}: [IMAGE:{filename}]\n"
        save_history()
        return {
            "type": "image",
            "filename": filename,
            "caption": f"{character_name}'s {imagename} today."
        }

    if len(parts) == 1 and parts[0] == "show":
        filename = generate_image(generate_image_prompt())
        history += f"{character_name}: [IMAGE:{filename}]\n"
        save_history()
        return {
            "type": "image",
            "filename": filename,
            "caption": f"{character_name} sent."
        }

    history += f"User: {user_input}\n{character_name}: "

    cleaned_history = history  # simplified for now

    prompt = persona + "\n" + cleaned_history

    payload = {
        "prompt": prompt,
        "max_length": 200,
        "temperature": 0.8,
        "top_p": 0.9,
        "stop_sequence": ["User:", f"{character_name}:"]
    }

    if TEST_MODE:
        reply = f"{character_name} nods thoughtfully."
    else:
        response = requests.post(SERVER_URL, json=payload)
        data = response.json()
        reply = data["results"][0]["text"].strip()

    history += reply + "\n"
    save_history()

    return reply

# ---------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------
app = FastAPI()

# ⭐ CORS FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⭐ Static mount BEFORE routes
app.mount("/images", StaticFiles(directory="G:/images"), name="images")

# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
class ServerUrlUpdate(BaseModel):
    server_url: str

@app.post("/update_server_url")
def update_server_url(data: ServerUrlUpdate):
    global SERVER_URL
    SERVER_URL = data.server_url.strip()
    evaluate_test_mode()
    return {"ok": True}

class ImageUrlUpdate(BaseModel):
    image_url: str

@app.post("/update_image_url")
def update_image_url(data: ImageUrlUpdate):
    global IMAGE_GEN_SERVER_URL
    IMAGE_GEN_SERVER_URL = data.image_url.strip()
    evaluate_test_mode()
    return {"ok": True}

class ChatRequest(BaseModel):
    message: str


@app.get("/ping_server")
def ping_server():
    import requests
    try:
        r = requests.get(SERVER_URL, timeout=3)
        print("PASS Ping test")
        print(TEST_MODE)
        print(TEST_MODE_IMAGE)
        return {"ok": True, "status": r.status_code}
    except Exception as e:
        print("Fail Ping test")
        print(TEST_MODE)
        print(TEST_MODE_IMAGE)
        return {"ok": False, "error": str(e)}



@app.post("/chat")
def chat(req: ChatRequest):
    reply = send_message(req.message)
    return {"reply": reply}

@app.get("/history")
def get_history():
    return {"history": history}

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
            new_data["inventory"] = new_inventory
        else:
            new_inventory = raw_inventory
            new_data["inventory"] = new_inventory
    else:
        new_inventory = inventory


    # --- DESCRIPTION NORMALIZATION ---
    raw_description = req.get("description", description)

    if raw_description != description:
        # Normalize description
        if isinstance(raw_description, list):
        # Convert ["a young man a farmer"] → "a young man a farmer"
            new_description = " ".join(raw_description)
            new_data["description"] = new_description
        else:
            new_description = raw_description
            new_data["description"] = new_description
    else:
    # No change → keep existing
        new_description = description

    # --- POSE ---
    raw_pose = req.get("pose", pose)

    if raw_pose != pose:
        if isinstance(raw_pose, list):
            new_pose = " ".join(raw_pose)
            new_data["pose"] = new_pose
        else:
            new_pose = raw_pose
            new_data["pose"] = new_pose
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

@app.get("/favicon.ico")
def favicon():
    return {}

@app.get("/character")
def get_character():
    return {"name": character_name}

@app.get("/active_character")
def active_character():
    return {"character": character_name}

@app.post("/direct_character_say")
async def direct_character_say(data: dict):
    global history, character_name

    character = data.get("character")
    text = data.get("text")

    if not character or not text:
        return {"ok": False, "error": "Missing character or text"}

    # Append to in‑memory history
    history += f"{character}: {text}\n"

    # Save to correct per‑character history file
    with open(history_filename(), "w", encoding="utf-8") as f:
        json.dump({"history": history}, f, indent=2)

    print(f"[DIRECT] {character}: {text}")

    return {"ok": True}


@app.get("/")
def root():
    return {"status": "Python game server running"}

# ---------------------------------------------------------
# Run server LAST
# ---------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
