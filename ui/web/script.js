async function send() {
    let inputBox = document.getElementById("input");
    let chat = document.getElementById("chat");

    let text = inputBox.value.trim();
    if (!text) return;

    // show user message
    addMessage(text, "user");

    inputBox.value = "";

    try {
        let res = await fetch(
            "http://127.0.0.1:8000/ask?query=" + encodeURIComponent(text)
        );

        let data = await res.json();

        addMessage(data.response, "bot");

    } catch (error) {
        addMessage("Error connecting to Jarvis", "bot");
        console.error(error);
    }
}

function addMessage(text, type) {
    let chat = document.getElementById("chat");

    let msg = document.createElement("div");
    msg.classList.add("message", type);
    msg.innerText = text;

    chat.appendChild(msg);

    // auto scroll
    chat.scrollTop = chat.scrollHeight;
}