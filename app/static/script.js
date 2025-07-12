console.log(SESSION_ID)
console.log(STICKY_STR)

let ws;
let reconnectDelay = 1000;

const theReadme = document.getElementById("link-to-md");
const responsesDiv = document.getElementById("responses");
const theForm = document.getElementById("the-form");
const toggleHttpsBtn = document.getElementById("toggle-https");
const toggleWssBtn = document.getElementById("toggle-wss");

let showHttps = true;
let showWss = true;
let messages = [];

// function displayMessages() {
//   responsesDiv.innerHTML = "";

//   messages.forEach(msg => {
//     if ((msg.type === "https" && showHttps) || (msg.type === "wss" && showWss)) {
//       const div = document.createElement("div");
//       div.className = "response";

//       const label = document.createElement("span");
//       label.textContent = msg.type;
//       label.className = `response-label ${msg.type}`;

//       const text = document.createTextNode(msg.text);

//       div.appendChild(label);
//       div.appendChild(text);
//       responsesDiv.appendChild(div);
//     }
//   });
// }


function addMessage(type, text) {
  const div = document.createElement("div");
  div.className = "response";

  const labelNode = document.createElement("span");
  labelNode.textContent = type;
  labelNode.className = `response-label ${type}`;

  const textNode = document.createTextNode(text);

  div.appendChild(labelNode);
  div.appendChild(textNode);

  responsesDiv.appendChild(div);
  responsesDiv.scrollTop = responsesDiv.scrollHeight;

  // messages.push({ type, text });

  // if (messages.length > 100) {
  //   messages.shift();
  // }

  // displayMessages();
}

// README.md
theReadme.addEventListener("click", async () => {
  window.open("/readme", "_blank");
})

// --- Form Handlers ---
function wsSend(input, text) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ text, op: 'echo' }));
  } else {
    console.error("WebSocket not connected.");
  }

  input.value = "";
}

theForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  document.cookie = "StickyStr=;";
  const input = document.getElementById("the-input");
  const text = input.value.trim();
  if (!text) return;

  const clickedButton = e.submitter?.value;

  let theUrl;

  if (clickedButton === "ws-only") {
    wsSend(input, text); return;
  }

  if (clickedButton === "http-only") {
    theUrl = "submit/" + SESSION_ID;
  } else if (clickedButton === "http-sticky") {
    document.cookie = `StickyStr=${STICKY_STR};`
    theUrl = "submit/" + SESSION_ID;
  } else if (clickedButton === "with-redis") {
    theUrl = "with-redis/" + SESSION_ID;
  } else if (clickedButton === "not-sticky") {
    theUrl = "without-redis/" + SESSION_ID;
  } else if (clickedButton === "sticky") {
    document.cookie = `StickyStr=${STICKY_STR};`
    theUrl = "without-redis/" + SESSION_ID;
  }

  try {
    const response = await fetch(theUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, op: 'echo' })
    });

    const result = await response.json();
    addMessage("https", result.text);
    document.cookie = "StickyStr=;";
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
    document.cookie = "StickyStr=;";
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
