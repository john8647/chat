function openProfile() {
    const panel = document.getElementById("profilePanel");

    document.getElementById("profileName").textContent = characterName;
    document.getElementById("profilePersona").value = persona;
    document.getElementById("profileMood").value = mood;
    document.getElementById("profileOutfit").value = outfit;
    document.getElementById("profileLocation").value = charLocation;
    document.getElementById("profileInventory").value = inventory.join(", ");

    panel.style.display = "block";
}

function closeProfile() {
    document.getElementById("profilePanel").style.display = "none";
}


async function saveProfile() {
    const updated = {
        persona: document.getElementById("profilePersona").value,
        mood: document.getElementById("profileMood").value,
        outfit: document.getElementById("profileOutfit").value,
        location: document.getElementById("profileLocation").value,
        inventory: document.getElementById("profileInventory").value
            .split(",")
            .map(s => s.trim())
    };

    console.log("[PROFILE] Sending update:", updated);

    // IMPORTANT: Python server is on port 8000
    const response = await fetch("http://localhost:8000/character/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated)
    });

    const result = await response.json();
    console.log("[PROFILE] Update response:", result);

    // Update globals
    persona = updated.persona;
    mood = updated.mood;
    outfit = updated.outfit;
    charLocation = updated.location;
    inventory = updated.inventory;

    closeProfile();
}
