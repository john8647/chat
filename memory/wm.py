
# memory/wm.py

import json
import os

SUMMARY_FILE = "memory_summary.json"


def summarise_with_llm(llm, stm, thinking_about):
    summary = llm(stm)

    if thinking_about:
        summary += f"\n- internal thought:\n    + {thinking_about}"

    return summary


def load_summary() -> str:
    if os.path.exists(SUMMARY_FILE):
        with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("summary", "")
    return ""


def save_summary(summary: str):
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump({"summary": summary}, f, indent=2)
