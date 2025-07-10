console.log(SESSION_ID)

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
    const response = await fetch("submit/" + SESSION_ID, {
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

h2wForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("h2w-input");
  const text = input.value.trim();
  if (!text) return;

  const clickedButton = e.submitter?.value;

  let h2wUrl;

  if (clickedButton === "without-redis") {
    h2wUrl = "without-redis/" + SESSION_ID;
  } else {
    h2wUrl = "with-redis/" + SESSION_ID;
  }

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
  ws = new WebSocket("ws/" + SESSION_ID);

  ws.onopen = () => {
    console.log("WebSocket connected");
    reconnectDelay = 1000; // reset delay
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data?.text) {
      addMessage("wss", data.text);
    } else if (data?.websocket_pid) {
      const pid = data.websocket_pid;

      const span = document.getElementById("ws-pid");

      if (pid) {
        span.textContent = "Ws connection pid: " + pid;
        span.style.display = "inline";  // or "block" depending on layout
      } else {
        span.style.display = "none";
      }
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
