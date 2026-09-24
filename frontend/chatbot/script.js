const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("chat-input");
const sendButtonEl = document.getElementById("send-button");
const historyListEl = document.getElementById("history-list");
const newChatButtonEl = document.getElementById("new-chat-button");
const clearHistoryButtonEl = document.getElementById("clear-history-button");
const sidebarEl = document.getElementById("sidebar");
const sidebarToggleEl = document.getElementById("sidebar-toggle");
const sidebarOverlayEl = document.getElementById("sidebar-overlay");
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

// route -> { cls: which color the badge/left-border uses, label: shown text }
const ROUTE_STYLES = {
  FAST_QA_RESPONSE: { cls: "route-success", label: "Quick answer" },
  CLARIFY: { cls: "route-warning", label: "Needs clarification" },
  MARKDOWN_RAG_RESPONSE: { cls: "route-info", label: "From documents" },
  NO_ANSWER: { cls: "route-neutral", label: "No match found" },
  BLOCKED: { cls: "route-danger", label: "Access blocked" },
  OUT_OF_SCOPE: { cls: "route-neutral", label: "Out of scope" },
  DIRECT_RESPONSE: { cls: "route-success", label: "Direct response" },
  CAPABILITY_PENDING: { cls: "route-warning", label: "Planned route" },
};

const WELCOME_MESSAGE =
  "Ask me anything about the Prospect-to-Cash process — Prospects, Leads, Opportunities, " +
  "Quotations, Customer Orders, Credit, Shipments, Invoices, or Payments.";

const QUICK_PROMPTS = [
  "What is a Customer Order?",
  "Explain customer credit limits",
  "How does shipment processing work?",
  "Explain the invoice lifecycle",
];

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
    if (id) localStorage.setItem(STORAGE_ACTIVE_KEY, id);
    else localStorage.removeItem(STORAGE_ACTIVE_KEY);
  } catch {
    // ignore
  }
}

