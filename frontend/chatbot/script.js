const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("chat-input");
const sendButtonEl = document.getElementById("send-button");
const historyListEl = document.getElementById("history-list");
const newChatButtonEl = document.getElementById("new-chat-button");
const sidebarEl = document.getElementById("sidebar");
const sidebarToggleEl = document.getElementById("sidebar-toggle");

// Relative path on purpose — this page is served by the same FastAPI app
// it talks to, so it always hits the right host/port with no hardcoding
// (the replica project's bug this project is explicitly avoiding).
const CHAT_ENDPOINT = "/chat";

const ROUTE_LABELS = {
  FAST_QA_RESPONSE: null, // confident answer, no extra label needed
  CLARIFY: "Needs clarification",
  MARKDOWN_RAG: "No quick answer yet",
  BLOCKED: "Blocked",
};

const WELCOME_MESSAGE =
  "Hi! Ask me anything about the Prospect-to-Cash process — Prospects, Leads, " +
  "Opportunities, Quotations, Customer Orders, Credit, Shipments, Invoices, or Payments.";

const STORAGE_SESSIONS_KEY = "ptc_chat_sessions";
const STORAGE_ACTIVE_KEY = "ptc_active_session_id";
const MAX_SESSIONS = 50;

// ── Session storage (client-side only — no backend history yet) ──────

function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_SESSIONS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveSessions(sessions) {
  try {
    localStorage.setItem(STORAGE_SESSIONS_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS)));
  } catch {
    // storage full or unavailable — conversation still works, just won't persist
  }
}

function getActiveSessionId() {
  try {
    return localStorage.getItem(STORAGE_ACTIVE_KEY);
  } catch {
    return null;
  }
}

function setActiveSessionId(id) {
  try {
    localStorage.setItem(STORAGE_ACTIVE_KEY, id);
  } catch {
    // ignore
  }
}

function newSessionId() {
  return `session_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

function findSession(sessions, id) {
  return sessions.find((s) => s.id === id) || null;
}

// ── Rendering ──────────────────────────────────────────────────────

function renderMessages(session) {
  messagesEl.innerHTML = "";
  const messages = session && session.messages.length ? session.messages : [{ sender: "bot", text: WELCOME_MESSAGE }];
  for (const msg of messages) {
    renderMessage(msg.text, msg.sender, msg);
  }
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderMessage(text, sender, { route, source, score } = {}) {
  const row = document.createElement("div");
  row.className = `message ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble" + (route === "CLARIFY" ? " clarify" : "");
  bubble.textContent = text;

  const label = ROUTE_LABELS[route];
  if (sender === "bot" && (label || source)) {
    const meta = document.createElement("span");
    meta.className = "meta";
    const parts = [];
    if (label) parts.push(label);
    if (source) parts.push(`source: ${source}`);
    if (typeof score === "number") parts.push(`score: ${score.toFixed(2)}`);
    meta.textContent = parts.join(" · ");
    bubble.appendChild(meta);
  }

  row.appendChild(bubble);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderHistoryList(sessions, activeId) {
  historyListEl.innerHTML = "";

  if (sessions.length === 0) {
    const empty = document.createElement("div");
    empty.className = "history-empty";
    empty.textContent = "No conversations yet.";
    historyListEl.appendChild(empty);
    return;
  }

  for (const session of sessions) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "history-item" + (session.id === activeId ? " active" : "");
    item.textContent = session.title || "New chat";
    item.addEventListener("click", () => switchSession(session.id));
    historyListEl.appendChild(item);
  }
}

// ── Session actions ────────────────────────────────────────────────

let sessions = loadSessions();
let activeSessionId = getActiveSessionId();

function persistAndRender() {
  saveSessions(sessions);
  setActiveSessionId(activeSessionId);
  renderHistoryList(sessions, activeSessionId);
}

function createNewSession() {
  const session = { id: newSessionId(), title: "", createdAt: new Date().toISOString(), messages: [] };
  sessions.unshift(session);
  activeSessionId = session.id;
  persistAndRender();
  renderMessages(session);
  inputEl.focus();
}

function switchSession(id) {
  activeSessionId = id;
  persistAndRender();
  renderMessages(findSession(sessions, id));
}

function appendMessageToActiveSession(text, sender, meta = {}) {
  let session = findSession(sessions, activeSessionId);
  if (!session) {
    session = { id: newSessionId(), title: "", createdAt: new Date().toISOString(), messages: [] };
    sessions.unshift(session);
    activeSessionId = session.id;
  }
  session.messages.push({ sender, text, ...meta });
  if (!session.title && sender === "user") {
    session.title = text.length > 42 ? `${text.slice(0, 42)}…` : text;
  }
  persistAndRender();
}

// ── Init ───────────────────────────────────────────────────────────

if (!findSession(sessions, activeSessionId)) {
  activeSessionId = sessions.length > 0 ? sessions[0].id : null;
}
if (!activeSessionId) {
  createNewSession();
} else {
  persistAndRender();
  renderMessages(findSession(sessions, activeSessionId));
}

// ── Events ─────────────────────────────────────────────────────────

newChatButtonEl.addEventListener("click", createNewSession);

sidebarToggleEl.addEventListener("click", () => {
  sidebarEl.classList.toggle("collapsed");
});

async function sendQuery(query) {
  const response = await fetch(CHAT_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error(`Server returned ${response.status}`);
  }
  return response.json();
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = inputEl.value.trim();
  if (!query) return;

  renderMessage(query, "user");
  appendMessageToActiveSession(query, "user");
  inputEl.value = "";
  inputEl.disabled = true;
  sendButtonEl.disabled = true;

  try {
    const result = await sendQuery(query);
    const meta = { route: result.route, source: result.source, score: result.score };
    renderMessage(result.answer ?? "(no answer)", "bot", meta);
    appendMessageToActiveSession(result.answer ?? "(no answer)", "bot", meta);
  } catch (err) {
    const errorText = "Sorry, something went wrong reaching the server. Please try again.";
    renderMessage(errorText, "bot");
    appendMessageToActiveSession(errorText, "bot");
  } finally {
    inputEl.disabled = false;
    sendButtonEl.disabled = false;
    inputEl.focus();
  }
});
