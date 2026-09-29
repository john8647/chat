

async function loadCharacters() {
    const characterList = document.querySelector(".character-list");

    if (!characterList) return;

    const response = await fetch("/characters.json");
    if (!response.ok) {
        throw new Error(`Unable to load characters: ${response.status}`);
    }

    const characters = await response.json();
    if (!Array.isArray(characters) || characters.length === 0) {
        throw new Error("characters.json must contain at least one character");
    }

    characterList.replaceChildren();

    characters.forEach((character, index) => {
        if (!character.name) return;

        const item = document.createElement("div");
        item.className = `character-item${index === 0 ? " active" : ""}`;
        item.dataset.name = character.name;
        item.addEventListener("click", () => selectCharacter(character.name, item));

        const avatar = document.createElement("div");
        avatar.className = "avatar";
        avatar.style.backgroundImage = `url("http://192.168.0.121:8000/images/${character.image || character.name}.png")`;
        avatar.style.backgroundSize = "cover";

        const name = document.createElement("div");
        name.className = "character-name";
        name.textContent = character.name;

        item.append(avatar, name);
        characterList.appendChild(item);
    });

    const firstItem = characterList.querySelector(".character-item");
    if (firstItem) {
        await selectCharacter(firstItem.dataset.name, firstItem);
    }
}

window.addEventListener("DOMContentLoaded", () => {
    loadCharacters().catch(error => {
        console.error(error);
        setStatus("Offline");
    });
});

async function selectCharacter(name, element) {
    if (!name) {
    name = "Jimmy";
    }
    characterName = name;
    updateHeader();


    // Sidebar highlight
    document.querySelectorAll(".character-item").forEach(item => {
        item.classList.remove("active");
    });
    if (element) element.classList.add("active");

    // Backend call
    const res = await fetch("/character/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name })
    });

    const data = await res.json();

    // Update global state
    persona = data.persona;
    mood = data.mood;
    outfit = data.outfit;
    charLocation = data.location;
    inventory = data.inventory;
    description = data.description;
    pose = data.pose;
    age = data.age;
    thinking_about = data.thinking_about;
    // Update profile fields
    let inv = [];

    if (Array.isArray(inventory)) {
        inv = inventory;
    } else if (typeof inventory === "string" && inventory.length > 0) {
        inv = inventory.split(",").map(x => x.trim());
    }

    document.getElementById("profilePersona").value = persona;
    document.getElementById("profileMood").value = mood;
    document.getElementById("profileOutfit").value = outfit;
    document.getElementById("profileLocation").value = charLocation;
    document.getElementById("profileInventory").value = inv.join(", ");
    document.getElementById("profileDescription").value = description;
    document.getElementById("profilePose").value = pose;
    document.getElementById("profileAge").value = age;
    document.getElementById("profileThinking_about").value = thinking_about;
    await fetchHistory();
    setStatus("Online");
}


async function refreshCharacter() {
    const res = await fetch("http://192.168.0.121:8000/refresh_character", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ character: characterName })
    });

    const data = await res.json();

    if (data.ok) {
        //console.log("Character refreshed:", data.character);

        // ⭐ Re‑load character data into the frontend
        await selectCharacter(characterName);

        //alert("Character profile reloaded.");
    } else {
        alert("Failed to refresh character.");
    }
}