function newSessionId() {
  return `session_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

function newMessageId() {
  return `msg_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

function findSession(sessions, id) {
  return sessions.find((s) => s.id === id) || null;
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

// ── Rendering ──────────────────────────────────────────────────────

function renderWelcome() {
  const wrap = document.createElement("div");
  wrap.className = "welcome";
  wrap.innerHTML = `
    <div class="welcome-icon">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
        <path d="M8 10h8M8 14h5M21 12a9 9 0 10-4.2 7.6L21 21l-1.2-3.9A8.96 8.96 0 0021 12z"
              stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <h2>How can I help today?</h2>
    <p></p>
    <div class="quick-prompts" aria-label="Suggested questions"></div>
  `;
  wrap.querySelector("p").textContent = WELCOME_MESSAGE;

  const prompts = wrap.querySelector(".quick-prompts");
  for (const prompt of QUICK_PROMPTS) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "quick-prompt";
    button.textContent = prompt;
    button.addEventListener("click", () => {
      inputEl.value = prompt;
      inputEl.focus();
    });
    prompts.appendChild(button);
  }
  messagesEl.appendChild(wrap);
}

function renderMessages(session) {
  messagesEl.innerHTML = "";
  const messages = session ? session.messages : [];
  if (messages.length === 0) {
    renderWelcome();
  } else {
    for (const msg of messages) {
      renderMessage(msg.text, msg.sender, msg);
    }
  }
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

const THUMB_UP_PATH =
  "M7 11v9H4a1 1 0 01-1-1v-7a1 1 0 011-1h3zm0 0l4.5-7.5a1.5 1.5 0 012.6 1.5L13 9h5.2a2 2 0 " +
  "011.98 2.29l-1 7A2 2 0 0117.2 20H10a3 3 0 01-3-3v-6z";

function buildRatingGroup(sessionIdAtRender, messageId, currentRating) {
  const group = document.createElement("div");
  group.className = "message-rating";

  const upBtn = document.createElement("button");
  upBtn.type = "button";
  upBtn.className = "rating-button up" + (currentRating === "up" ? " active" : "");
  upBtn.setAttribute("aria-label", "Mark this answer helpful");
  upBtn.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none"><path d="${THUMB_UP_PATH}" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>`;

  const downBtn = document.createElement("button");
  downBtn.type = "button";
  downBtn.className = "rating-button down" + (currentRating === "down" ? " active" : "");
  downBtn.setAttribute("aria-label", "Mark this answer not helpful");
  downBtn.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" style="transform: rotate(180deg)"><path d="${THUMB_UP_PATH}" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>`;

  upBtn.addEventListener("click", () => {
    const newRating = setMessageRating(sessionIdAtRender, messageId, "up");
    upBtn.classList.toggle("active", newRating === "up");
    downBtn.classList.remove("active");
  });
  downBtn.addEventListener("click", () => {
    const newRating = setMessageRating(sessionIdAtRender, messageId, "down");
    downBtn.classList.toggle("active", newRating === "down");
    upBtn.classList.remove("active");
  });

  group.appendChild(upBtn);
  group.appendChild(downBtn);
  return group;
}

function renderMessage(text, sender, { route, source, sources, score, timestamp, decisionTrace, id, rating, sessionId } = {}) {
  const row = document.createElement("div");
  row.className = `message ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = sender === "user" ? "Y" : "AI";
  avatar.setAttribute("aria-hidden", "true");

  const column = document.createElement("div");
  column.className = "bubble-column";

  const style = ROUTE_STYLES[route];

  const bubble = document.createElement("div");
  bubble.className = "bubble" + (style ? ` ${style.cls}` : "");
  bubble.textContent = text;
  column.appendChild(bubble);

  const citation = source || (sources && sources.length ? sources.join("; ") : null);
  const hasFooter = sender === "bot" && (style || citation || timestamp || decisionTrace || id);
  if (hasFooter) {
    const footer = document.createElement("div");
    footer.className = "message-footer";

    if (style) {
      const tag = document.createElement("span");
      tag.className = `route-tag ${style.cls}`;
      tag.textContent = style.label;
      footer.appendChild(tag);
    }
    if (timestamp) {
      const time = document.createElement("span");
      time.className = "message-time";
      time.textContent = formatTime(timestamp);
      footer.appendChild(time);
    }
    if (decisionTrace?.intent || decisionTrace?.selected_route) {
      const decision = document.createElement("span");
      decision.className = "decision-note";
      decision.textContent = [decisionTrace.intent, decisionTrace.selected_route].filter(Boolean).join(" → ");
      footer.appendChild(decision);
    }
    if (id) {
      footer.appendChild(buildRatingGroup(sessionId || activeSessionId, id, rating));
    }
    column.appendChild(footer);

    if (citation) {
      const src = document.createElement("div");
      src.className = "source-note";
      src.textContent = `Source: ${citation}${typeof score === "number" ? ` · score ${score.toFixed(2)}` : ""}`;
      column.appendChild(src);
    }
  } else if (sender === "user" && timestamp) {
    const footer = document.createElement("div");
    footer.className = "message-footer";
    const time = document.createElement("span");
    time.className = "message-time";
    time.textContent = formatTime(timestamp);
    footer.appendChild(time);
    column.appendChild(footer);
  }

  row.appendChild(avatar);
  row.appendChild(column);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

let typingRow = null;

function showTyping() {
  typingRow = document.createElement("div");
  typingRow.className = "message bot";
  typingRow.innerHTML = `
    <div class="avatar" aria-hidden="true">AI</div>
    <div class="bubble-column">
      <div class="bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>
    </div>
  `;
  messagesEl.appendChild(typingRow);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideTyping() {
  if (typingRow) {
    typingRow.remove();
    typingRow = null;
  }
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
    const item = document.createElement("div");
    item.className = "history-item" + (session.id === activeId ? " active" : "");

    const title = document.createElement("button");
    title.type = "button";
    title.className = "history-item-title";
    title.textContent = session.title || "New chat";
    title.addEventListener("click", () => switchSession(session.id));

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "history-item-delete";
    deleteBtn.setAttribute("aria-label", "Delete this conversation");
    deleteBtn.innerHTML =
      '<svg viewBox="0 0 24 24" width="14" height="14" fill="none">' +
      '<path d="M4 7h16M9 7V5a1 1 0 011-1h4a1 1 0 011 1v2m-8 0v12a1 1 0 001 1h6a1 1 0 001-1V7" ' +
      'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    deleteBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteSession(session.id);
    });

    item.appendChild(title);
    item.appendChild(deleteBtn);
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
  closeSidebarOnMobile();
  inputEl.focus();
}

function switchSession(id) {
  activeSessionId = id;
  persistAndRender();
  renderMessages(findSession(sessions, id));
  closeSidebarOnMobile();
}

function deleteSession(id) {
  const session = findSession(sessions, id);
  const label = session && session.title ? `"${session.title}"` : "this conversation";
  if (!window.confirm(`Delete ${label}? This can't be undone.`)) return;

  sessions = sessions.filter((s) => s.id !== id);

  if (activeSessionId === id) {
    if (sessions.length > 0) {
      activeSessionId = sessions[0].id;
      persistAndRender();
      renderMessages(sessions[0]);
    } else {
      activeSessionId = null;
      persistAndRender();
      createNewSession();
      return;
    }
  } else {
    persistAndRender();
  }
}

function clearAllHistory() {
  if (sessions.length === 0) return;
  if (!window.confirm("Delete all conversations? This can't be undone.")) return;
  sessions = [];
  activeSessionId = null;
  persistAndRender();
  createNewSession();
}

function setMessageRating(sessionId, messageId, value) {
  const session = findSession(sessions, sessionId);
  if (!session) return null;
  const message = session.messages.find((m) => m.id === messageId);
  if (!message) return null;
  message.rating = message.rating === value ? null : value; // click the active one again to unset
  saveSessions(sessions);
  return message.rating;
}

function appendMessageToActiveSession(text, sender, meta = {}) {
  let session = findSession(sessions, activeSessionId);
  if (!session) {
    session = { id: newSessionId(), title: "", createdAt: new Date().toISOString(), messages: [] };
    sessions.unshift(session);
    activeSessionId = session.id;
  }
  session.messages.push({ id: newMessageId(), timestamp: new Date().toISOString(), ...meta, sender, text });
  if (!session.title && sender === "user") {
    session.title = text.length > 42 ? `${text.slice(0, 42)}…` : text;
  }
  persistAndRender();
}

// ── Sidebar open/close (mobile uses an overlay + auto-close on navigate) ──

function closeSidebarOnMobile() {
  if (window.matchMedia("(max-width: 960px)").matches) {
    sidebarEl.classList.add("collapsed");
  }
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

if (window.matchMedia("(max-width: 960px)").matches) {
  sidebarEl.classList.add("collapsed");
}

applyContextToInputs(loadSimulatedContext());
updateContextSummary();

// ── Events ─────────────────────────────────────────────────────────

newChatButtonEl.addEventListener("click", createNewSession);
clearHistoryButtonEl.addEventListener("click", clearAllHistory);

sidebarToggleEl.addEventListener("click", () => {
  sidebarEl.classList.toggle("collapsed");
});

sidebarOverlayEl.addEventListener("click", () => {
  sidebarEl.classList.add("collapsed");
});

contextToggleEl.addEventListener("click", () => {
  contextPanelEl.classList.toggle("collapsed");
  contextToggleEl.setAttribute("aria-expanded", String(!contextPanelEl.classList.contains("collapsed")));
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

  renderMessage(query, "user", { timestamp: new Date().toISOString() });
  appendMessageToActiveSession(query, "user");
  inputEl.value = "";
  inputEl.disabled = true;
  sendButtonEl.disabled = true;
  showTyping();

  try {
    const result = await sendQuery(query);
    const meta = {
      id: newMessageId(),
      sessionId: activeSessionId,
      route: result.route,
      source: result.source,
      sources: result.sources,
      score: result.score,
      decisionTrace: result.decision_trace,
      timestamp: new Date().toISOString(),
    };
    const text =
      result.answer ??
      (result.route === "BLOCKED"
        ? `Access denied for this request (reason: ${result.reason || "not permitted"}). Try a different simulated group in the context panel.`
        : "(no answer)");
    hideTyping();
    renderMessage(text, "bot", meta);
    appendMessageToActiveSession(text, "bot", meta);
  } catch (err) {
    console.error("Chat request failed", err);
    hideTyping();
    const errorText = "Sorry, something went wrong reaching the server. Please try again.";
    renderMessage(errorText, "bot");
    appendMessageToActiveSession(errorText, "bot");
  } finally {
    inputEl.disabled = false;
    sendButtonEl.disabled = false;
    inputEl.focus();
  }
});
