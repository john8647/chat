function openProfile() {
    const panel = document.getElementById("profilePanel");
        // Update profile fields
    let inv = [];

    if (Array.isArray(inventory)) {
        inv = inventory;
    } else if (typeof inventory === "string" && inventory.length > 0) {
        inv = inventory.split(",").map(x => x.trim());
    }

    document.getElementById("profileName").textContent = characterName;
    document.getElementById("profilePersona").value = persona;
    document.getElementById("profileMood").value = mood;
    document.getElementById("profileOutfit").value = outfit;
    document.getElementById("profileLocation").value = charLocation;
    document.getElementById("profileInventory").value = inv.join(", ");
    document.getElementById("profileDescription").value = description;
    document.getElementById("profilePose").value = pose;
    document.getElementById("profileAge").value = age;
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
        inventory: document.getElementById("profileInventory").value,
        description: document.getElementById("profileDescription").value,
        pose: document.getElementById("profilePose").value,
        age: document.getElementById("profileAge").value
            .split(",")
            .map(s => s.trim())
    };

    

    // IMPORTANT: Python server is on port 8000
    const response = await fetch("http://192.168.0.121:8000/character/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated)
    });

    const result = await response.json();
    
    // Update globals
    persona = updated.persona;
    mood = updated.mood;
    outfit = updated.outfit;
    charLocation = updated.location;
    inventory = updated.inventory;
    description = updated.description;
    pose = updated.pose;
    age = updated.age;
    closeProfile();
}
