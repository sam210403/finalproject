document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");
    const chatInput = document.getElementById("chat-input");

    function appendMessage(sender, message) {
        let msgDiv = document.createElement("div");
        msgDiv.classList.add(sender);
        msgDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function getBotResponse(userInput) {
        userInput = userInput.toLowerCase();
        if (userInput.includes("hello") || userInput.includes("hi")) {
            return "Hello! How can I assist you today?";
        } else if (userInput.includes("order")) {
            return "You can view your orders in the 'Cart' section.";
        } else if (userInput.includes("recommend")) {
            return "I can recommend products based on your location. Visit the 'Recommended' page.";
        } else if (userInput.includes("thanks") || userInput.includes("thank you")) {
            return "You're welcome! Let me know if you need anything else.";
        } else {
            return "I'm not sure about that. Can you ask something else?";
        }
    }

    function sendMessage() {
        let userMessage = chatInput.value.trim();
        if (userMessage === "") return;

        appendMessage("You", userMessage);
        setTimeout(() => {
            let botReply = getBotResponse(userMessage);
            appendMessage("Bot", botReply);
        }, 500);

        chatInput.value = "";
    }

    document.querySelector("button").addEventListener("click", sendMessage);

    chatInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            sendMessage();
        }
    });
});
