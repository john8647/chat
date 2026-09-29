# memory/stm.py

def clean_stm(history: str, max_lines: int = 20) -> str:
    """
    Short-Term Memory cleaner.
    Keeps only the last N meaningful lines.
    Removes blank lines, commands, and noise.
    """

    if not history:
        return ""

    lines = history.split("\n")

    cleaned = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        # Remove commands
        lower = line.lower()
        if lower.startswith("say "):
            continue
        if lower.startswith("said "):
            continue
        if lower.startswith("audio "):
            continue
        if lower.startswith("image "):
            continue

        # Remove markers
        if line.startswith("[IMAGE"):
            continue
        if line.startswith("[AUDIO"):
            continue

        cleaned.append(line)

    # Keep only last N lines
    stm = cleaned[-max_lines:]

    return "\n".join(stm)
