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
let TEST_MODE = true;
let replyMode = true;
const modal = document.getElementById("global-options-modal");
const btn = document.getElementById("global-options-btn");
const closeBtn = document.getElementById("close-options");



window.addEventListener("DOMContentLoaded", () => {
    const defaultItem = document.querySelector('.character-item[data-name="Jimmy"]');
    if (defaultItem) {
        selectCharacter("Jimmy", defaultItem);
    }
});




function updateHeader() {
    document.getElementById("chatHeaderName").textContent = characterName;
    document.getElementById("chatHeaderAvatar").style.backgroundImage =
        `url('http://localhost:8000/images/${characterName.toLowerCase()}.png')`;
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

    await fetch("http://localhost:8000/reply_mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: replyMode })
    });

    // 1. Send server URL
    await fetch("http://localhost:8000/update_server_url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ server_url: serverUrl })
    });

    // 2. Send image URL
    await fetch("http://localhost:8000/update_image_url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: imageUrl })
    });

    // ⭐ 3. Only ping if at least one URL is non-empty
    let pingResult = { ok: true };

    if (serverUrl !== "" || imageUrl !== "") {
        const ping = await fetch("http://localhost:8000/ping_server");
        pingResult = await ping.json();
    }

    //console.log("Ping:", pingResult);

    // ⭐ 4. Close modal if:
    //    - both URLs are empty (test mode)
    //    - OR ping succeeded
    if ((serverUrl === "" && imageUrl === "") || pingResult.ok) {
        document.getElementById("global-options-modal").classList.add("hidden");
        return;
    }

    // ⭐ 5. Only show error if ping failed AND user entered something
    alert("Saved, but ping failed: " + pingResult.error);
};


document.getElementById("reply_mode").addEventListener("change", (e) => {
    replyMode = e.target.checked;
    console.log("Reply mode:", replyMode);
});



document.getElementById("server-url-input").addEventListener("change", (e) => {
    SERVER_URL = normalizeUrl(e.target.value);
    evaluateTestMode();
});

document.getElementById("image-url-input").addEventListener("change", (e) => {
    IMAGE_GEN_SERVER_URL = normalizeUrl(e.target.value);
    evaluateTestMode();
});


fetch("http://localhost:8000/update_image_url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_url: IMAGE_GEN_SERVER_URL })
});



fetch("http://localhost:8000/update_server_url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ server_url: SERVER_URL })
});



//fetch("http://localhost:8000/ping_server")
//    .then(r => r.json())
//   .then(data => console.log("Ping:", data));

