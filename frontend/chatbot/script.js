const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("chat-input");
const sendButtonEl = document.getElementById("send-button");
const historyListEl = document.getElementById("history-list");
const newChatButtonEl = document.getElementById("new-chat-button");
const sidebarEl = document.getElementById("sidebar");
const sidebarToggleEl = document.getElementById("sidebar-toggle");
const contextToggleEl = document.getElementById("context-toggle");
const contextPanelEl = document.getElementById("context-panel");
const contextSummaryEl = document.getElementById("context-summary");
const ctxGroupEl = document.getElementById("ctx-group");
const ctxSiteEl = document.getElementById("ctx-site");
const ctxModuleEl = document.getElementById("ctx-module");
const ctxFormEl = document.getElementById("ctx-form");

// Relative path on purpose — this page is served by the same FastAPI app
// it talks to, so it always hits the right host/port with no hardcoding
// (the replica project's bug this project is explicitly avoiding).
const CHAT_ENDPOINT = "/chat";

const ROUTE_LABELS = {
  FAST_QA_RESPONSE: null, // confident quick answer, no extra label needed
  CLARIFY: "Needs clarification",
  MARKDOWN_RAG_RESPONSE: "From document search",
  NO_ANSWER: "No information found",
  BLOCKED: "Blocked",
};

const WELCOME_MESSAGE =
  "Hi! Ask me anything about the Prospect-to-Cash process — Prospects, Leads, " +
  "Opportunities, Quotations, Customer Orders, Credit, Shipments, Invoices, or Payments.";

const STORAGE_SESSIONS_KEY = "ptc_chat_sessions";
const STORAGE_ACTIVE_KEY = "ptc_active_session_id";
const STORAGE_CONTEXT_KEY = "ptc_simulated_context";
const MAX_SESSIONS = 50;

// ── Context Simulator (mock only — stands in for a real SyteLine screen) ──

function loadSimulatedContext() {
  try {
    const raw = localStorage.getItem(STORAGE_CONTEXT_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveSimulatedContext(context) {
  try {
    localStorage.setItem(STORAGE_CONTEXT_KEY, JSON.stringify(context));
  } catch {
    // ignore — falls back to defaults next load
  }
}

function readContextFromInputs() {
  return {
    simulated_group: ctxGroupEl.value,
    site: ctxSiteEl.value.trim() || null,
    module: ctxModuleEl.value.trim() || null,
    form: ctxFormEl.value.trim() || null,
  };
}

function applyContextToInputs(context) {
  ctxGroupEl.value = context.simulated_group || "SALES_REP";
  ctxSiteEl.value = context.site || "";
  ctxModuleEl.value = context.module || "";
  ctxFormEl.value = context.form || "";
}

function updateContextSummary() {
  const context = readContextFromInputs();
  const location = [context.site, context.module].filter(Boolean).join(" / ");
  contextSummaryEl.textContent = location ? `${context.simulated_group} · ${location}` : context.simulated_group;
}

function onContextChange() {
  const context = readContextFromInputs();
  saveSimulatedContext(context);
  updateContextSummary();
}

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

function renderMessage(text, sender, { route, source, sources, score } = {}) {
  const row = document.createElement("div");
  row.className = `message ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble" + (route === "CLARIFY" ? " clarify" : "");
  bubble.textContent = text;

  const label = ROUTE_LABELS[route];
  const citation = source || (sources && sources.length ? sources.join("; ") : null);
  if (sender === "bot" && (label || citation)) {
    const meta = document.createElement("span");
    meta.className = "meta";
    const parts = [];
    if (label) parts.push(label);
    if (citation) parts.push(`source: ${citation}`);
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

applyContextToInputs(loadSimulatedContext());
updateContextSummary();

// ── Events ─────────────────────────────────────────────────────────

newChatButtonEl.addEventListener("click", createNewSession);

sidebarToggleEl.addEventListener("click", () => {
  sidebarEl.classList.toggle("collapsed");
});

contextToggleEl.addEventListener("click", () => {
  contextPanelEl.classList.toggle("collapsed");
});

for (const el of [ctxGroupEl, ctxSiteEl, ctxModuleEl, ctxFormEl]) {
  el.addEventListener("change", onContextChange);
  el.addEventListener("input", onContextChange);
}

async function sendQuery(query) {
  const context = readContextFromInputs();
  const response = await fetch(CHAT_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      simulated_group: context.simulated_group,
      context: { site: context.site, module: context.module, form: context.form },
    }),
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
    const meta = { route: result.route, source: result.source, sources: result.sources, score: result.score };
    const text =
      result.answer ??
      (result.route === "BLOCKED"
        ? `Access denied for this request (reason: ${result.reason || "not permitted"}). Try a different simulated group in the context panel.`
        : "(no answer)");
    renderMessage(text, "bot", meta);
    appendMessageToActiveSession(text, "bot", meta);
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
