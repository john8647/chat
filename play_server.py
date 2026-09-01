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
reply_mode = True
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

# lora = {
# "Jimmy": "jimmy_f1",
# "Sarah": "sarah_f1",
# "Chloe": "chloe_f1"
# }

lora = {
    "Leah": "rosie_b",
    "Chloe": "chloe_f1"
}
voices = {
    "Leah": "voice - best one UK version 10-Leah.mp3",
    "Chloe": "voice - best one UK version 6-Chloe untested.mp3"
}
# character
persona = ""
mood = ""
outfit = ""
char_location = ""
inventory = []
emptyhanded = True
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


def generate_audio(dialog_script, user):
    global character_name, voices
    if not comfyui_alive():
        print(
            f"ComfyUI server is NOT alive or unreachable.  Was about to say {dialog_script} as {user}")
        return None
    workflow_path = "resources/comfyui_api/audio_workflow.json"
    with open(workflow_path, "r") as f:
        workflow = json.load(f)
        # 1. User speaking → use user's own voice
    if user == "User":
        workflow["3"]["inputs"]["audio"] = "voice - my own voice.mp3"
    else:
        # 2. Character speaking → look up voice
        voice_file = voices.get(character_name)

        if voice_file:
            # Known character → use mapped voice
            workflow["3"]["inputs"]["audio"] = voice_file
        else:
            # Unknown character → disable voice or use fallback
            workflow["3"]["inputs"]["audio"] = "a-male-voice-br-go.mp3"
    workflow["2"]["inputs"]["text"] = dialog_script

    resp = requests.post(f"{IMAGE_GEN_SERVER_URL}/prompt",
                         json={"prompt": workflow})
    # print("RAW AUDIO RESPONSE:", resp.text)

    data = resp.json()
    prompt_id = data["prompt_id"]
    print(prompt_id)
    result = None
    initialwait = True
    start_time = time.time()
    MAX_WAIT = 300

    while True:
        if time.time() - start_time > MAX_WAIT:
            print("ERROR: Audio generation timed out.")
            return None

        if initialwait:
            time.sleep(5)
            initialwait = False
            continue

        queue = requests.get(f"{IMAGE_GEN_SERVER_URL}/queue").json()
        all_items = (
            queue.get("queue_pending", []) +
            queue.get("queue_running", []) +
            queue.get("queue_done", [])
        )

        if not all_items:
            history_data = requests.get(
                f"{IMAGE_GEN_SERVER_URL}/history/{prompt_id}").json()
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

    # print("starting search")
    history_data = requests.get(
        f"{IMAGE_GEN_SERVER_URL}/history/{prompt_id}"
    ).json()

    # 1. Get the inner object for this prompt_id
    prompt_result = history_data.get(prompt_id)
    # print("no history")
    if not prompt_result:
        print("ERROR: No history entry for prompt_id", prompt_id)
        print(json.dumps(history_data, indent=4))
        # print("no history")
        return None

    # 2. Get outputs
    outputs = prompt_result.get("outputs", {})
    if not outputs:
        print("ERROR: Audio outputs missing in history for", prompt_id)
        print(json.dumps(prompt_result, indent=4))
        return None

    # 3. Find the audio node (13 here, but we’ll scan)
    # print("Audio file on he way: 1")
    audio_node = None
    for node_id, node_data in outputs.items():
        if isinstance(node_data, dict) and isinstance(node_data.get("audio"), list) and node_data["audio"]:
            audio_node = node_data
            break
    # print("Audio file on he way: 2")
    if not audio_node:
        print("ERROR: Audio output node not found in outputs")
        print(json.dumps(outputs, indent=4))
        return None

    audio_list = audio_node["audio"]
    audio_info = audio_list[0]
    audio_filename = audio_info["filename"]
    subfolder = audio_info.get("subfolder", "")

    # print("Audio file:", audio_filename, "subfolder:", subfolder)

    audio_data = requests.get(
        f"{IMAGE_GEN_SERVER_URL}/view?filename={audio_filename}&subfolder={subfolder}"
    ).content

    # print("Audio file on he way: 3")
    AUDIO_OUTPUT_DIR = os.path.join("G:/images", "audio")
    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
    safe_filename = os.path.basename(audio_filename)
    save_path = os.path.join(AUDIO_OUTPUT_DIR, safe_filename)

    with open(save_path, "wb") as f:
        f.write(audio_data)

    return safe_filename


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
    workflow["77"]["inputs"]["filename_prefix"] = random_prefix

    if character_name in lora:
        workflow["28"]["inputs"]["lora_1"]["on"] = "true"
        workflow["28"]["inputs"]["lora_1"]["lora"] = lora[character_name]
    else:
        # Unknown character → disable LoRA
        workflow["28"]["inputs"]["lora_1"]["on"] = "false"
        workflow["28"]["inputs"]["lora_1"]["lora"] = ""   # or leave unchanged

    resp = requests.post(f"{IMAGE_GEN_SERVER_URL}/prompt",
                         json={"prompt": workflow})
    data = resp.json()
    print("RAW IMAGE RESPONSE:", resp.text)

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
            history_data = requests.get(
                f"{IMAGE_GEN_SERVER_URL}/history/{prompt_id}").json()
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
    output_node = prompt_result["outputs"]["77"]
    filename = output_node["images"][0]["filename"]

    img_data = requests.get(
        f"{IMAGE_GEN_SERVER_URL}/view?filename={filename}").content

    IMAGE_OUTPUT_DIR = "G:/images"
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
    save_path = os.path.join(IMAGE_OUTPUT_DIR, filename)

    with open(save_path, "wb") as f:
        f.write(img_data)

    return filename


