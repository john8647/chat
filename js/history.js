async function fetchHistory() {
    const res = await fetch("/history");
    const data = await res.json();

    const chat = document.getElementById("chat");
    chat.innerHTML = "";

    const lines = data.history.split("\n");

    for (let line of lines) {
        line = line.trim();
        if (!line) continue;
        if (line.startsWith("Conversation history")) continue;

        // USER MESSAGES
        if (line.startsWith("User:")) {
            appendBubble(line.replace("User:", "").trim(), "you");
            continue;
        }

        // CHARACTER IMAGE MESSAGES
        if (line.includes("[IMAGE:")) {
            const match = line.match(/\[IMAGE:(.+?)\]/);
            if (match) {
                const filename = match[1];
                appendImageBubble(filename, `${characterName}'s image`);
            }
            continue;
        }

        // CHARACTER TEXT MESSAGES
        if (line.startsWith(characterName + ":")) {
            appendBubble(line.replace(characterName + ":", "").trim(), "character");
            continue;
        }

        // FALLBACK (character text)
        appendBubble(line, "character");
    }
}
