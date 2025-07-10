function updatePetStats(petData) {
    document.getElementById("pet-name").textContent = petData.name;
    document.getElementById("happiness").textContent = petData.happiness;
    document.getElementById("hunger").textContent = petData.hunger;
    document.getElementById("energy").textContent = petData.energy;
    document.getElementById("mood").textContent = petData.mood.mood;
}

function fetchPetData() {
    fetch("/pet/")
        .then(response => response.json())
        .then(data => updatePetStats(data))
        .catch(err => console.error("Pet Fetch Error:", err));
}

document.getElementById("feed-btn").addEventListener("click", () => {
    fetch("/pet/feed", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            updatePetStats(data.pet);
            animatePet("feed");
        });
});

document.getElementById("play-btn").addEventListener("click", () => {
    fetch("/pet/update?action=play", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            updatePetStats(data.pet);
            animatePet("play");
        });
});

document.addEventListener("DOMContentLoaded", fetchPetData);