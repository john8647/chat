import json
import os

# -----------------------------
# CONFIG
# -----------------------------
DATASET_DIR = "datasets"
POSE_FILE = os.path.join(DATASET_DIR, "pose_keywords.json")
MOOD_FILE = os.path.join(DATASET_DIR, "mood_keywords.json")
OUTFIT_FILE = os.path.join(DATASET_DIR, "outfit_keywords.json")

os.makedirs(DATASET_DIR, exist_ok=True)


# -----------------------------
# LOAD / SAVE JSON
# -----------------------------
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


pose_dict = load_json(POSE_FILE)
mood_dict = load_json(MOOD_FILE)
outfit_dict = load_json(OUTFIT_FILE)


# -----------------------------
# CHECK IF PHRASE ALREADY MAPPED
# -----------------------------
def phrase_already_mapped(phrase):
    phrase_lower = phrase.lower()

    for d in (pose_dict, mood_dict, outfit_dict):
        for canonical, phrases in d.items():
            if any(phrase_lower == p.lower() for p in phrases):
                return True
    return False


# -----------------------------
# ADD MAPPING
# -----------------------------
def add_mapping(category, phrase, canonical):
    phrase = phrase.strip()

    if category == "pose":
        d = pose_dict
        path = POSE_FILE
    elif category == "mood":
        d = mood_dict
        path = MOOD_FILE
    elif category == "outfit":
        d = outfit_dict
        path = OUTFIT_FILE
    else:
        return

    if canonical not in d:
        d[canonical] = []

    if phrase not in d[canonical]:
        d[canonical].append(phrase)

    save_json(path, d)
    print(f"Saved mapping: '{phrase}' → {canonical} ({category})")


# -----------------------------
# TRAINER LOOP
# -----------------------------
def train_from_file(filepath):
    if not os.path.exists(filepath):
        print("File not found:", filepath)
        return

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print("\n=== TRAINING STARTED ===")
    print(f"Loaded {len(lines)} lines from {filepath}\n")

    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        print(f"\nLine {idx}: {line}")

        # Step 1: choose phrase inside the line
        print("\nEnter the phrase to map from this line,")
        print("or just press ENTER to skip this line.")
        phrase = input("Phrase: ").strip()

        if not phrase:
            print("Skipping line.")
            continue

        # If phrase already mapped, skip
        if phrase_already_mapped(phrase):
            print("Phrase already mapped — skipping.")
            continue

        # Step 2: choose category
        print("\nDoes this phrase affect:")
        print("1. Pose")
        print("2. Mood")
        print("3. Outfit")
        print("4. None (cancel)")

        choice = input("Enter choice (1-4): ").strip()

        if choice == "4":
            print("Cancelled for this phrase.")
            continue

        category_map = {"1": "pose", "2": "mood", "3": "outfit"}

        if choice not in category_map:
            print("Invalid choice — skipping phrase.")
            continue

        category = category_map[choice]

        # Step 3: show existing canonical keywords for that category
        if category == "pose":
            d = pose_dict
        elif category == "mood":
            d = mood_dict
        else:
            d = outfit_dict

        print("\nDoes this phrase map to an existing keyword:")
        if d:
            for i, canonical in enumerate(d.keys(), start=1):
                print(f"{i}. {canonical}")
        else:
            print("(No existing keywords yet.)")

        print("Or type: New <keyword>")
        mapping_choice = input("Enter choice: ").strip()

        # Handle new canonical keyword
        if mapping_choice.lower().startswith("new "):
            canonical = mapping_choice[4:].strip()
            if not canonical:
                print("No keyword provided — skipping.")
                continue
            add_mapping(category, phrase, canonical)
            continue

        # Handle existing canonical keyword
        try:
            index = int(mapping_choice)
            canonical = list(d.keys())[index - 1]
            add_mapping(category, phrase, canonical)
        except:
            print("Invalid choice — skipping phrase.")

    print("\n=== TRAINING COMPLETE ===\n")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("Character Phrase Trainer")
    filepath = input("Enter path to story file: ").strip()
    train_from_file(filepath)
