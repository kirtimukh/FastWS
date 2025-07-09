console.log(SESSION_ID)
const apiUrl = "http://localhost:8000/submit/" + SESSION_ID;
const wsUrl = "ws://localhost:8000/ws/" + SESSION_ID;
const h2wUrl = "http://localhost:8000/http-to-ws/" + SESSION_ID;

let ws;
let reconnectDelay = 1000;

const responsesDiv = document.getElementById("responses");
const httpsForm = document.getElementById("https-form");
const wsForm = document.getElementById("ws-form");
const h2wForm = document.getElementById("h2w-form");
const toggleHttpsBtn = document.getElementById("toggle-https");
const toggleWssBtn = document.getElementById("toggle-wss");

let showHttps = true;
let showWss = true;
let messages = [];

function displayMessages() {
  responsesDiv.innerHTML = "";

  messages.forEach(msg => {
    if ((msg.type === "https" && showHttps) || (msg.type === "wss" && showWss)) {
      const div = document.createElement("div");
      div.className = "response";
      div.textContent = `${msg.type}: ${msg.text}`;
      responsesDiv.appendChild(div);
    }
  });
}

function addMessage(type, text) {
  messages.push({ type, text });

  if (messages.length > 100) {
    messages.shift();
  }

  displayMessages();
}

// --- Form Handlers ---

httpsForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("https-input");
  const text = input.value.trim();
  if (!text) return;

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, op: 'echo' })
    });

    const result = await response.json();
    addMessage("https", result.text);
  } catch (err) {
    console.error("HTTP error:", err);
  }

  input.value = "";
});

h2wForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("h2w-input");
  const text = input.value.trim();
  if (!text) return;

  try {
    const response = await fetch(h2wUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, op: 'echo' })
    });

    const result = await response.json();
    addMessage("https", result.text);
  } catch (err) {
    console.error("HTTP error:", err);
  }

  input.value = "";
});

wsForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const input = document.getElementById("ws-input");
  const text = input.value.trim();
  if (!text) return;

  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ text, op: 'echo' }));
  } else {
    console.error("WebSocket not connected.");
  }

  input.value = "";
});

// --- Filtering ---

toggleHttpsBtn.addEventListener("click", () => {
  showHttps = !showHttps;
  toggleHttpsBtn.style.opacity = showHttps ? "1" : "0.5";
  displayMessages();
});

toggleWssBtn.addEventListener("click", () => {
  showWss = !showWss;
  toggleWssBtn.style.opacity = showWss ? "1" : "0.5";
  displayMessages();
});

// --- WebSocket Reconnection Logic ---

function connectWebSocket() {
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log("WebSocket connected");
    reconnectDelay = 1000; // reset delay
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data?.text) {
      addMessage("wss", data.text);
    }
  };

  ws.onclose = () => {
    console.warn("WebSocket closed. Reconnecting...");
    setTimeout(connectWebSocket, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 30000); // exponential backoff
  };

  ws.onerror = (err) => {
    console.error("WebSocket error:", err);
    ws.close(); // trigger reconnect
  };
}

connectWebSocket();
