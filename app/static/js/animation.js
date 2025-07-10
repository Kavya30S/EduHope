function bounceElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add("bounce");
        setTimeout(() => element.classList.remove("bounce"), 1000);
    }
}

function fadeIn(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.opacity = 0;
        element.style.display = "block";
        let opacity = 0;
        const interval = setInterval(() => {
            opacity += 0.1;
            element.style.opacity = opacity;
            if (opacity >= 1) clearInterval(interval);
        }, 50);
    }
}

function initAnimations() {
    document.querySelectorAll(".animate-on-load").forEach(el => {
        el.style.opacity = 0;
        fadeIn(el.id);
    });
}

document.addEventListener("DOMContentLoaded", initAnimations);

function animatePet(action) {
    const pet = document.getElementById("pet-image");
    if (!pet) return;

    if (action === "feed") {
        pet.style.transform = "scale(1.1)";
        setTimeout(() => pet.style.transform = "scale(1)", 300);
    } else if (action === "play") {
        bounceElement("pet-image");
    }
}