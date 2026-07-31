const chat = document.getElementById("chat");
const input = document.getElementById("input");

function appendBubble(text, who) {
    const row = document.createElement("div");
    row.className = "message-row " + (who === "you" ? "you" : "character");

    const bubble = document.createElement("div");
    bubble.className = "message-bubble " + (who === "you" ? "you" : "character");
    bubble.innerHTML = text;

    row.appendChild(bubble);
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
}

function showTyping() {
    setStatus("Typing...");

    const row = document.createElement("div");
    row.className = "message-row character";
    row.id = "typingRow";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble character";

    bubble.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    row.appendChild(bubble);
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
}

function hideTyping() {
    const row = document.getElementById("typingRow");
    if (row) row.remove();
    setStatus("Online");
}

async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    appendBubble(text, "you");
    input.value = "";
    input.focus();

    showTyping();

    const res = await fetch("/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
    });

    const data = await res.json();

    hideTyping();
    appendBubble(data.reply, "character");
}

input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});
