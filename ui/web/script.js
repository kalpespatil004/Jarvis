const form = document.getElementById("commandForm");
const inputBox = document.getElementById("input");
const chat = document.getElementById("chat");
const micButton = document.getElementById("micButton");
const sendButton = document.getElementById("sendButton");
const voiceToggle = document.getElementById("voiceToggle");
const inputStatus = document.getElementById("inputStatus");
const connectionStatus = document.getElementById("connectionStatus");
const modeLabel = document.getElementById("modeLabel");

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const API_URL = "http://127.0.0.1:8000/ask";
const API_TIMEOUT_MS = 15000;

let recognition = null;
let voiceOutputEnabled = true;
let isListening = false;
let isBusy = false;
let shouldSendVoiceResult = false;
let activeController = null;
let activeTimeoutId = null;
let latestRequestId = 0;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
        isListening = true;
        micButton.classList.add("listening");
        inputStatus.innerText = "Listening";
    };

    recognition.onresult = (event) => {
        let transcript = "";

        for (let index = event.resultIndex; index < event.results.length; index += 1) {
            transcript += event.results[index][0].transcript;
        }

        inputBox.value = transcript.trim();

        if (event.results[event.results.length - 1].isFinal) {
            shouldSendVoiceResult = true;
            recognition.stop();
        }
    };

    recognition.onerror = (event) => {
        shouldSendVoiceResult = false;
        isListening = false;
        micButton.classList.remove("listening");
        setBusy(false);

        const message = event.error === "not-allowed"
            ? "Microphone permission is blocked. Allow mic access in the browser and try again."
            : "Voice input stopped. Tap the mic and speak again.";
        addMessage(message, "system");
    };

    recognition.onend = () => {
        isListening = false;
        micButton.classList.remove("listening");

        if (shouldSendVoiceResult) {
            shouldSendVoiceResult = false;
            send();
            return;
        }

        if (!isBusy) {
            inputStatus.innerText = "Standby";
        }
    };
} else {
    micButton.disabled = true;
    micButton.title = "Voice input is not supported in this browser";
    inputStatus.innerText = "Text only";
    modeLabel.innerText = "Text only";
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    send();
});

inputBox.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        send();
    }
});

micButton.addEventListener("click", () => {
    if (!recognition) return;

    if (isListening) {
        recognition.stop();
        return;
    }

    recognition.start();
});

voiceToggle.addEventListener("click", () => {
    voiceOutputEnabled = !voiceOutputEnabled;

    voiceToggle.classList.toggle("active", voiceOutputEnabled);
    voiceToggle.setAttribute("aria-pressed", String(voiceOutputEnabled));
    voiceToggle.innerText = voiceOutputEnabled ? "Enabled" : "Muted";

    console.log(
        voiceOutputEnabled
            ? "Backend voice enabled"
            : "Backend voice muted"
    );
});

async function send() {
    const text = inputBox.value.trim();
    if (!text) return;

    if (isBusy) {
        cancelActiveRequest();
    }

    stopListening();

    addMessage(text, "user");
    inputBox.value = "";
    setBusy(true);

    const requestId = latestRequestId + 1;
    latestRequestId = requestId;
    activeController = new AbortController();
    activeTimeoutId = window.setTimeout(() => activeController.abort(), API_TIMEOUT_MS);

    try {
        const res = await fetch(`${API_URL}?query=${encodeURIComponent(text)}`, {
            signal: activeController.signal,
        });

        if (requestId !== latestRequestId) return;

        if (!res.ok) {
            throw new Error(`Jarvis returned ${res.status}`);
        }

        const data = await res.json();
        if (requestId !== latestRequestId) return;

        const reply = data.response || "I received an empty response.";

        connectionStatus.innerText = "Online";
        addMessage(reply, "bot");
        
    } catch (error) {
        if (requestId !== latestRequestId) return;

        connectionStatus.innerText = "Offline";
        const message = error.name === "AbortError"
            ? "Jarvis took too long to respond. The request was stopped so the console stays ready."
            : "Jarvis API is offline. Start the backend with: uvicorn api.main:app --reload";
        addMessage(message, "bot");
        console.error(error);
    } finally {
        if (requestId === latestRequestId) {
            clearActiveRequest();
            setBusy(false);
            inputBox.focus();
        }
    }
}

function addMessage(text, type) {
    const msg = document.createElement("article");
    const role = document.createElement("span");
    const body = document.createElement("p");

    msg.classList.add("message", type);
    role.classList.add("role");
    role.innerText = type === "user" ? "You" : type === "system" ? "System" : "Jarvis";
    body.innerText = text;

    msg.appendChild(role);
    msg.appendChild(body);
    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
}

function setBusy(busy) {
    isBusy = busy;
    sendButton.disabled = busy;
    sendButton.innerText = busy ? "Wait" : "Send";
    inputStatus.innerText = busy ? "Processing" : "Standby";
}

function stopListening() {
    shouldSendVoiceResult = false;

    if (recognition && isListening) {
        recognition.stop();
    }

    isListening = false;
    micButton.classList.remove("listening");
}

function cancelActiveRequest() {
    if (activeController) {
        activeController.abort();
    }

    clearActiveRequest();
}

function clearActiveRequest() {
    if (activeTimeoutId) {
        window.clearTimeout(activeTimeoutId);
    }

    activeController = null;
    activeTimeoutId = null;
}
