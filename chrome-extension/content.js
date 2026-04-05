(function() {
    if (document.getElementById("airflow-chat-btn")) return;

    const AGENT_URL = "http://localhost:8090/chat";

    // CSS inject
    const style = document.createElement("style");
    style.textContent = `
        #airflow-chat-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: #017CEE;
            color: white;
            border: none;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 9999;
        }
        #airflow-chat-box {
            position: fixed;
            bottom: 100px;
            right: 30px;
            width: 350px;
            height: 450px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            display: none;
            flex-direction: column;
            z-index: 9999;
            font-family: Arial, sans-serif;
        }
        #airflow-chat-header {
            background: #017CEE;
            color: white;
            padding: 14px 16px;
            border-radius: 12px 12px 0 0;
            font-weight: bold;
            font-size: 14px;
        }
        #airflow-chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .chat-msg-user {
            background: #017CEE;
            color: white;
            padding: 8px 12px;
            border-radius: 12px 12px 0 12px;
            align-self: flex-end;
            max-width: 80%;
            font-size: 13px;
        }
        .chat-msg-bot {
            background: #f0f0f0;
            color: #333;
            padding: 8px 12px;
            border-radius: 12px 12px 12px 0;
            align-self: flex-start;
            max-width: 80%;
            font-size: 13px;
            white-space: pre-wrap;
        }
        #airflow-chat-input-area {
            display: flex;
            padding: 10px;
            border-top: 1px solid #eee;
            gap: 8px;
        }
        #airflow-chat-input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 20px;
            font-size: 13px;
            outline: none;
        }
        #airflow-chat-send {
            background: #017CEE;
            color: white;
            border: none;
            border-radius: 50%;
            width: 34px;
            height: 34px;
            cursor: pointer;
            font-size: 16px;
        }
    `;
    document.head.appendChild(style);

    // Chat butonu
    const btn = document.createElement("button");
    btn.id = "airflow-chat-btn";
    btn.innerHTML = "🤖";
    btn.title = "Airflow AI Assistant";
    document.body.appendChild(btn);

    // Chat kutusu
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
            document.getElementById("airflow-chat-messages").lastChild.textContent = data.response;
        } catch(e) {
            document.getElementById("airflow-chat-messages").lastChild.textContent = "Error: Could not reach agent.";
        }
    }

    document.getElementById("airflow-chat-send").addEventListener("click", sendMessage);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && document.getElementById("airflow-chat-input") === document.activeElement) {
            sendMessage();
        }
    });
})();