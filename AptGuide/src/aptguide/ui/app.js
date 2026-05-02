const messagesContainer = document.getElementById("messages");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");

let sessionId = "demo-" + Date.now();

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function addMessage(content, isUser = false, sources = []) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user" : "assistant"}`;

    let html = `<div class="message-content">${escapeHtml(content)}</div>`;

    if (sources.length > 0) {
        html += `<div class="source">来源：${sources.map(escapeHtml).join(", ")}</div>`;
    }

    messageDiv.innerHTML = html;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function renderCards(cards) {
    let html = '<div class="cards-container">';
    for (const card of cards) {
        const tags = (card.tags || [])
            .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
            .join("");
        html += `
        <div class="room-card">
            <div class="room-card-header">
                <span class="room-title">${escapeHtml(card.title)}</span>
                <span class="room-rent">${escapeHtml(card.rent)}</span>
            </div>
            <div class="room-card-body">
                <span class="room-district">${escapeHtml(card.district)}</span>
                ${tags ? `<div class="room-tags">${tags}</div>` : ""}
                ${card.description ? `<p class="room-desc">${escapeHtml(card.description)}</p>` : ""}
            </div>
            <div class="room-card-actions">
                <button class="btn-appointment" data-room-id="${escapeHtml(card.id)}" data-room-title="${escapeHtml(card.title)}">预约看房</button>
            </div>
        </div>`;
    }
    html += "</div>";
    return html;
}

function addCards(cards, actions) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message assistant cards-message";
    messageDiv.innerHTML = renderCards(cards);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Bind appointment button clicks
    messageDiv.querySelectorAll(".btn-appointment").forEach((btn) => {
        btn.addEventListener("click", () => {
            const title = btn.getAttribute("data-room-title") || "房源";
            messageInput.value = `预约看房 ${title}`;
            messageInput.focus();
        });
    });
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

        // 如果有卡片数据，展示房间卡片
        if (data.cards && data.cards.length > 0) {
            addCards(data.cards, data.actions);
        }
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
