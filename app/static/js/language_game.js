let recorder;
let audioChunks = [];

function startLanguageGame() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            recorder = new MediaRecorder(stream);
            recorder.ondataavailable = e => audioChunks.push(e.data);
            recorder.onstop = sendAudio;
            audioChunks = [];
            recorder.start();
            document.getElementById("record-btn").textContent = "Stop Recording";
        })
        .catch(err => console.error("Audio Error:", err));
}

function stopRecording() {
    if (recorder && recorder.state !== "inactive") {
        recorder.stop();
        recorder.stream.getTracks().forEach(track => track.stop());
        document.getElementById("record-btn").textContent = "Record";
    }
}

function sendAudio() {
    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.wav");

    fetch("/games/language/play", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => alert("You said: " + data.recognized_text))
    .catch(err => console.error("Upload Error:", err));
}

document.getElementById("record-btn").addEventListener("click", () => {
    if (recorder && recorder.state === "recording") {
        stopRecording();
    } else {
        startLanguageGame();
    }
});