# memory/dialogue.py

dialogue_history = ""


def add_user_line(user_input: str):
    global dialogue_history
    dialogue_history += f"User: {user_input}\n"


def add_character_line(character_name: str, reply: str):
    global dialogue_history
    dialogue_history += f"{character_name}: {reply}\n"


def get_dialogue_history() -> str:
    return dialogue_history


def clear_dialogue_history():
    global dialogue_history
    dialogue_history = ""
