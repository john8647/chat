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

        if (line.startsWith("User:")) {
            appendBubble(line.replace("User:", "").trim(), "you");
        } else if (line.startsWith(characterName + ":")) {
            appendBubble(line.replace(characterName + ":", "").trim(), "character");
        } else {
            appendBubble(line, "character");
        }
    }
}