def generate_image_prompt():
    global character_name, outfit, char_location, description, age, pose, mood, inventory

    lora_name = lora.get(character_name, "")
    use_lora = bool(lora_name)

    if use_lora:
        subject_line = f"A real photo of {lora_name} {description}, age {age}."
    else:
        subject_line = f"A real photo of {description}, age {age}."

    image_prompt = (
        "Photorealistic.\n"
        f"{subject_line}\n"
        f"{pose}, looking {mood}.\n"
        f"Wearing {outfit}. "
        f"{build_holding_text(inventory)}\n"
        f"Scene: {char_location}."
        f"Image Details: high quality, raw, detailed skin texture with visible pores."
    )

    return image_prompt


def build_holding_text(inventory):
    if not inventory:
        return ""  # no holding line at all

    if len(inventory) == 1:
        return f"Holding a {inventory[0]}."

    if len(inventory) == 2:
        return f"Holding a {inventory[0]} and a {inventory[1]}."

    # 3 or more items
    items = ", ".join(inventory[:-1])
    last = inventory[-1]
    return f"Holding {items}, and a {last}."


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
                persona = data.get("persona", "").replace("\n", "")
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
    global character_profile_changes, persona, mood, outfit, char_location, inventory, character_name, description, pose, age, emptyhanded
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
        if (len(new_data['inventory']) > 0):
            if (emptyhanded == True):
                emptyhanded = False
                changes.append(
                    f"Inventory updated now is: {new_data['inventory']}")
        else:
            if (emptyhanded == False):
                changes.append(f"{character_name} has nothing in their hands.")
                emptyhanded = True
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


def test_requests(payload):
    global character_name

    test_replies = [
        f"{character_name} nods thoughtfully.",
        f"{character_name} adjusts his straw hat.",
        f"{character_name} looks around the farmyard.",
        f"{character_name} smiles warmly.",
        f"{character_name} takes a slow breath and continues.",
        f"{character_name} steps closer and speaks softly."
    ]

    # ⭐ MUST return a string, not a dict
    return random.choice(test_replies)


