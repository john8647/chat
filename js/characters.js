async function selectCharacter(name, element) {
    characterName = name;
    updateHeader();
    if (!name) {
    name = "Jimmy";
    }


    // Sidebar highlight
    document.querySelectorAll(".character-item").forEach(item => {
        item.classList.remove("active");
    });
    element.classList.add("active");

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
    await fetchHistory();
    setStatus("Online");
}
