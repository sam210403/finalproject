document.addEventListener("DOMContentLoaded", function () {
    updateCartCount();
});

// 🛒 Add to Cart Function (With Dynamic Update)
// 🛒 Add to Cart Function (No Location)
function addToCart(productId) {
    fetch(`/add_to_cart/${productId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        updateCartCount();  // ✅ Refresh cart count
    })
    .catch(error => console.error("Error:", error));
}

// 🔄 Update Cart Count (Live)
function updateCartCount() {
    fetch("/cart_count")
        .then(response => response.json())
        .then(data => {
            const cartCountElement = document.getElementById("cart-count");
            if (cartCountElement) {
                cartCountElement.innerText = data.count;
            }
        })
        .catch(error => console.error("Error:", error));
}

// ✅ Run cart count update on page load
document.addEventListener("DOMContentLoaded", updateCartCount);

// 🛎️ Toast Notification Function
function showToast(message) {
    let toast = document.createElement("div");
    toast.className = "toast-message";
    toast.innerText = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// 🤖 Chatbot Function (With Typing Indicator)
document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatBox = document.getElementById("chat-box");

    if (chatForm && chatInput && chatBox) {
        chatForm.addEventListener("submit", function (e) {
            e.preventDefault();
            let userMessage = chatInput.value.trim();
            if (!userMessage) return;

            appendMessage("You", userMessage);
            chatInput.value = "";

            // Show typing indicator
            let typingIndicator = appendMessage("Bot", "Typing...");
            
            fetch("/chatbot", {
                method: "POST",
                body: new URLSearchParams({ user_input: userMessage }),
                headers: { "Content-Type": "application/x-www-form-urlencoded" }
            })
            .then(response => response.text())
            .then(data => {
                typingIndicator.remove(); // Remove typing indicator
                appendMessage("Bot", data);
            })
            .catch(error => {
                typingIndicator.remove();
                console.error("Error:", error);
                appendMessage("Bot", "⚠️ Sorry, something went wrong.");
            });

        });
    }
    function sendMessage() {
        let userInput = document.getElementById("user-input").value;
        let chatbox = document.getElementById("chatbox");
    
        if (userInput.trim() === "") return;
    
        chatbox.innerHTML += `<div class="user-message">${userInput}</div>`;
        document.getElementById("user-input").value = "";
    
        fetch("/chatbot", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: userInput })
        })
        .then(response => response.json())
        .then(data => {
            chatbox.innerHTML += `<div class="bot-message">${data.response}</div>`;
            chatbox.scrollTop = chatbox.scrollHeight;
        })
        .catch(error => console.error("Error:", error));
    }
    
    // 📩 Append messages to chatbox
    function appendMessage(sender, message) {
        let msgElement = document.createElement("p");
        msgElement.innerHTML = `<b>${sender}:</b> ${message}`;
        chatBox.appendChild(msgElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll
        return msgElement;
    }
    document.addEventListener("DOMContentLoaded", function () {
        // 🎉 Show an alert when the page loads
        alert("Your order has been placed successfully! 🎉");
    
        // 🎯 Auto-redirect to the home page after a delay
        setTimeout(function () {
            window.location.href = "/"; // Redirect to home page after 5 seconds
        }, 5000);
    });
    
});
