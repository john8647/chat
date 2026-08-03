const chat = document.getElementById("chat");
const input = document.getElementById("input");

function appendBubble(text, who) {
    const row = document.createElement("div");
    row.className = "message-row " + (who === "you" ? "message-right" : "message-left");

    const avatar = document.createElement("img");
    avatar.className = "avatar-chat";
    avatar.src = who === "you" ? "images/you.png" : "images/" + characterName + ".png";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble " + (who === "you" ? "message-right" : "message-left");

    const timestamp = document.createElement("div");
    timestamp.className = "timestamp";
    timestamp.textContent = formatTimestamp(new Date());

    bubble.innerHTML = text;
    bubble.appendChild(timestamp);

    if (who === "you") {
        row.appendChild(bubble);
        row.appendChild(avatar);
    } else {
        row.appendChild(avatar);
        row.appendChild(bubble);
    }

    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
}



function showTyping() {
    setStatus("Typing...");

    const row = document.createElement("div");
    row.className = "message-row message-left";
    row.id = "typingRow";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble message-left";

    bubble.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    row.appendChild(bubble);
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
}

function appendImageBubble(filename, caption) {
    const row = document.createElement("div");
    row.className = "message-row message-left";

    const avatar = document.createElement("img");
    avatar.className = "avatar-chat";
    avatar.src = "images/" + characterName + ".png";

    const bubble = document.createElement("div");
    bubble.className = "image-bubble";

    const img = document.createElement("img");
    img.src = "images/" + filename;
    img.className = "chat-image";

    const cap = document.createElement("div");
    cap.className = "image-caption";
    cap.textContent = caption;

    bubble.appendChild(img);
    bubble.appendChild(cap);

    row.appendChild(avatar);
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

    const parts = text.split(" ");
    const isImageCommand = parts[0].toLowerCase() === "image" && parts.length === 2;

    // Only show user bubble if NOT an image command
    if (!isImageCommand) {
        appendBubble(text, "you");
    }

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

    if (data.reply && data.reply.type === "image") {
        
        appendImageBubble(data.reply.filename, data.reply.caption);
    } else {
        
        appendBubble(data.reply, "character");
    }
}



function formatTimestamp(date) {
    const now = new Date();
    const diff = now - date;
    const oneDay = 24 * 60 * 60 * 1000;

    // Today → show HH:MM
    if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString("en-GB", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false
        });
    }

    // Last 7 days → show weekday
    if (diff < 7 * oneDay) {
        return date.toLocaleDateString("en-GB", { weekday: "short" });
    }

    // Older → show full date
    return date.toLocaleDateString("en-GB", {
        day: "numeric",
        month: "long",
        year: "numeric"
    });
}


input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});
