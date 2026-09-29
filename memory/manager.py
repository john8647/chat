# memory/manager.py
import json
from memory.stm import clean_stm
from memory.wm import summarise_with_llm, load_summary, save_summary
from memory.ltm import extract_stable_facts, update_character_ltm


def update_memory(stm):

    with open("memory_debug.json", "w", encoding="utf-8") as f:
        json.dump({
            "stm": stm
        }, f, indent=2)

    return stm


def build_prompt(persona: str, ltm: list, wm: str, stm: str, user_input: str):
    """
    Builds the final prompt for the LLM.
    """

    ltm_text = "\n".join(ltm)

    prompt = f"""
[PERSONA]
{persona}

[LONG-TERM MEMORY]
{ltm_text}

[WORKING MEMORY]
{wm}

[RECENT HISTORY]
{stm}

[USER INPUT]
{user_input}

Respond as the character.
"""

    return prompt.strip()