def clean_history_for_prompt(history: str) -> str:
    shortest_message = 18
    last_short_lines_kept_in = 6

    cleaned_lines = []

    # First pass: remove commands and image markers
    for raw_line in history.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Split speaker + content
        if ": " in line:
            speaker, content = line.split(": ", 1)
        else:
            speaker = ""
            content = line

        lower = content.lower().strip()

        # Remove image markers
        if content.startswith("[IMAGE"):
            continue

        # Remove audio markers
        if content.startswith("[AUDIO"):
            continue

        if lower.startswith("say "):
            continue
        if lower.startswith("said "):
            continue

        # Remove commands
        if lower == "show":
            continue
        # Remove commands
        if lower.startswith("audio "):
            continue
        if lower.startswith("image "):
            continue

        # Keep speaker + content together
        if speaker:
            cleaned_lines.append(f"{speaker}: {content}")
        else:
            cleaned_lines.append(content)

    # Second pass: short-line filtering
    final_lines = []
    total_lines = len(cleaned_lines)
    cutoff_index = total_lines - last_short_lines_kept_in

    for index, line in enumerate(cleaned_lines):
        # Extract content again for length check
        if ": " in line:
            _, content = line.split(": ", 1)
        else:
            content = line

        # Keep long lines always
        if len(content) >= shortest_message:
            final_lines.append(line)
            continue

        # Keep short lines only if they are in the last N lines
        if index >= cutoff_index:
            final_lines.append(line)
            continue

        # Otherwise skip short lines

    # ⭐ Real newlines for debug file
    # debug_output = "\n".join(final_lines)

    # with open("character_test_clean_history.json", "w", encoding="utf-8") as f:
    #    f.write(debug_output)

    # ⭐ Literal \n characters for the model
    cleaned_for_model = "\\n".join(final_lines)

    return cleaned_for_model


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

    if len(parts) == 2 and parts[0] == "audio":
        audioname = parts[1].strip()
        filename = f"{audioname}.flac"

        # Add to history (consistent with IMAGE format)
        history += f"{character_name}: [AUDIO:{filename}]\n"
        save_history()
        return {
            "type": "audio",
            "filename": filename,
            "caption": f"{character_name} said."
        }

    if len(parts) == 1 and parts[0] == "show" and TEST_MODE_IMAGE != True:
        filename = generate_image(generate_image_prompt())
        history += f"{character_name}: [IMAGE:{filename}]\n"
        save_history()
        return {
            "type": "image",
            "filename": filename,
            "caption": f"{character_name} sent."
        }

    parts = user_input.split(" ", 1)
    lower = user_input.lower()

    # SAY command (character speaks)
    if lower.startswith("say ") and len(parts) == 2:
        dialog_script = parts[1].strip()
        # print(dialog_script)
        filename = generate_audio(dialog_script, character_name)

    # Add marker to history
        history += f"{character_name}: [AUDIO:{filename}]\n"
        save_history()

        return {
            "type": "audio",
            "filename": filename,
            "caption": f"{character_name} said"
        }

    # SAID command (user speaks)
    if lower.startswith("said ") and len(parts) == 2:
        dialog_script = parts[1].strip()

        filename = generate_audio(dialog_script, "User")

        # Add marker to history
        history += f"User: [AUDIO:{filename}]\n"
        save_history()

        return {
            "type": "audio",
            "filename": filename,
            "caption": "You said"
        }

    # ⭐ If reply mode is OFF → do not generate AI replies
    if not reply_mode:
        print("Reply mode OFF — skipping AI reply.")
        history += f"User: {user_input}\n"
        save_history()
        return ""   # or return None or return {"reply": ""}

    history += f"User: {user_input}\n{character_name}: "
    # Build cleaned history (strip short messages, remove image markers)
    cleaned_history = clean_history_for_prompt(history)
    print(character_profile_changes)
    if character_profile_changes.strip():
        prompt = (
            persona
            + "\nRecent Updates are:\n"
            + character_profile_changes + "\n"
            + cleaned_history
        )
        character_profile_changes = character_profile_changes.strip()
    else:
        prompt = persona + "\n" + cleaned_history

    payload = {
        "prompt": prompt,
        "max_length": 200,
        "max_length": 50,
        "temperature": 0.6,
        "top_p": 0.7,
        "stop_sequence": ["User:", f"{character_name}:"]
    }

    with open("prompt_payload.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)

    if TEST_MODE:
        reply = test_requests(payload)
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

    raw = data.server_url.strip()

    # If nothing entered → stay in test mode
    if not raw:
        SERVER_URL = ""
        evaluate_test_mode()
        return {"ok": True, "msg": "No URL provided. Test mode remains active."}

    # Must start with http or https
    if not raw.startswith("http://") and not raw.startswith("https://"):
        SERVER_URL = ""
        evaluate_test_mode()
        return {"ok": False, "msg": "Invalid URL. Must start with http:// or https://"}

    # Append KoboldAI Lite endpoint if missing
    if not raw.endswith("/api/v1/generate"):
        raw = raw.rstrip("/") + "/api/v1/generate"

    SERVER_URL = raw

    evaluate_test_mode()
    return {"ok": True, "server_url": SERVER_URL}


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

    # ⭐ Normalize raw_inventory FIRST
    if isinstance(raw_inventory, str):
        # Convert "" → []
        # Convert "Bucket, Rope" → ["Bucket", "Rope"]
        normalized_inventory = [
            item.strip() for item in raw_inventory.split(",") if item.strip()
        ]
    else:
        # Already a list
        normalized_inventory = raw_inventory

    # ⭐ Now compare normalized inventory to previous inventory
    if normalized_inventory != inventory:
        # Inventory actually changed → record it
        new_data["inventory"] = normalized_inventory
    else:
        # No change → do NOT include inventory in new_data
        pass

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
    inventory = raw_inventory
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


@app.post("/reply_mode")
def set_reply_mode(data: dict):
    global reply_mode
    reply_mode = data.get("enabled", True)
    print("Reply mode set to:", reply_mode)
    return {"ok": True}


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
