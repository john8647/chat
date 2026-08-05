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
window.addEventListener("DOMContentLoaded", () => {
    const defaultItem = document.querySelector('.character-item[data-name="Jimmy"]');
    if (defaultItem) {
        selectCharacter("Jimmy", defaultItem);
    }
});



function updateHeader() {
    document.getElementById("chatHeaderName").textContent = characterName;
    document.getElementById("chatHeaderAvatar").style.backgroundImage =
        `url('/images/${characterName.toLowerCase()}.png')`;
}

function setStatus(text) {
    document.getElementById("chatHeaderStatus").textContent = text;
}
