
const ws = new WebSocket("ws://192.168.0.121:8000/ws");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // Only process API-originated websocket messages

    // API-submitted user speech should enter the normal chat flow.
    const speaker = typeof data.character === "string" ? data.character.trim().toLowerCase() : "";
    //console.log("Print we are here")
    if (data.source === "api" && data.type === "direct_say" && ["me", "user"].includes(speaker)) {
        const text = data.reply && typeof data.reply.text === "string"
            ? data.reply.text
            : data.text;
        if (typeof text === "string" && text.trim()) {
            handleNormalChat({ type: "normal_chat", raw: text })
                .catch((error) => console.error("Failed to process API user speech:", error));
        }
        return;
    }

    // Direct speech
    if (data.source === "api" && data.type === "direct_say" && (characterName === data.character || data.character === 'you')) {
        const reply = data.reply;
        console.log(data)
        console.log("Client detected a message via the API")
        if (!reply) {
            // legacy fallback
            appendBubble(data.text, data.character);
            return;
        }

        switch (reply.type) {
            case "text":
                appendBubble(reply.text, data.character);
                break;

            case "audio":
                appendAudioBubble(reply.filename, reply.caption, data.character, true);
                break;

            case "image":
                appendImageBubble(reply.filename, reply.caption);
                break;

            default:
                handleReply(reply);
                break;
        }

        return;
    }

    // Direct command (remote-triggered chat)
    if (data.source !== "api" && data.type === "direct_command" && characterName === data.character) {

        const reply = data.reply;
        const firstWord = data.command.split(" ")[0].toLowerCase();
        const skipBubbleCommands = ["say", "said", "audio", "image", "view", "show"];

        // IMAGE reply
        if (reply && reply.type === "image") {
            appendImageBubble(reply.filename, reply.caption);
            return;
        }

        // Only show "you" bubble if command is NOT a TTS/image/show command
        if (!skipBubbleCommands.includes(firstWord)) {
            appendBubble(data.command, "you");
        }

        // Route reply normally
        handleReply(reply);

        return;
    }


};





async function loadCharacterName() {
    const res = await fetch("http://192.168.0.121:8000/active_character");
    const data = await res.json();
    characterName = data.character;
}


function handleReply(reply) {
    console.log("Character reply only _ after handle object 1");
    // Determine speaker
    const who = reply.caption === "You said" ? "you" : "character";

    // Route by type
    if (reply.type === "text") {
        appendBubble(reply.text, who);
        return;
    }

    if (reply.type === "image") {
        appendImageBubble(reply.filename, reply.caption);
        return;
    }

    if (reply.type === "audio") {
        appendAudioBubble(reply.filename, reply.caption, who, true);
        return;
    }

    if (reply.type === "audio_text") {
        appendBubble(reply.text, who);
        appendAudioBubble(reply.filename, reply.caption, who, true);
        return;
    }

    if (reply.type === "none") {
        return;
    }

    console.warn("Unknown reply type:", reply);
}




loadCharacterName();

const chat = document.getElementById("chat");
const input = document.getElementById("input");

