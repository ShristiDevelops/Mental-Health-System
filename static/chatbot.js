function sendMessage() {

    let inputBox = document.getElementById("userInput");
    let message = inputBox.value.trim();

    // ❌ Agar empty hai to send mat karo
    if (message === "") {
        return;
    }

    // ✅ Button disable (double click prevent)
    let sendBtn = document.querySelector("button");
    sendBtn.disabled = true;

    // User message show karo
    document.getElementById("chatbox").innerHTML +=
        "<p><b>You:</b> " + message + "</p>";

    // Input clear karo immediately
    inputBox.value = "";

    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {

        document.getElementById("chatbox").innerHTML +=
            "<p><b>Bot:</b> " + data.response + "</p>";

        // Scroll to bottom
        let chatbox = document.getElementById("chatbox");
        chatbox.scrollTop = chatbox.scrollHeight;

    })
    .catch(error => {
        console.log("Error:", error);
    })
    .finally(() => {
        // ✅ Re-enable button after response
        sendBtn.disabled = false;
    });
}