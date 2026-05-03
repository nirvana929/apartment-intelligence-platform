const messagesContainer = document.getElementById("messages");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const chatContainer = document.getElementById("chatContainer");

let sessionId = "demo-" + Date.now();
let welcomeHidden = false;

// ========== 工具函数 ==========

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    });
}

function hideWelcome() {
    if (welcomeHidden) return;
    welcomeHidden = true;
    const welcome = document.querySelector(".welcome-section");
    if (welcome) {
        welcome.style.transition = "opacity 0.3s, max-height 0.3s";
        welcome.style.opacity = "0";
        welcome.style.maxHeight = "0";
        welcome.style.overflow = "hidden";
        welcome.style.padding = "0";
        setTimeout(() => welcome.remove(), 300);
    }
}

// ========== 消息渲染 ==========

function addMessage(content, isUser = false, sources = []) {
    hideWelcome();

    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user" : "assistant"}`;

    let html = `<div class="message-content">${escapeHtml(content)}</div>`;

    if (sources.length > 0) {
        html += `<div class="source">来源：${sources.map(escapeHtml).join(", ")}</div>`;
    }

    messageDiv.innerHTML = html;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// ========== 加载动画 ==========

function addLoadingIndicator() {
    const div = document.createElement("div");
    div.id = "loadingIndicator";
    div.className = "message assistant";
    div.innerHTML = `
        <div class="message-content loading-msg">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>`;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

function removeLoadingIndicator() {
    const el = document.getElementById("loadingIndicator");
    if (el) el.remove();
}

// ========== 房源卡片 ==========

function renderRoomCards(cards) {
    let html = '<div class="cards-container">';
    for (const card of cards) {
        const tags = (card.tags || [])
            .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
            .join("");
        html += `
        <div class="room-card">
            <div class="room-card-header">
                <span class="room-title">${escapeHtml(card.title)}</span>
                <span class="room-rent">&yen;${escapeHtml(card.rent)}/月</span>
            </div>
            <div class="room-card-body">
                <span class="room-district">${escapeHtml(card.district)}</span>
                ${tags ? `<div class="room-tags">${tags}</div>` : ""}
                ${card.description ? `<p class="room-desc">${escapeHtml(card.description)}</p>` : ""}
            </div>
            <div class="room-card-actions">
                <button class="btn-appointment" data-room-id="${escapeHtml(card.room_id || card.id)}" data-room-title="${escapeHtml(card.title)}">预约看房</button>
            </div>
        </div>`;
    }
    html += "</div>";
    return html;
}

// ========== 预约卡片 ==========

function renderAppointmentCards(cards) {
    const statusMap = { pending: "待确认", confirmed: "已确认", cancelled: "已取消" };
    let html = '<div class="cards-container">';
    for (const card of cards) {
        const statusText = statusMap[card.status] || card.status;
        const statusClass = card.status === "confirmed" ? "status-confirmed" : "status-pending";
        html += `
        <div class="info-card appointment-card">
            <div class="info-card-header">
                <span class="info-card-icon">&#128197;</span>
                <span class="info-card-title">${escapeHtml(card.room_title)}</span>
                <span class="info-status ${statusClass}">${escapeHtml(statusText)}</span>
            </div>
            <div class="info-card-body">
                <div class="info-row"><span class="info-label">预约时间</span><span class="info-value">${escapeHtml(card.appointment_time)}</span></div>
                <div class="info-row"><span class="info-label">预约编号</span><span class="info-value">${escapeHtml(card.appointment_id)}</span></div>
                ${card.created_at ? `<div class="info-row"><span class="info-label">创建时间</span><span class="info-value">${escapeHtml(card.created_at)}</span></div>` : ""}
            </div>
        </div>`;
    }
    html += "</div>";
    return html;
}

// ========== 租约卡片 ==========

function renderLeaseCards(cards) {
    let html = '<div class="cards-container">';
    for (const card of cards) {
        const isActive = card.status === "active";
        const statusText = isActive ? "生效中" : card.status;
        const statusClass = isActive ? "status-active" : "status-inactive";
        html += `
        <div class="info-card lease-card">
            <div class="info-card-header">
                <span class="info-card-icon">&#128203;</span>
                <span class="info-card-title">${escapeHtml(card.room_title)}</span>
                <span class="info-status ${statusClass}">${escapeHtml(statusText)}</span>
            </div>
            <div class="info-card-body">
                <div class="info-row"><span class="info-label">月租金</span><span class="info-value rent-value">&yen;${escapeHtml(card.rent)}</span></div>
                <div class="info-row"><span class="info-label">起始日期</span><span class="info-value">${escapeHtml(card.start_date)}</span></div>
                <div class="info-row"><span class="info-label">到期日期</span><span class="info-value">${escapeHtml(card.end_date)}</span></div>
                <div class="info-row"><span class="info-label">合同编号</span><span class="info-value">${escapeHtml(card.lease_id)}</span></div>
            </div>
        </div>`;
    }
    html += "</div>";
    return html;
}

// ========== 卡片分发 ==========

function addCards(cards) {
    if (!cards || cards.length === 0) return;

    const messageDiv = document.createElement("div");
    messageDiv.className = "message assistant cards-message";

    const firstType = cards[0].type;
    if (firstType === "appointment") {
        messageDiv.innerHTML = renderAppointmentCards(cards);
    } else if (firstType === "lease") {
        messageDiv.innerHTML = renderLeaseCards(cards);
    } else {
        messageDiv.innerHTML = renderRoomCards(cards);
    }

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    // 绑定预约按钮
    messageDiv.querySelectorAll(".btn-appointment").forEach((btn) => {
        btn.addEventListener("click", () => {
            const roomId = btn.getAttribute("data-room-id");
            const roomTitle = btn.getAttribute("data-room-title");
            openTimePicker(roomId, roomTitle);
        });
    });
}

// ========== 确认卡片 ==========

function addConfirmation(confirmation) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message assistant";

    const summary = escapeHtml(confirmation.summary || "");
    messageDiv.innerHTML = `
        <div class="confirmation-container">
            <div class="confirmation-summary">${summary}</div>
            <div class="confirmation-actions">
                <button class="btn-confirm">确认</button>
                <button class="btn-cancel">取消</button>
            </div>
        </div>
    `;

    messageDiv.querySelector(".btn-confirm").addEventListener("click", () => {
        messageInput.value = "确认";
        sendMessage();
    });

    messageDiv.querySelector(".btn-cancel").addEventListener("click", () => {
        messageInput.value = "取消";
        sendMessage();
    });

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// ========== 时间选择弹窗 ==========

let pendingRoomId = null;
let pendingRoomTitle = null;

function openTimePicker(roomId, roomTitle) {
    pendingRoomId = roomId;
    pendingRoomTitle = roomTitle;
    document.getElementById("modalRoomTitle").textContent = roomTitle;

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById("appointmentDate").value = tomorrow.toISOString().split("T")[0];

    document.getElementById("timePickerModal").style.display = "flex";
}

function closeTimePicker() {
    document.getElementById("timePickerModal").style.display = "none";
    pendingRoomId = null;
    pendingRoomTitle = null;
}

document.getElementById("modalConfirm").addEventListener("click", () => {
    const date = document.getElementById("appointmentDate").value;
    const time = document.getElementById("appointmentTime").value;
    if (!date) { alert("请选择日期"); return; }
    const msg = `预约看房 ${pendingRoomTitle}，房间号${pendingRoomId}，时间${date} ${time}`;
    closeTimePicker();
    messageInput.value = msg;
    sendMessage();
});

document.getElementById("modalCancel").addEventListener("click", closeTimePicker);
document.getElementById("timePickerModal").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeTimePicker();
});

// ========== 快捷操作 ==========

function bindQuickActions(container) {
    container.querySelectorAll(".quick-btn, .welcome-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            messageInput.value = btn.getAttribute("data-message");
            sendMessage();
        });
    });
}

bindQuickActions(document);

// ========== 发送消息 ==========

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    addMessage(message, true);
    messageInput.value = "";

    sendButton.disabled = true;
    addLoadingIndicator();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, message }),
        });

        const data = await response.json();
        removeLoadingIndicator();

        addMessage(data.reply, false, data.sources);

        if (data.cards && data.cards.length > 0) {
            addCards(data.cards);
        }

        if (data.pending_confirmation) {
            addConfirmation(data.pending_confirmation);
        }
    } catch (error) {
        removeLoadingIndicator();
        addMessage("抱歉，发生了错误。请稍后重试。", false);
    } finally {
        sendButton.disabled = false;
    }
}

sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});
