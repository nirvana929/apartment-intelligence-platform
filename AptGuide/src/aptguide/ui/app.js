const messagesContainer = document.getElementById("messages");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");

let sessionId = "demo-" + Date.now();

function addMessage(content, isUser = false, sources = []) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user" : "assistant"}`;

    let html = `<div class="message-content">${content}</div>`;

    if (sources.length > 0) {
        html += `<div class="source">来源：${sources.join(", ")}</div>`;
    }

    messageDiv.innerHTML = html;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // 添加用户消息
    addMessage(message, true);
    messageInput.value = "";

    // 禁用发送按钮
    sendButton.disabled = true;
    sendButton.textContent = "发送中...";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message,
            }),
        });

        const data = await response.json();

        // 添加助手回复
        addMessage(data.reply, false, data.sources);
    } catch (error) {
        addMessage("抱歉，发生了错误。请稍后重试。", false);
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "发送";
    }
}

// 事件监听
sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});
