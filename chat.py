import requests

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

SERVER_URL = "https://interact-italia-knitting-repository.trycloudflare.com:443/api/v1/generate"
character_name = "Jimmy"
lora = {"Jimmy": "Jimmy_0303"}

#Test area
import random

test_replies = [
    f"{character_name} nods thoughtfully.",
    f"{character_name} adjusts his straw hat.",
    f"{character_name} looks around the farmyard.",
    f"{character_name} smiles warmly.",
    f"{character_name} takes a slow breath and continues.",
    f"{character_name} steps closer and speaks softly."
]

def test_requests(payload):
    """
    Fake request handler for test mode.
    Returns a random reply from test_replies.
    """
    reply = random.choice(test_replies)
    return {
        "results": [
            {"text": reply}
        ]
    }

TEST_MODE = True   # Set to False to use the real API


# Full chat history (User + {character_name} dialogue)
persona = f"""
You are {character_name}, an old farmer..
You only wear farm clothes.
You enjoy when John looks after you. Only talk about yourself.
"""


# Conversation memory
history = persona + "Conversation history:\n"

# Structured world/character state
character_state = {
    "outfit": "black jumper, black trousers and brown shoes",
    "location": "living room",
    "time": "late afternoon",
    "mood": "calm"
}

# ---------------------------------------------------------
# Utility: Extract recent chat context
# ---------------------------------------------------------
def get_clean_recent_context(history, persona, character_name,
                             min_length=20, max_lines=6):
    """
    Combines get_recent_context + get_clean_recent_context:
    1. Extract last 6 lines of history.
    2. If persona tail (last 2 words) appears in those lines,
       trim everything before that point.
    3. Clean lines (remove prefixes, strip quotes, enforce min length).
    """

    # --- Step 1: Extract last 6 lines ---
    history_lines = history.strip().split("\n")
    recent_lines = history_lines[-max_lines:] if len(history_lines) >= max_lines else history_lines
    recent_text = "\n".join(recent_lines)

    # --- Step 2: Persona tail trimming ---
    persona_words = persona.strip().split()
    if len(persona_words) >= 2:
        persona_tail = " ".join(persona_words[-2:])
    else:
        persona_tail = persona_words[-1] if persona_words else ""

    # If persona tail appears in the recent lines, trim everything before it
    if persona_tail and persona_tail in recent_text:
        recent_text = recent_text.split(persona_tail, 1)[1].strip()

    # Re-split after trimming
    lines = recent_text.split("\n")

    # --- Step 3: Clean lines ---
    cleaned = []
    TRIPLE_DQ = '"""'
    TRIPLE_SQ = "'''"

    for line in reversed(lines):

        # Remove speaker prefixes
        if line.startswith("User:"):
            line = line.replace("User:", "").strip()
        elif line.startswith(f"{character_name}:"):
            line = line.replace(f"{character_name}:", "").strip()

        # Remove triple quotes
        line = line.replace(TRIPLE_DQ, "").replace(TRIPLE_SQ, "").strip()

        # Skip empty or too-short lines
        if len(line) < min_length:
            continue

        cleaned.append(line)

        if len(cleaned) >= max_lines:
            break

    cleaned.reverse()
    return "\n".join(cleaned)




# ---------------------------------------------------------
# Core: Normal chat message handler
# ---------------------------------------------------------

def send_message(user_input):
    """
    Sends a normal chat message to the text-generation API.
    Maintains the conversation history exactly like your PowerShell version.
    """
    global history

    # Append user message to history
    history += f"User: {user_input}\n{character_name}: "

    # Build JSON payload
    payload = {
        "prompt": history,
        "max_length": 200,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop_sequence": ["User:", f"{character_name}:"]
    }

    # Choose real or test mode
    if TEST_MODE:
        data = test_requests(payload)
    else:
        response = requests.post(SERVER_URL, json=payload)
        data = response.json()

    # Extract reply text
    reply = data["results"][0]["text"].strip()

    # Append reply to history
    history += reply + "\n"

    return reply

def get_history():
    return history

# ---------------------------------------------------------
# Command: Illustrate the current scene
# ---------------------------------------------------------
def illustrate_scene():
    """
    Builds a photographic-style scene prompt using:
    - recent chat context
    - structured character state
    - clear instruction to describe a realistic image scene

    In TEST_MODE:
        Returns the prompt directly so you can inspect it.
    In real mode:
        Sends the prompt to the LLM and returns its response.
    """
    recent = get_clean_recent_context(history, persona, character_name)
    # Build the new photographic-style prompt
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
Incorporate any actions or events implied by the following recent context:
\"\"\"{recent}\"\"\"

Task:
Create a vivid, immersive photographic-style description focusing on:
- the person and their outfit first
- the environment second
- any actions or motion suggested by recent events
- lighting and atmosphere based on time and mood
"""
    TRIPLE_DQ = '"""'
    TRIPLE_SQ = "'''"
    prompt = prompt.replace(TRIPLE_DQ, '').replace(TRIPLE_SQ, '').strip()

    payload = {
        "prompt": prompt,
        "max_length": 300,
        "temperature": 0.7,
        "top_p": 0.9
    }

    # TEST MODE: return the prompt instead of calling the API
    if TEST_MODE:
        return f"[TEST MODE — Prompt Sent to LLM]\n\n{prompt}"

    # REAL MODE: call the API
    response = requests.post(SERVER_URL, json=payload)
    data = response.json()

    return data["results"][0]["text"].strip()


# ---------------------------------------------------------
# Main Loop
# ---------------------------------------------------------

print("Chat started. Type 'exit' to quit.\n")
print("Commands available:")
print("'image'- illustrate the current scene\n")
print("'history'- the current history set\n")
print("'quit'- exit\n")

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    # Command mode
    if user_input.lower() == "history":
        print(f"\n{get_history()}\n")
        continue

    # Command mode
    if user_input.lower() == "image":
        scene = illustrate_scene()
        print(f"\n{scene}\n")
        continue

    # Normal chat mode
    ai_reply = send_message(user_input)
    print(f"{character_name}: {ai_reply}\n")
