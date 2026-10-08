// Support console. Reads /api/admin/overview (+ /health, /audit) and lets a SUPPORT_ADMIN handle
// tickets, unanswered questions and disliked answers. Every piece of user text is set with
// textContent — never innerHTML — so nothing a user typed can run in the admin's browser.

const groupEl = document.getElementById("group");
const daysEl = document.getElementById("days");
const refreshEl = document.getElementById("refresh");
const exportEl = document.getElementById("export");
const messageEl = document.getElementById("message");
const consoleEl = document.getElementById("console");
const showDoneEls = document.querySelectorAll(".show-done");

// Plain words for every internal code the server returns.
const REVIEW_TEXT = { content_gap: "📝 Needs a document", reviewed: "✓ Done", dismissed: "Ignored" };
const OUTCOME_TEXT = {
  FAST_QA_RESPONSE: "Approved answer", MARKDOWN_RAG_RESPONSE: "Answered from documents",
  NO_ANSWER: "Not found in documents", CLARIFY: "Asked to clarify", DIRECT_RESPONSE: "Small talk",
  OUT_OF_SCOPE: "Off-topic", CAPABILITY_PENDING: "Needs live SyteLine data", BLOCKED: "Blocked",
};
const CHECK_TEXT = {
  passed: "Matched the documents", repaired: "Corrected (a claim was removed)", replaced: "Refused (couldn't confirm)",
  not_found: "Not in the documents", unverified: "Not checked (checker unavailable)",
  none: "Not needed (fixed or approved text)", approved: "Approved answer",
};
const MOOD_TEXT = {
  F0_NORMAL: "Calm", F1_CONFUSED: "Confused", F2_COMPLAINT: "Complaining", F3_FRUSTRATED: "Frustrated",
  F4_PERSISTENT: "Asked again (problem came back)", none: "Small talk / not rated",
};
const TRIGGER_TEXT = {
  frustration: "The user was frustrated", persistent: "The same problem came back",
  unresolved: "The assistant couldn't answer twice", user_request: "The user asked for a person",
  user_confirmed: "The user raised it",
};
const TICKET_STATUS = {
  open: { text: "● Open", kind: "info" },
  in_progress: { text: "In progress", kind: "warning" },
  resolved: { text: "✓ Resolved", kind: "good" },
  closed: { text: "Closed", kind: "" },
};
const MAIL_TEXT = {
  sent: { text: "📧 Emailed", kind: "" },
  failed: { text: "⛔ Email failed", kind: "critical" },
  not_configured: { text: "Not emailed (mail not set up)", kind: "warning" },
  logged: { text: "Not emailed (mail off)", kind: "" },
};
const STATUS_TEXT = {
  SUCCESS: { text: "Answered", kind: "good" }, NO_ANSWER: { text: "Not answered", kind: "warning" },
  CLARIFY: { text: "Asked to clarify", kind: "" }, OUT_OF_SCOPE: { text: "Off-topic", kind: "" },
  NOT_AVAILABLE: { text: "Needs live data", kind: "" }, BLOCKED: { text: "Blocked", kind: "critical" },
  ERROR: { text: "Error", kind: "critical" },
};
const EVENT_TEXT = {
  chat: "Question", rating: "Rated an answer", ticket_created: "Created a ticket", ticket_status: "Changed a ticket",
  feedback_review: "Reviewed feedback", admin_access: "Opened the console", chat_deleted: "Deleted a chat",
  chat_deleted_all: "Deleted all chats", retention_purge: "Removed old records",
};

const state = { data: null, health: null, ticketFilter: "active" };

// ── Helpers ──────────────────────────────────────────────────────────

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function badge(text, kind = "") {
  return el("span", `badge ${kind}`.trim(), text);
}

function button(label, onClick, className = "") {
  const node = el("button", className, label);
  node.type = "button";
  node.addEventListener("click", onClick);
  return node;
}

function formatTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function plural(n, word) {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

function query(extra = {}) {
  return new URLSearchParams({ simulated_group: groupEl.value, ...extra }).toString();
}

function showMessage(text, isError = false) {
  messageEl.hidden = !text;
  messageEl.textContent = text || "";
  messageEl.classList.toggle("error", isError);
}

function emptyState(text) {
  return el("div", "empty", text);
}

async function send(method, path, body) {
  const response = await fetch(`${path}?${query()}`, {
    method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Server returned ${response.status}`);
  return response.json();
}

function stat(label, value, detail) {
  const node = el("div", "stat");
  node.append(el("div", "label", label), el("div", "value", value ?? "—"));
  if (detail) node.append(el("div", "detail", detail));
  return node;
}

function setCount(id, value, alert = false) {
  const node = document.getElementById(id);
  node.textContent = value ? String(value) : "";
  node.classList.toggle("alert", Boolean(value) && alert);
}

function where(item) {
  return [item.site, item.module, item.form].filter(Boolean).join(" / ");
}

// ── Navigation ───────────────────────────────────────────────────────

function openView(name) {
  document.querySelectorAll(".nav-item").forEach((item) => {
    const active = item.dataset.view === name;
    item.classList.toggle("active", active);
    if (active) item.setAttribute("aria-current", "page"); else item.removeAttribute("aria-current");
  });
  document.querySelectorAll(".view").forEach((view) => { view.hidden = view.id !== `view-${name}`; });
  if (name === "audit" && !document.getElementById("audit-results").childElementCount) searchAudit();
  window.scrollTo({ top: 0 });
}

document.querySelectorAll(".nav-item").forEach((item) => item.addEventListener("click", () => openView(item.dataset.view)));

// ── Home ─────────────────────────────────────────────────────────────

function activeTickets() {
  return (state.data?.tickets || []).filter((t) => t.status === "open" || t.status === "in_progress");
}

function pendingGaps() {
  return (state.data?.content_gaps || []).filter((g) => !g.review_status);
}

function renderHome() {
  const s = state.data.summary;
  const tickets = activeTickets();
  document.getElementById("home-stats").replaceChildren(
    stat("Questions asked", s.answers - s.blocked, `in ${plural(s.conversations, "chat")}`),
    stat("Answered", s.answered_pct === null ? "—" : `${s.answered_pct}%`, `${s.answered} answered from the documents`),
    stat("Rated helpful", s.satisfaction_pct === null ? "—" : `${s.satisfaction_pct}%`, `👍 ${s.thumbs_up}  ·  👎 ${s.thumbs_down}`),
    stat("Open tickets", tickets.length, tickets.length ? `${tickets.filter((t) => t.priority === "high").length} high priority` : "none waiting"),
  );

  const todo = [];
  const add = (icon, title, note, view, kind = "") => todo.push({ icon, title, note, view, kind });
  if (tickets.length) {
    const high = tickets.filter((t) => t.priority === "high").length;
    add("🎫", `${plural(tickets.length, "ticket")} waiting for support`,
      high ? `${high} high priority — contact these users first` : "Contact the users and update each ticket", "tickets");
  }
  const gaps = pendingGaps();
  if (gaps.length) {
    add("❓", `${plural(gaps.length, "topic")} users couldn't get answered`,
      "Decide which need a new document from the data team", "gaps");
  }
  if (s.open_downvotes) add("👎", `${plural(s.open_downvotes, "disliked answer")} to check`, "Read the answer and fix the document if it is wrong", "disliked");
  if (s.security.alerts) add("🛡️", `${plural(s.security.alerts, "security alert")}`, "Someone was blocked several times in a short time", "security");
  const openAlerts = state.health?.open_alerts?.length || 0;
  if (openAlerts) add("📈", `${plural(openAlerts, "system alert")}`, state.health.open_alerts.map((a) => a.message).join(" · "), "health");
  const mail = state.data.mail;
  if (mail && (!mail.enabled || mail.missing.length)) {
    add("📧", "Ticket email is not set up", "Tickets are saved here but nobody is emailed", "health");
  }

  const list = document.getElementById("home-todo");
  if (!todo.length) {
    list.replaceChildren(el("div", "all-clear", "✓ Nothing needs your attention right now."));
    return;
  }
  list.replaceChildren(...todo.map((t) => {
    const row = el("div", "todo");
    const text = el("div", "todo-text");
    text.append(el("div", "todo-title", t.title), el("div", "todo-note", t.note));
    row.append(el("span", "todo-icon", t.icon), text, button("Open", () => openView(t.view)));
    return row;
  }));
}

// ── Tickets ──────────────────────────────────────────────────────────

const TICKET_ACTIONS = {
  open: [["▶ Start working", "in_progress", "primary"], ["✓ Mark resolved", "resolved", ""]],
  in_progress: [["✓ Mark resolved", "resolved", "primary"], ["↩ Back to open", "open", ""]],
  resolved: [["Close ticket", "closed", ""], ["↺ Reopen", "open", ""]],
  closed: [["↺ Reopen", "open", ""]],
};

function ticketMatchesFilter(ticket) {
  if (state.ticketFilter === "all") return true;
  if (state.ticketFilter === "active") return ticket.status === "open" || ticket.status === "in_progress";
  return ticket.status === state.ticketFilter;
}

function ticketCard(ticket) {
  const item = el("article", `item ticket-card${ticket.priority === "high" ? " high" : ""}`);
  const top = el("div", "item-top");
  const heading = el("div");
  heading.append(el("div", "item-ref", `${ticket.ticket_ref} · ${formatTime(ticket.created_at)}`),
    el("div", "item-title", ticket.issue_summary));
  const badges = el("div", "badges");
  if (ticket.priority === "high") badges.append(badge("▲ High priority", "critical"));
  const status = TICKET_STATUS[ticket.status] || TICKET_STATUS.open;
  badges.append(badge(status.text, status.kind));
  top.append(heading, badges);
  item.append(top);

  const meta = el("div", "meta");
  meta.append(el("span", "", `👤 ${ticket.user_display_name || ticket.user_id}`));
  if (where(ticket)) meta.append(el("span", "", `🖥️ ${where(ticket)}`));
  const record = [ticket.record_type, ticket.record_id].filter(Boolean).join(" ");
  if (record) meta.append(el("span", "", `📄 ${record}`));
  const mail = MAIL_TEXT[ticket.notification_status];
  if (mail) meta.append(el("span", mail.kind ? `badge ${mail.kind}` : "", mail.text));
  item.append(meta);
  if (ticket.user_note) {
    const note = el("div", "ticket-message");
    note.append(el("span", "section-label", "USER'S NOTE"), el("p", "note", ticket.user_note));
    item.append(note);
  }

  const more = el("details");
  more.append(el("summary", "", "Show the conversation and details"));
  const fields = el("dl", "fields");
  const field = (term, value) => { if (value) fields.append(el("dt", "", term), el("dd", "", value)); };
  field("Why it was raised", TRIGGER_TEXT[ticket.trigger] || ticket.trigger);
  field("User's mood", MOOD_TEXT[ticket.mood] || ticket.mood);
  field("User id", ticket.user_id);
  more.append(fields);
  const turns = ticket.conversation_summary || [];
  if (turns.length) {
    more.append(el("h4", "", "Conversation before the ticket"));
    const list = el("ol", "turns");
    turns.forEach((turn) => {
      const li = el("li");
      li.append(el("div", "turn-q", turn.question), badge(OUTCOME_TEXT[turn.outcome] || turn.outcome || ""));
      if (turn.answer) li.append(el("div", "turn-a", turn.answer));
      list.append(li);
    });
    more.append(list);
  }
  item.append(more);

  const actions = el("div", "actions ticket-footer");
  const saved = el("span", "muted");
  const buttons = (TICKET_ACTIONS[ticket.status] || []).map(([label, next, cls]) => button(label, async () => {
    buttons.forEach((b) => (b.disabled = true));
    saved.textContent = "Saving…";
    try {
      await send("PUT", `/api/admin/tickets/${ticket.ticket_id}`, { status: next });
      ticket.status = next;
      renderTickets();
      renderHome();
    } catch (err) {
      console.error(err);
      saved.textContent = "Couldn’t save — try again.";
      buttons.forEach((b) => (b.disabled = false));
    }
  }, cls));
  actions.append(...buttons, saved);
  item.append(actions);
  return item;
}

function renderTickets() {
  const tickets = state.data.tickets;
  setCount("nav-tickets", activeTickets().length);
  const shown = tickets.filter(ticketMatchesFilter);
  const list = document.getElementById("ticket-list");
  if (!shown.length) {
    list.replaceChildren(emptyState(state.ticketFilter === "active" ? "No tickets waiting. 🎉" : "No tickets here."));
    return;
  }
  list.replaceChildren(...shown.map(ticketCard));
}

document.querySelectorAll("#ticket-filter .chip").forEach((chip) => chip.addEventListener("click", () => {
  state.ticketFilter = chip.dataset.status;
  document.querySelectorAll("#ticket-filter .chip").forEach((c) => c.classList.toggle("active", c === chip));
  renderTickets();
}));

// ── Unanswered questions and disliked answers ────────────────────────

function reviewActions(messageIds, current, onSaved) {
  const actions = el("div", "actions");
  const status = el("span", "muted");
  const choices = [["📝 Needs a document", "content_gap", "primary"], ["✓ Done", "reviewed", ""], ["Ignore", "dismissed", ""]];
  if (current) choices.push(["↩ Undo", null, ""]);
  const buttons = choices.map(([label, value, cls]) => button(label, async () => {
    buttons.forEach((b) => (b.disabled = true));
    status.textContent = "Saving…";
    try {
      for (const id of messageIds) await send("PUT", `/api/admin/feedback/${id}`, { status: value });
      onSaved(value);
    } catch (err) {
      console.error(err);
      status.textContent = "Couldn’t save — try again.";
      buttons.forEach((b) => (b.disabled = false));
    }
  }, cls));
  actions.append(...buttons, status);
  return actions;
}

function reviewBadge(status) {
  return status ? badge(REVIEW_TEXT[status], status === "content_gap" ? "info" : "good") : null;
}

function renderGaps() {
  const gaps = state.data.content_gaps;
  setCount("nav-gaps", pendingGaps().length);
  const list = document.getElementById("gap-list");
  if (!gaps.length) {
    list.replaceChildren(emptyState("Every question in this period was answered. 🎉"));
    return;
  }
  list.replaceChildren(...gaps.map((gap) => {
    const item = el("article", "item");
    const top = el("div", "item-top");
    top.append(el("div", "item-title", gap.topic));
    const review = reviewBadge(gap.review_status);
    if (review) top.append(review);
    item.append(top);
    const meta = el("div", "meta");
    const askedBy = gap.users?.length ? gap.users.join(", ") : plural(gap.user_count, "person").replace("persons", "people");
    meta.append(el("span", "", `Asked ${plural(gap.count, "time")}`), el("span", "", `👤 ${askedBy}`),
      el("span", "", `last on ${formatTime(gap.last_asked)}`));
    item.append(meta);
    if (gap.last_answer) {
      item.append(el("div", "muted", "What the assistant replied:"), el("p", "quote", gap.last_answer));
    }
    if (gap.examples.length > 1) {
      item.append(el("div", "muted", "How people asked it:"));
      const examples = el("ul", "examples");
      gap.examples.forEach((example) => examples.append(el("li", "", example)));
      item.append(examples);
    }
    item.append(reviewActions(gap.message_ids, gap.review_status, (value) => {
      gap.review_status = value;
      renderGaps();
      renderHome();
    }));
    return item;
  }));
}

// "quotation.md — Quotation Module > Estimate versus quote" → one short line per document, 4 at most.
function documentList(sources) {
  const box = el("div");
  if (!sources?.length) return box;
  box.append(el("div", "muted", "Documents it used:"));
  const list = el("ul", "examples");
  sources.slice(0, 4).forEach((source) => list.append(el("li", "", source.length > 110 ? `${source.slice(0, 110)}…` : source)));
  if (sources.length > 4) list.append(el("li", "muted", `and ${sources.length - 4} more`));
  box.append(list);
  return box;
}

function renderDisliked() {
  const items = state.data.downvoted;
  setCount("nav-disliked", state.data.summary.open_downvotes);
  const list = document.getElementById("disliked-list");
  if (!items.length) {
    list.replaceChildren(emptyState("No disliked answers in this period."));
    return;
  }
  list.replaceChildren(...items.map((entry) => {
    const item = el("article", "item response-card");
    const top = el("div", "item-top");
    const heading = el("div");
    heading.append(el("div", "item-ref", `${entry.user_id} · ${formatTime(entry.created_at)}`), el("div", "item-title", entry.question));
    top.append(heading);
    const review = reviewBadge(entry.review_status);
    if (review) top.append(review);
    item.append(top);
    const answer = el("div", "response-preview");
    answer.append(el("span", "section-label", "ASSISTANT RESPONSE"), el("p", "quote", entry.answer));
    item.append(answer);
    const meta = el("div", "meta");
    meta.append(el("span", "", `Source: ${OUTCOME_TEXT[entry.route] || entry.route}`));
    if (entry.validation && !["approved", "none"].includes(entry.validation)) {
      meta.append(el("span", "", `Check: ${CHECK_TEXT[entry.validation] || entry.validation}`));
    }
    if (entry.mood && entry.mood !== "F0_NORMAL") meta.append(el("span", "", `Mood: ${MOOD_TEXT[entry.mood] || entry.mood}`));
    item.append(meta);
    item.append(documentList(entry.sources));
    const actions = reviewActions([entry.message_id], entry.review_status, (value) => {
      if (!entry.review_status && value) state.data.summary.open_downvotes -= 1;
      if (entry.review_status && !value) state.data.summary.open_downvotes += 1;
      entry.review_status = value;
      renderDisliked();
      renderHome();
    });
    actions.classList.add("response-footer");
    item.append(actions);
    return item;
  }));
}

// ── Security ─────────────────────────────────────────────────────────

function renderSecurity() {
  const events = state.data.security_events;
  setCount("nav-security", state.data.summary.security.alerts, true);
  const list = document.getElementById("security-list");
  if (!events.length) {
    list.replaceChildren(emptyState("Nothing was blocked. 🎉"));
    return;
  }
  // Summary first: one row per person, so repeat offenders stand out without scrolling.
  const people = new Map();
  events.forEach((event) => {
    const p = people.get(event.user_id) || { attempts: 0, high: 0, alerts: 0, last: event.created_at };
    p.attempts += 1;
    if (event.severity === "high") p.high += 1;
    if (event.alert_raised) p.alerts += 1;
    people.set(event.user_id, p);
  });
  const summary = el("div", "card");
  summary.append(el("h3", "", "Who was blocked"));
  const table = el("table", "mini wide");
  const head = table.insertRow();
  ["User", "Blocked attempts", "High risk", "Repeated (alerts)", "Last attempt"].forEach((t) => head.append(el("th", "", t)));
  [...people.entries()].sort((a, b) => b[1].attempts - a[1].attempts).forEach(([user, p]) => {
    const alertCell = el("td");
    alertCell.append(p.alerts ? badge(`🚨 ${p.alerts}`, "critical") : el("span", "muted", "—"));
    table.insertRow().append(el("td", "", user), el("td", "num", p.attempts), el("td", "num", p.high), alertCell,
      el("td", "", formatTime(p.last)));
  });
  const scroll = el("div", "scroll");
  scroll.append(table);
  summary.append(scroll);

  const limit = state.showAllSecurity ? events.length : 10;
  const cards = events.slice(0, limit).map((event) => {
    const item = el("article", "item");
    const top = el("div", "item-top");
    const heading = el("div");
    const label = event.label.replace(/^SEC_/, "").replaceAll("_", " ").toLowerCase();
    heading.append(el("div", "item-ref", `${event.user_id} · ${formatTime(event.created_at)}`),
      el("div", "item-title", label.charAt(0).toUpperCase() + label.slice(1)));
    const badges = el("div", "badges");
    badges.append(event.severity === "high" ? badge("High risk", "critical") : badge("Medium risk", "warning"));
    if (event.alert_raised) badges.append(badge("🚨 Repeated — alert raised", "critical"));
    top.append(heading, badges);
    item.append(top);
    if (event.query_excerpt) item.append(el("p", "quote", event.query_excerpt));
    if (where(event)) item.append(el("div", "meta", `🖥️ ${where(event)}`));
    return item;
  });
  const heading = el("h3", "", state.showAllSecurity ? `All ${events.length} blocked attempts` : "Latest blocked attempts");
  list.replaceChildren(summary, heading, ...cards);
  if (events.length > 10) {
    list.append(button(state.showAllSecurity ? "Show only the latest 10" : `Show all ${events.length}`, () => {
      state.showAllSecurity = !state.showAllSecurity;
      renderSecurity();
    }));
  }
}

// ── Ticket email (Outlook) ───────────────────────────────────────────

function renderMail(mail) {
  const summary = document.getElementById("mail-summary");
  if (!mail.enabled) {
    summary.textContent = "Off — tickets are saved here, but nobody is emailed. Set ESCALATION_NOTIFIER=outlook in .env.";
  } else if (mail.missing.length) {
    summary.textContent = `Not ready — fill in these .env values and restart the server: ${mail.missing.join(", ")}`;
  } else {
    const alerts = mail.alert_recipients.length ? mail.alert_recipients.join(", ") : "not emailed";
    summary.textContent = `Working — tickets are emailed to ${mail.ticket_recipients.join(", ")} from ${mail.sender}. ` +
      `Security alerts: ${alerts}.`;
  }
  document.getElementById("mail-test").disabled = !mail.enabled || mail.missing.length > 0;
}

document.getElementById("mail-test").addEventListener("click", async () => {
  const testButton = document.getElementById("mail-test");
  const result = document.getElementById("mail-test-result");
  testButton.disabled = true;
  result.textContent = "Sending…";
  try {
    const response = await fetch(`/api/admin/notifier/test?${query()}`, { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    result.textContent = data.sent ? `✅ Sent to ${data.to.join(", ")} — check the inbox.`
      : data.reason === "not_configured" ? `Not set up: ${data.missing.join(", ")}` : `⛔ Failed: ${data.error}`;
  } catch (err) {
    console.error(err);
    result.textContent = "Couldn’t send — check the role and the server.";
  } finally {
    testButton.disabled = false;
  }
});

// ── System health ────────────────────────────────────────────────────

const SVG = "http://www.w3.org/2000/svg";

function svgEl(tag, attrs = {}, text) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}

function shortDay(iso) {
  const [, m, d] = iso.split("-");
  return `${Number(d)}/${Number(m)}`;
}

// One chart = one measure on one axis. Bars (stacked when several series) or a line. Every mark
// has a hover tooltip.
function chart(container, days, series, { kind = "bar", format = (v) => String(v), label }) {
  // drawn close to the card's real width (~300px) so the axis text stays readable when scaled
  const width = 340, height = 160, left = 46, bottom = 22, top = 12;
  const plotW = width - left - 8, plotH = height - top - bottom;
  const totals = days.map((d) => series.reduce((sum, s) => sum + (Number(d[s.key]) || 0), 0));
  const max = Math.max(...totals, 0) || 1;
  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": label, class: "chart" });
  svg.append(svgEl("line", { x1: left, x2: width - 8, y1: top + plotH, y2: top + plotH, class: "axis" }));
  svg.append(svgEl("line", { x1: left, x2: width - 8, y1: top, y2: top, class: "grid" }));
  svg.append(svgEl("text", { x: left - 6, y: top + 4, class: "tick", "text-anchor": "end" }, format(max)));
  svg.append(svgEl("text", { x: left - 6, y: top + plotH, class: "tick", "text-anchor": "end" }, format(0)));
  const step = plotW / days.length;
  const barW = Math.max(4, Math.min(28, step - 6));
  const labelEvery = Math.ceil(days.length / 7);
  const points = [];
  days.forEach((day, i) => {
    const cx = left + step * i + step / 2;
    if ((days.length - 1 - i) % labelEvery === 0) { // counted back from today so labels never collide
      svg.append(svgEl("text", { x: cx, y: height - 6, class: "tick", "text-anchor": "middle" }, shortDay(day.day)));
    }
    if (kind === "line") {
      const v = day[series[0].key];
      if (v !== null && v !== undefined) points.push([cx, top + plotH - (v / max) * plotH, v, day.day]);
      return;
    }
    let y = top + plotH;
    series.forEach((s) => {
      const v = Number(day[s.key]) || 0;
      if (!v) return;
      const h = (v / max) * plotH;
      y -= h;
      const rect = svgEl("rect", { x: cx - barW / 2, y, width: barW, height: Math.max(h - 1, 1), rx: 3, class: s.cls });
      rect.append(svgEl("title", {}, `${day.day} · ${s.name}: ${format(v)}`));
      svg.append(rect);
    });
  });
  if (kind === "line" && points.length) {
    svg.append(svgEl("polyline", { points: points.map((p) => `${p[0]},${p[1]}`).join(" "), class: "line" }));
    points.forEach(([x, y, v, d]) => {
      const dot = svgEl("circle", { cx: x, cy: y, r: 4, class: "dot" });
      dot.append(svgEl("title", {}, `${d} · ${series[0].name}: ${format(v)}`));
      svg.append(dot);
    });
  }
  container.replaceChildren(svg);
  if (series.length > 1) {
    const legend = el("div", "legend");
    series.forEach((s) => {
      const item = el("span", "legend-item");
      item.append(el("span", `swatch ${s.cls}`), el("span", "", s.name));
      legend.append(item);
    });
    container.append(legend);
  }
}

function fmtSeconds(v) {
  return v === null || v === undefined ? "—" : `${v} s`;
}

function renderBreakdown(tableId, counts, labels) {
  const table = document.getElementById(tableId);
  const entries = Object.entries(counts || {});
  const total = entries.reduce((sum, [, n]) => sum + n, 0);
  table.replaceChildren();
  if (!entries.length) {
    table.insertRow().append(el("td", "", "No data in this period"));
    return;
  }
  for (const [key, count] of entries) {
    table.insertRow().append(el("td", "", labels[key] || key), el("td", "num", count),
      el("td", "pct", total ? `${Math.round((100 * count) / total)}%` : ""));
  }
}

const SERVICE_TEXT = { postgres: "Database", milvus: "Document search", redis: "Permission cache" };

function renderHealth(h) {
  document.getElementById("health-updated").textContent =
    `Checked just now · running for ${Math.round(h.uptime_s / 60)} min` +
    (h.process.ram_mb ? ` · memory ${h.process.ram_mb} MB` : "");
  document.getElementById("health-services").replaceChildren(...Object.entries(h.services).map(([name, r]) =>
    badge(`${r.ok ? "✓" : "⛔"} ${SERVICE_TEXT[name] || name}: ${r.ok ? "working" : "DOWN"}`, r.ok ? "good" : "critical")));

  const d = h.last_24h;
  const open = h.open_alerts.length;
  setCount("nav-health", open, true);
  document.getElementById("health-stats").replaceChildren(
    stat("Questions (last 24 h)", d.requests, `${d.answered} answered · ${d.errors} failed`),
    stat("Response time", fmtSeconds(d.p95_latency_s), `almost all answers are faster · typical ${fmtSeconds(d.p50_latency_s)}`),
    stat("Errors (last 24 h)", d.error_rate_pct === null ? "—" : `${d.error_rate_pct}%`, `alert above ${h.thresholds.error_rate_pct}%`),
    stat("OpenAI cost today", `$${h.cost_today_usd.toFixed(2)}`, `alert above $${h.thresholds.daily_cost_usd.toFixed(2)} a day`),
  );

  chart(document.getElementById("chart-requests"), h.daily,
    [{ key: "answered", name: "Answered", cls: "bar-a" },
     { key: "unanswered_or_other", name: "Not answered, small talk or blocked", cls: "bar-b" }],
    { label: "Questions per day", format: (v) => String(Math.round(v)) });
  chart(document.getElementById("chart-latency"), h.daily, [{ key: "p95_latency_s", name: "Response time" }],
    { kind: "line", label: "Response time per day", format: (v) => `${Number(v).toFixed(0)} s` });
  chart(document.getElementById("chart-cost"), h.daily, [{ key: "cost_usd", name: "Cost", cls: "bar-a" }],
    { label: "OpenAI cost per day", format: (v) => `$${Number(v).toFixed(2)}` });
  chart(document.getElementById("chart-check"), h.daily,
    [{ key: "checked_ok", name: "✓ Matched / approved", cls: "bar-good" },
     { key: "repaired", name: "Corrected", cls: "bar-warn" },
     { key: "refused_or_not_found", name: "⛔ Refused / not in documents", cls: "bar-bad" }],
    { label: "Answer check per day", format: (v) => String(Math.round(v)) });

  const llm = document.getElementById("health-llm");
  llm.replaceChildren();
  const head = llm.insertRow();
  ["Purpose", "Model", "Calls", "Failed", "Avg time", "Tokens in / out", "Cost"].forEach((t) => head.append(el("th", "", t)));
  if (!h.llm.length) llm.insertRow().append(el("td", "", "No OpenAI calls in this period"));
  h.llm.forEach((r) => {
    llm.insertRow().append(el("td", "", r.purpose.replaceAll("_", " ")), el("td", "", r.model), el("td", "num", r.calls),
      el("td", "num", r.failures), el("td", "num", `${(r.avg_ms / 1000).toFixed(1)} s`),
      el("td", "num", `${r.prompt_tokens.toLocaleString()} / ${r.completion_tokens.toLocaleString()}`),
      el("td", "num", `$${r.cost_usd.toFixed(3)}`));
  });
  const stages = document.getElementById("health-stages");
  stages.replaceChildren();
  const shead = stages.insertRow();
  ["Step", "Runs", "Average", "Slowest", ""].forEach((t) => shead.append(el("th", "", t)));
  const slowest = Math.max(1, ...h.stages.map((s) => s.avg_ms));
  h.stages.forEach((s) => {
    const bar = el("td", "bar-cell");
    const fill = el("span", "meter");
    fill.style.width = `${Math.max(2, (100 * s.avg_ms) / slowest)}%`;
    bar.append(fill);
    stages.insertRow().append(el("td", "", s.stage.replaceAll("_", " ")), el("td", "num", s.runs),
      el("td", "num", `${(s.avg_ms / 1000).toFixed(2)} s`), el("td", "num", `${(s.max_ms / 1000).toFixed(1)} s`), bar);
  });

  const t = h.thresholds;
  document.getElementById("health-thresholds").textContent =
    `Checked automatically every few minutes. An alert is raised when errors pass ${t.error_rate_pct}%, answers take ` +
    `longer than ${t.p95_latency_s} s, fewer than ${t.answered_pct_min}% are answered, cost passes $${t.daily_cost_usd} a day, ` +
    `or a service is down.`;
  const alerts = document.getElementById("health-alerts");
  if (!h.recent_alerts.length) {
    alerts.replaceChildren(el("div", "all-clear", "✓ No alerts — everything is within limits."));
  } else {
    alerts.replaceChildren(...h.recent_alerts.map((a) => {
      const row = el("div", "alert-row");
      const text = el("div");
      text.append(el("div", "item-title", a.message),
        el("div", "muted", `raised ${formatTime(a.raised_at)}${a.resolved_at ? ` · resolved ${formatTime(a.resolved_at)}` : ""}`));
      row.append(text, a.resolved_at ? badge("✓ Resolved", "good")
        : badge(a.severity === "critical" ? "⛔ Open" : "⚠ Open", a.severity === "critical" ? "critical" : "warning"));
      return row;
    }));
  }
}

async function loadHealth() {
  try {
    const response = await fetch(`/api/admin/health?${query({ days: Math.max(Number(daysEl.value), 14) })}`);
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    const h = await response.json();
    h.daily.forEach((d) => { d.unanswered_or_other = Math.max(0, d.requests - d.answered); });
    state.health = h;
    renderHealth(h);
  } catch (err) {
    console.error(err);
    document.getElementById("health-updated").textContent = "Health numbers are unavailable (the database is needed).";
  }
  if (state.data) renderHome();
}

document.getElementById("health-check").addEventListener("click", async () => {
  const result = document.getElementById("health-check-result");
  result.textContent = "Checking…";
  try {
    const response = await fetch(`/api/admin/health/check?${query()}`, { method: "POST" });
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    const data = await response.json();
    result.textContent = data.changes.length
      ? data.changes.map((c) => `${c.change}: ${c.rule.replaceAll("_", " ")}`).join(" · ")
      : data.open_alerts.length ? `${plural(data.open_alerts.length, "alert")} still open` : "✓ All good";
    loadHealth();
  } catch (err) {
    console.error(err);
    result.textContent = "Couldn’t run the check.";
  }
});

// ── Activity log ─────────────────────────────────────────────────────

function describeDetails(details) {
  const entries = Object.entries(details || {}).filter(([, v]) => v !== null && v !== "" && typeof v !== "object");
  return entries.map(([k, v]) => `${k.replaceAll("_", " ")}: ${v}`).join(" · ") || "—";
}

async function searchAudit(event) {
  if (event) event.preventDefault();
  const results = document.getElementById("audit-results");
  results.replaceChildren(el("p", "muted", "Searching…"));
  const params = { days: daysEl.value };
  const filters = { user_id: "audit-user", event_type: "audit-type", status: "audit-status", request_id: "audit-request" };
  for (const [name, id] of Object.entries(filters)) {
    const value = document.getElementById(id).value.trim();
    if (value) params[name] = value;
  }
  try {
    const response = await fetch(`/api/admin/audit?${query(params)}`);
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    const { events } = await response.json();
    if (!events.length) {
      results.replaceChildren(emptyState("Nothing matches this search."));
      return;
    }
    const table = el("table", "mini wide audit-table");
    const head = table.insertRow();
    ["When", "User", "What happened", "Details", "Result", "Time", "Cost"].forEach((t) => head.append(el("th", "", t)));
    events.forEach((e) => {
      const row = table.insertRow();
      const details = e.event_type === "chat" ? (e.question_text || "—") : describeDetails(e.details);
      const result = el("td");
      const status = STATUS_TEXT[e.status];
      if (status) result.append(badge(status.text, status.kind));
      row.append(el("td", "", formatTime(e.created_at)), el("td", "", e.user_id || "—"),
        el("td", "", EVENT_TEXT[e.event_type] || e.event_type), el("td", "wrap", details), result,
        el("td", "num", e.latency_ms ? `${(e.latency_ms / 1000).toFixed(1)} s` : ""),
        el("td", "num", e.cost_usd ? `$${e.cost_usd.toFixed(4)}` : ""));
      row.title = `request ${e.request_id || "—"}${e.answer_preview ? `\nanswer: ${e.answer_preview}` : ""}`;
    });
    const wrap = el("div", "card scroll");
    wrap.append(el("p", "muted", `${plural(events.length, "record")} · point at a row to see its answer and request id`), table);
    results.replaceChildren(wrap);
  } catch (err) {
    console.error(err);
    results.replaceChildren(emptyState("Couldn’t search the activity log."));
  }
}

document.getElementById("audit-form").addEventListener("submit", searchAudit);

// ── Load ─────────────────────────────────────────────────────────────

let retryTimer = null;

async function load(attempt = 0) {
  clearTimeout(retryTimer);
  refreshEl.disabled = true;
  showMessage("Loading…");
  exportEl.href = `/api/admin/content-gaps.csv?${query({ days: Math.max(Number(daysEl.value), 30) })}`;
  const includeDone = [...showDoneEls].some((box) => box.checked);
  try {
    const response = await fetch(`/api/admin/overview?${query({ days: daysEl.value, include_reviewed: includeDone })}`);
    if (response.status === 403) {
      consoleEl.hidden = true;
      showMessage(`🔒 This console is only for the support team. The “${groupEl.selectedOptions[0].text}” role can’t ` +
        "open it — choose “Support admin” in “Testing as” above.", true);
      return;
    }
    if (response.status === 503) {
      consoleEl.hidden = true;
      showMessage("The console is unavailable because the database is down.", true);
      return;
    }
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    state.data = await response.json();
    const s = state.data.summary;
    renderTickets();
    renderGaps();
    renderDisliked();
    renderSecurity();
    renderMail(state.data.mail);
    renderBreakdown("validation-table", s.breakdown.validation, CHECK_TEXT);
    renderBreakdown("mood-table", s.breakdown.mood, MOOD_TEXT);
    renderBreakdown("route-table", s.breakdown.route, OUTCOME_TEXT);
    renderHome();
    loadHealth();
    consoleEl.hidden = false;
    showMessage("");
    const audit = document.getElementById("audit-results");
    if (audit.childElementCount) searchAudit();
  } catch (err) {
    // Usually the server is restarting (it reloads after a code change, ~40 s): try again by itself.
    console.warn(err);
    if (attempt < 20) {
      showMessage(`⏳ Can’t reach the server yet — it may be starting up. Trying again… (${attempt + 1})`);
      retryTimer = setTimeout(() => load(attempt + 1), 3000);
    } else {
      showMessage("Couldn’t reach the server. Check that it is running, then press Refresh.", true);
    }
  } finally {
    refreshEl.disabled = false;
  }
}

showDoneEls.forEach((box) => box.addEventListener("change", () => {
  showDoneEls.forEach((other) => { other.checked = box.checked; });
  load();
}));
[groupEl, daysEl].forEach((control) => control.addEventListener("change", () => load()));
refreshEl.addEventListener("click", () => load());
load();
