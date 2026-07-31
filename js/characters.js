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


    // Update profile fields
    document.getElementById("profilePersona").value = persona;
    document.getElementById("profileMood").value = mood;
    document.getElementById("profileOutfit").value = outfit;
    document.getElementById("profileLocation").value = charLocation;
    document.getElementById("profileInventory").value = inventory.join(", ");

    await fetchHistory();
    setStatus("Online");
}
