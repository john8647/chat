// Global state
let characterName = "Jimmy";
let persona = "";
let mood = "";
let outfit = "";
let charLocation = "";
let inventory = [];
let description = ""
let pose = ""
let age = ""
let SERVER_URL = "";
let IMAGE_GEN_SERVER_URL = "";
let AUDIO_GEN_SERVER_URL = "";
let TEST_MODE = true;
let replyMode = true;
const modal = document.getElementById("global-options-modal");
const btn = document.getElementById("global-options-btn");
const closeBtn = document.getElementById("close-options");



function updateHeader() {
    document.getElementById("chatHeaderName").textContent = characterName;
    document.getElementById("chatHeaderAvatar").style.backgroundImage =
        `url('http://192.168.0.121:8000/images/${characterName.toLowerCase()}.png')`;
}

function setStatus(text) {
    document.getElementById("chatHeaderStatus").textContent = text;
}

function openGlobalOptions() {
    document.getElementById("global-options-modal").classList.remove("hidden");
}

function closeGlobalOptions() {
    document.getElementById("global-options-modal").classList.add("hidden");
}




function normalizeUrl(url) {
    if (!url) return "";
    if (!url.includes(":443")) {
        url = url.replace(/\/$/, "");
        url += ":443/api/v1/generate";
    }
    return url;
}

function isValidCloudflareUrl(url) {
    return url.startsWith("https://") && url.includes(".trycloudflare.com");
}

function evaluateTestMode() {
    TEST_MODE = !(isValidCloudflareUrl(SERVER_URL) || isValidCloudflareUrl(IMAGE_GEN_SERVER_URL));
}

document.getElementById("save-options-btn").onclick = async () => {
    const serverUrl = document.getElementById("server-url-input").value.trim();
    const imageUrl = document.getElementById("image-url-input").value.trim();
    const audioUrl = document.getElementById("audio-url-input").value.trim();
    const tts_mode = document.getElementById('tts-mode').value;
    // 1. Update reply mode
    await fetch("http://192.168.0.121:8000/reply_mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: replyMode })
    });

    // 2. Update server URL (may be empty)
    await fetch("http://192.168.0.121:8000/update_server_url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ server_url: serverUrl })
    });

    // 3. Update image URL (may be empty)
    await fetch("http://192.168.0.121:8000/update_image_url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: imageUrl })
    });

    // 4. Update audio URL (may be empty)
    await fetch("http://192.168.0.121:8000/update_audio_url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio_url: audioUrl })
    });

    // 5. Update the TTS mode in game.
    await fetch("http://192.168.0.121:8000/update_tts_mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_tts_mode: tts_mode })
    });
    
    // 6. Close modal immediately — no ping tests
    document.getElementById("global-options-modal").classList.add("hidden");
};


document.getElementById("reply_mode").addEventListener("change", (e) => {
    replyMode = e.target.checked;
    console.log("Reply mode:", replyMode);
});



document.getElementById("server-url-input").addEventListener("change", (e) => {
    SERVER_URL = normalizeUrl(e.target.value);
    //evaluateTestMode();
});

document.getElementById("image-url-input").addEventListener("change", (e) => {
    IMAGE_GEN_SERVER_URL = normalizeUrl(e.target.value);
    //evaluateTestMode();
});

document.getElementById("audio-url-input").addEventListener("change", (e) => {
    AUDIO_GEN_SERVER_URL = normalizeUrl(e.target.value);
    //evaluateTestMode();
});

fetch("http://192.168.0.121:8000/update_image_url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_url: IMAGE_GEN_SERVER_URL })
});



fetch("http://192.168.0.121:8000/update_server_url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ server_url: SERVER_URL })
});

