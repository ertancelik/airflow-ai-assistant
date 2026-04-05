(function() {
    const AGENT_URL = "http://localhost:8090/chat";

    const btn = document.createElement("button");
    btn.id = "airflow-chat-btn";
    btn.innerHTML = "🤖";
    btn.title = "Airflow AI Assistant";
    document.body.appendChild(btn);

    const box = document.createElement("div");
    box.id = "airflow-chat-box";
    box.innerHTML = `
        <div id="airflow-chat-header">🤖 Airflow AI Assistant</div>
        <div id="airflow-chat-messages"></div>
        <div id="airflow-chat-input-area">
            <input id="airflow-chat-input" type="text" placeholder="Ask me anything..." />
            <button id="airflow-chat-send">➤</button>
        </div>
    `;
    document.body.appendChild(box);

    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/chat_plugin/static/chat.css";
    document.head.appendChild(link);

    btn.addEventListener("click", () => {
        box.style.display = box.style.display === "flex" ? "none" : "flex";
    });

    function addMessage(text, role) {
        const msgs = document.getElementById("airflow-chat-messages");
        const div = document.createElement("div");
        div.className = role === "user" ? "chat-msg-user" : "chat-msg-bot";
        div.textContent = text;
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
    }

    async function sendMessage() {
        const input = document.getElementById("airflow-chat-input");
        const message = input.value.trim();
        if (!message) return;

        addMessage(message, "user");
        input.value = "";
        addMessage("Thinking...", "bot");

        try {
            const response = await fetch(AGENT_URL, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({message})
            });
            const data = await response.json();
            const msgs = document.getElementById("airflow-chat-messages");
            msgs.lastChild.textContent = data.response;
        } catch (e) {
            const msgs = document.getElementById("airflow-chat-messages");
            msgs.lastChild.textContent = "Error: Could not reach agent.";
        }
    }

    document.getElementById("airflow-chat-send").addEventListener("click", sendMessage);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && document.getElementById("airflow-chat-input") === document.activeElement) {
            sendMessage();
        }
    });
})();