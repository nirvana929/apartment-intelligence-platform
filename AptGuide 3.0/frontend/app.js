const { createApp, ref, nextTick, onMounted } = Vue;

createApp({
  setup() {
    const messages = ref([]);
    const input = ref("");
    const loading = ref(false);
    const chatContainer = ref(null);
    const inputEl = ref(null);

    function getSessionId() {
      let sid = localStorage.getItem("aptguide_session_id");
      if (!sid) {
        sid = crypto.randomUUID();
        localStorage.setItem("aptguide_session_id", sid);
      }
      return sid;
    }

    function scrollToBottom() {
      nextTick(() => {
        const el = chatContainer.value;
        if (el) el.scrollTop = el.scrollHeight;
      });
    }

    function formatText(text) {
      if (!text) return "";
      return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");
    }

    async function sendMessage() {
      const text = input.value.trim();
      if (!text || loading.value) return;

      const sessionId = getSessionId();

      messages.value.push({ role: "user", text });
      input.value = "";
      loading.value = true;
      scrollToBottom();

      try {
        const resp = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, session_id: sessionId }),
        });

        if (!resp.ok) {
          throw new Error(`HTTP ${resp.status}`);
        }

        const data = await resp.json();

        messages.value.push({
          role: "assistant",
          text: data.message || "",
          cards: data.cards || [],
        });
      } catch (err) {
        messages.value.push({
          role: "assistant",
          text: `抱歉，请求失败：${err.message}`,
        });
      } finally {
        loading.value = false;
        scrollToBottom();
        if (inputEl.value) inputEl.value.focus();
      }
    }

    onMounted(() => {
      if (inputEl.value) inputEl.value.focus();
    });

    return {
      messages,
      input,
      loading,
      chatContainer,
      inputEl,
      sendMessage,
      formatText,
    };
  },
}).mount("#app");
