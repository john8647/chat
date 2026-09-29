# memory/ltm.py

import json
import os


def extract_stable_facts(summary: str):
    """
    Extract stable facts from WM summary.
    Very simple rule-based extractor.
    """

    facts = []

    lines = summary.split("\n")
    for line in lines:
        lower = line.lower()

        # Example rules — expand later
        if "likes" in lower or "prefers" in lower:
            facts.append(line)

        if "is currently" in lower:
            facts.append(line)

        if "promised" in lower:
            facts.append(line)

        if "dislikes" in lower:
            facts.append(line)

    return facts


def update_character_ltm(character_name: str, facts: list):
    """
    Updates the character JSON with new stable facts.
    """

    filename = f"{character_name}.json"

    if not os.path.exists(filename):
        return

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Add facts to LTM
    existing = data.get("long_term_memory", [])
    merged = list(set(existing + facts))
    data["long_term_memory"] = merged

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
