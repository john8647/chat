const mode = window.tts_mode_js;


async function loadCharacterName() {
    const res = await fetch("http://192.168.0.121:8000/active_character");
    const data = await res.json();
    characterName = data.character;
}

function handleReply(reply) {

    // Determine speaker
    const who = reply.caption === "You said" ? "you" : "character";

    // Route by type
    if (reply.type === "text") {
        appendBubble(reply.text, who);
        return;
    }

    if (reply.type === "audio") {
        appendAudioBubble(reply.filename, reply.caption, who);
        return;
    }

    if (reply.type === "audio_text") {
        appendBubble(reply.text, who);
        appendAudioBubble(reply.filename, reply.caption, who);
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
    const row = document.createElement("div");
    row.className = "message-row message-left";

    const avatar = document.createElement("img");
    avatar.className = "avatar-chat";
    avatar.src =  "http://192.168.0.121:8000/images/" + characterName + ".png";

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

function appendAudioBubble(filename, caption, who) {
    console.log("Append audio bubble called! 1")


    // ⭐  Audio bubble creation split here
    const row = document.createElement("div");
    row.className = "message-row " + (who === "you" ? "message-right" : "message-left");

    const avatar = document.createElement("img");
    avatar.className = "avatar-chat";
    avatar.src = who === "you" ? "http://192.168.0.121:8000/images/you.png" : "http://192.168.0.121:8000/images/" + characterName + ".png";

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble " + (who === "you" ? "audio-bubble-right" : "audio-bubble");


    // Create audio player
    const audio = document.createElement("audio");
    audio.controls = true;
    audio.preload = "none";

    const source = document.createElement("source");
    source.src = "http://192.168.0.121:8000/images/audio/" + filename;
    source.type = "audio/flac";

    audio.appendChild(source);

    // Optional caption (same style as images)
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



function appendBubble(text, who) {
    console.log("Beginning speak 1")

    // ⭐ If this is an image marker, redirect to appendImageBubble
    if (text.includes("[IMAGE:")) {
        const match = text.match(/\[IMAGE:(.+?)\]/);
        if (match) {
            const filename = match[1];
            appendImageBubble(filename, `${characterName} sent.`);
            return; // ⭐ Stop normal bubble rendering
        }
    }

    if (text.includes("[AUDIO:")) {
        const match = text.match(/\[AUDIO:(.+?)\]/);
        if (match) {
            const filename = match[1];
            appendAudioBubble(filename, `${characterName} said.`);
            return; // ⭐ Stop normal bubble rendering
        }
    }

    // ⭐ Normal text bubble continues here
    const row = document.createElement("div");
    row.className = "message-row " + (who === "you" ? "message-right" : "message-left");

    const avatar = document.createElement("img");
    avatar.className = "avatar-chat";
    avatar.src = who === "you" ? "http://192.168.0.121:8000/images/you.png" : "http://192.168.0.121:8000/images/" + characterName + ".png";

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

function appendBubble(text, who) {
    
    const row = document.createElement("div");
    row.className = "message-row " + (who === "you" ? "message-right" : "message-left");

    const avatar = document.createElement("img");
    avatar.className = "avatar-chat";
    avatar.src = who === "you" ? "http://192.168.0.121:8000/images/you.png" : "http://192.168.0.121:8000/images/" + characterName + ".png";

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
    input.value = "";
    if (!text) return;

    const firstLetter = characterName[0].toLowerCase();

    // ⭐ Direct speech
    const colonParts = text.split(":");
    if (colonParts.length > 1 && colonParts[0].trim().toLowerCase() === firstLetter) {

        const directText = colonParts.slice(1).join(":").trim();

        const res = await fetch("http://192.168.0.121:8000/direct_character_say", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                character: characterName,
                text: directText
            })
        });

        const data = await res.json();

        console.log("Reply received:", data.reply);
        handleReply(data.reply);

        
        return;
    }


    // ⭐ Image command
    const spaceParts = text.split(" ");
    const isImageCommand = 
        spaceParts[0].toLowerCase() === "image" &&
        spaceParts.length === 2;

    if (isImageCommand) {
        //appendBubble(text, "you");
        //console.log("HERE! 0")
        const res = await fetch("/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        const data = await res.json();

        // ⭐ Always show image result even if replyMode = OFF
        appendImageBubble(data.reply.filename, data.reply.caption);

        //input.value = "";
        return;
    }
    //console.log(text)
    // ⭐ Show command
    if (text.toLowerCase() === "show" && IMAGE_GEN_SERVER_URL.length > 1) {
        //appendBubble(text, "you");
        //console.log("HERE!")
        const res = await fetch("/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        //input.value = "";
        const data = await res.json();

        appendImageBubble(data.reply.filename, data.reply.caption);

        
        return;
    }

    if (text.toLowerCase() === "view") {
        //appendBubble(text, "you");
        
        const res = await fetch("/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        //input.value = "";
        const data = await res.json();

        
        appendBubble(data, "you");
        
        return;
    }

    // ⭐ Voice command
    //spaceParts = text.split(" ");
    const isVoiceCommand =
        spaceParts[0].toLowerCase() === "audio" &&
        spaceParts.length === 2;

    if (isVoiceCommand) {
        //appendBubble(text, "you");
        console.log("HERE! 8")
        const res = await fetch("/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        const data = await res.json();

        // ⭐ Always show audio result even if replyMode = OFF
        appendAudioBubble(data.reply.filename, data.reply.caption);

        //input.value = "";
        return;
    }

    if (text.toLowerCase().startsWith("say ") && AUDIO_GEN_SERVER_URL.length > 1) {
    //appendBubble(text, "you");
    console.log("HERE! 9")
    const res = await fetch("/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
    });

    const data = await res.json();

    // ⭐ Always show audio result even if replyMode = OFF
    appendAudioBubble(data.reply.filename, data.reply.caption);

    //input.value = "";
    return;
    }
    
    if (text.toLowerCase().startsWith("said ") && AUDIO_GEN_SERVER_URL.length > 1) {    
        console.log("HERE! 10")
        const res = await fetch("/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        const data = await res.json();

        // ⭐ Always show audio result for user (you)
        appendAudioBubble(data.reply.filename, data.reply.caption, 'you');
        
        //input.value = "";
        return;
    }
    // ⭐ Normal user bubble
    if (
        text.toLowerCase() !== "show" &&
        window.tts_mode_js !== "everybody_talking"
    ) {
        appendBubble(text, "you");
    }
        
    //input.value = "";
    if (
        window.tts_mode_js === "everybody_talking" ||
        window.tts_mode_js === "everybody_talking_with_text"
    ){
        text = "said " + text; //line 446
        console.log("all talk modes.");
        console.log(text)
    }

    if (text.toLowerCase().startsWith("said ") && AUDIO_GEN_SERVER_URL.length > 1) {    
        console.log("HERE! 10")
        const res = await fetch("/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        const data = await res.json();

        // ⭐ Always show audio result for user (you)
        appendAudioBubble(data.reply.filename, data.reply.caption, 'you');
        
        
        return;
    }    

    // ⭐ If reply mode OFF → stop here (commands already handled)
    if (!replyMode) {
        //console.log("Reply mode OFF — skipping AI reply.");
        
        const res = await fetch("/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        //console.log("In not reply mode")
        const data = await res.json();
        return;
    }

    // ⭐ AI reply
    showTyping();
    
    const res = await fetch("/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
    });

    const data = await res.json();
    //console.log("HERE!1234")
    //console.log(data)
    hideTyping();

    if (data.reply && data.reply.type === "image") {
        appendImageBubble(data.reply.filename, data.reply.caption);
    } else {
        //appendBubble(data.reply, "character");
        handleReply(data.reply);

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
