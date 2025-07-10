function initDashboard() {
    fetch("/education/lessons")
        .then(response => response.json())
        .then(data => {
            const lessonList = document.getElementById("lesson-list");
            if (lessonList) {
                lessonList.innerHTML = data.lessons.map(l => `
                    <li>${l.title} - ${l.subject}</li>
                `).join("");
            }
        })
        .catch(err => console.error("Fetch Error:", err));
}

function showNotification(message) {
    const notification = document.createElement("div");
    notification.className = "notification";
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

document.addEventListener("DOMContentLoaded", () => {
    initDashboard();
    document.querySelectorAll("button[data-action]").forEach(btn => {
        btn.addEventListener("click", () => {
            const action = btn.dataset.action;
            if (action === "feed-pet") {
                fetch("/pet/feed", { method: "POST" })
                    .then(response => response.json())
                    .then(data => {
                        showNotification(data.message);
                        animatePet("feed");
                    });
            }
        });
    });
});