function appendImageBubble(filename, caption) {
    const character_image = window.character_image;
    const row = document.createElement("div");
    row.className = "message-row message-left";

    const avatar = document.createElement("img");
    avatar.className = "avatar-chat";
    avatar.src = "http://192.168.0.121:8000/images/" + character_image + ".png";

    const bubble = document.createElement("div");
    bubble.className = "image-bubble";

    const img = document.createElement("img");
    img.src = "http://192.168.0.121:8000/images/" + filename;
    img.className = "chat-image";

    img.onclick = function () {
        //console.log("Thumbnail clicked for:", filename);
        openImageModal("http://192.168.0.121:8000/images/" + filename);
    };

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

function appendAudioBubble(filename, caption, who, autoplay = false) {
    const character_image = window.character_image;

    const row = document.createElement("div");
    row.className = "message-row " + (who === "you" ? "message-right" : "message-left");

    const avatar = document.createElement("img");
    avatar.className = "avatar-chat";
    avatar.src = who === "you"
        ? "http://192.168.0.121:8000/images/characters/you.png"
        : "http://192.168.0.121:8000/images/" + character_image + ".png";

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble " + (who === "you" ? "audio-bubble-right" : "audio-bubble");

    const audio = document.createElement("audio");
    audio.controls = true;
    audio.preload = "none";

    const source = document.createElement("source");
    source.src = "http://192.168.0.121:8000/images/audio/" + filename;
    source.type = "audio/flac";
    audio.appendChild(source);

    // ⭐ Only autoplay if explicitly requested
    if (autoplay) {
        audio.autoplay = true;
        audio.addEventListener("canplay", () => {
            audio.play().catch(err => console.warn("Autoplay blocked:", err));
        });
    }

    const cap = document.createElement("div");
    cap.className = "audio-caption";
    cap.textContent = caption;

    bubble.appendChild(audio);
    bubble.appendChild(cap);

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

function appendBubble(text, who) {

    text = text.replace(/\\n/g, "\n");

    // ⭐ Split multi-line messages into separate bubbles
    if (typeof text === "string" && text.includes("\n")) {
        //console.log("instant message split up into more that one bubble")
        const lines = text
            .split(/\r?\n/)
            .map(line => line.trim())
            .filter(line => line.length > 0);

        for (const line of lines) {
            appendBubble(line, who);
        }

        return;
    }

    //console.log("Beginning speak 1")
    const character_image = window.character_image;
    const row = document.createElement("div");
    row.className = "message-row " + (who === "you" ? "message-right" : "message-left");

    const avatar = document.createElement("img");
    avatar.className = "avatar-chat";
    avatar.src = who === "you" ? "http://192.168.0.121:8000/images/characters/you.png" : "http://192.168.0.121:8000/images/" + character_image + ".png";

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


function openImageModal(src) {
    //console.log("openImageModal called with:", src);

    const modal = document.getElementById("image-modal");
    const img = document.getElementById("image-modal-img");

    if (!modal) {
        console.log("ERROR: #image-modal not found in DOM");
        return;
    }

    if (!img) {
        console.log("ERROR: #image-modal-img not found in DOM");
        return;
    }

    img.src = src;
    //console.log("Image src set:", img.src);

    //modal.classList.remove("hidden");
    document.getElementById("image-modal").classList.remove("hidden");
    //console.log("Modal should now be visible");
}



document.getElementById("image-modal-backdrop").onclick = () => {
    document.getElementById("image-modal").classList.add("hidden");
};


document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("image-modal");
    //console.log("Modal display:", window.getComputedStyle(modal).display);
});





const cap = document.createElement("div");
cap.className = "image-caption";

function hideTyping() {
    const row = document.getElementById("typingRow");
    if (row) row.remove();
    setStatus("Online");
}

async function sendMessage() {
    let text = input.value.trim();
    if (!text) return;
    input.value = "";

    const parsed = classifyInput(text);

    // ⭐ Route based on classification
    if (parsed.type === "direct_speech") {
        return await handleDirectSpeech(parsed);
    }

    if (parsed.type === "command") {
        return await handleCommand(parsed);
    }

    return await handleNormalChat(parsed);
}


function classifyInput(text) {
    const firstLetter = characterName[0].toLowerCase();
    const colonParts = text.split(":");

    // ⭐ Direct speech: "J: hello"
    if (colonParts.length > 1 && colonParts[0].trim().toLowerCase() === firstLetter) {
        return {
            type: "direct_speech",
            args: colonParts.slice(1).join(":").trim(),
            raw: text
        };
    }

    // ⭐ Commands
    const parts = text.split(" ");
    const cmd = parts[0].toLowerCase();

    const commands = ["image", "audio", "say", "said", "show", "view"];
    if (commands.includes(cmd)) {
        return {
            type: "command",
            command: cmd,
            args: parts.slice(1).join(" "),
            raw: text
        };
    }

    // ⭐ Normal chat
    return {
        type: "normal_chat",
        raw: text
    };
}


async function handleDirectSpeech(parsed) {

    // ⭐ If character = Me/User → treat as normal chat
    if (["me", "user"].includes(characterName.toLowerCase())) {
        return await handleNormalChat(parsed);
    }

    const res = await fetch("http://192.168.0.121:8000/direct_character_say", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            character: characterName,
            text: parsed.args,
            source: "ui"
        })
    });
    const data = await res.json();
    handleReplyObject(data);
}


async function handleCommand(parsed) {

    // Skip showing "you" bubble for commands
    const skipBubble = ["image", "audio", "say", "said", "show", "view"];
    if (!skipBubble.includes(parsed.command)) {
        appendBubble(parsed.raw, "you");
    }

    const res = await fetch("/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: parsed.raw })
    });

    const data = await res.json();
    handleReplyObject(data);
    //console.log("handle image")
}


async function handleNormalChat(parsed) {
    if (!(window.tts_mode_js === "everybody_talking" ||
        window.tts_mode_js === "everybody_talking_with_text")) {
        appendBubble(parsed.raw, "you");
    }

    const res = await fetch("/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: parsed.raw })
    });

    const data = await res.json();
    handleReplyObject(data);
}


function handleReplyObject(data) {

    if (
        data.reply?.user_reply?.type === "audio" &&
        data.reply?.character_reply?.type === "audio" ||
        data.reply?.user_reply?.type === "audio_text" &&
        data.reply?.character_reply?.type === "audio_text"
    ) {
        //console.log(data)
        handleReply(data.reply.user_reply);

        setTimeout(() => {
            handleReply(data.reply.character_reply);
        }, 15000);

        return;
    }

    if (data.reply?.character_reply) {
        //console.log(data)
        console.log("Character reply only");
        handleReply(data.character_reply);
        return;
    }

    if (data.reply) {
        //console.log("Normal reply");
        handleReply(data.reply);
        return;
    }

    console.warn("Unknown reply bundle:", data);
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
