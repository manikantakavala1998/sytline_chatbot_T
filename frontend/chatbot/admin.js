// Feedback console (Phase 5 step 4). Reads /api/admin/overview and lets a SUPPORT_ADMIN review
// 👎 answers and unanswered questions and move tickets along. Every piece of user text is set
// with textContent — never innerHTML — so nothing a user typed can run in the admin's browser.

const groupEl = document.getElementById("group");
const daysEl = document.getElementById("days");
const includeReviewedEl = document.getElementById("include-reviewed");
const refreshEl = document.getElementById("refresh");
const exportEl = document.getElementById("export");
const messageEl = document.getElementById("message");
const consoleEl = document.getElementById("console");

const REVIEW_LABELS = { content_gap: "📝 Needs a document", reviewed: "✅ Reviewed", dismissed: "🚫 Dismissed" };
const VALIDATION_LABELS = {
  passed: "Passed", repaired: "Repaired (claim removed)", replaced: "Refused (couldn't confirm)",
  not_found: "Not in documents", unverified: "Unverified (checker down)", none: "Not checked (templates, Excel)",
  approved: "Approved Excel answer",
};
const MOOD_LABELS = {
  F0_NORMAL: "F0 Normal", F1_CONFUSED: "F1 Confused", F2_COMPLAINT: "F2 Complaint",
  F3_FRUSTRATED: "F3 Frustrated", F4_PERSISTENT: "F4 Repeated problem", none: "Small talk / not classified",
};
const ROUTE_LABELS = {
  FAST_QA_RESPONSE: "Approved Excel answer", MARKDOWN_RAG_RESPONSE: "Answer from documents",
  NO_ANSWER: "No answer", CLARIFY: "Asked to clarify", DIRECT_RESPONSE: "Small talk",
  OUT_OF_SCOPE: "Out of scope", CAPABILITY_PENDING: "Needs live data (Phase 4)", BLOCKED: "Blocked",
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function formatTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function query(extra = {}) {
  const params = new URLSearchParams({ simulated_group: groupEl.value, ...extra });
  return params.toString();
}

function showMessage(text, isError = false) {
  messageEl.hidden = !text;
  messageEl.textContent = text || "";
  messageEl.classList.toggle("error", isError);
}

// ── Tiles ────────────────────────────────────────────────────────────

function tile(label, value, detail, state) {
  const node = el("div", "tile");
  node.append(el("div", "label", label), el("div", "value", value ?? "—"));
  if (detail) node.append(el("div", "detail", detail));
  if (state) node.append(el("span", `state ${state.kind}`, state.text));
  return node;
}

function renderTiles(s) {
  const tiles = document.getElementById("tiles");
  tiles.replaceChildren(
    tile("Questions answered", s.answered_pct === null ? "—" : `${s.answered_pct}%`,
      `${s.answered} of ${s.answers - s.blocked} questions · ${s.conversations} chats`),
    tile("Rated helpful", s.satisfaction_pct === null ? "—" : `${s.satisfaction_pct}%`,
      `👍 ${s.thumbs_up} · 👎 ${s.thumbs_down}`),
    tile("Disliked, to review", s.open_downvotes, "👎 answers not yet reviewed",
      s.open_downvotes ? { kind: "warning", text: "⚠ Needs review" } : { kind: "good", text: "✓ All reviewed" }),
    tile("Unanswered questions", s.no_answer, `${s.clarify} more needed clarification`),
    tile("Open tickets", (s.tickets.open || 0) + (s.tickets.in_progress || 0),
      `${s.tickets.resolved || 0} resolved · ${s.tickets.closed || 0} closed`),
    tile("Security alerts", s.security.alerts, `${s.security.events} blocked attempts · ${s.security.high} high severity`,
      s.security.alerts ? { kind: "critical", text: "⛔ Investigate" } : { kind: "good", text: "✓ None" }),
  );
}

function renderBreakdown(tableId, counts, labels) {
  const table = document.getElementById(tableId);
  const entries = Object.entries(counts || {});
  const total = entries.reduce((sum, [, n]) => sum + n, 0);
  table.replaceChildren();
  if (!entries.length) {
    const row = table.insertRow();
    row.append(el("td", "", "No data in this period"));
    return;
  }
  for (const [key, count] of entries) {
    const row = table.insertRow();
    row.append(
      el("td", "", labels[key] || key),
      el("td", "num", count),
      el("td", "pct", total ? `${Math.round((100 * count) / total)}%` : ""),
    );
  }
}

// ── Review actions ───────────────────────────────────────────────────

async function send(method, path, body) {
  const response = await fetch(`${path}?${query()}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Server returned ${response.status}`);
  return response.json();
}

function reviewButtons(messageIds, currentStatus) {
  const actions = el("div", "actions");
  const status = el("span", "done", currentStatus ? `Current: ${REVIEW_LABELS[currentStatus]}` : "");
  const buttons = [];
  const choices = [["content_gap", "📝 Needs a document"], ["reviewed", "✅ Reviewed"], ["dismissed", "🚫 Dismiss"]];
  if (currentStatus) choices.push([null, "↩ Back to queue"]);
  for (const [value, label] of choices) {
    const button = el("button", value === "content_gap" ? "primary" : "", label);
    button.type = "button";
    button.addEventListener("click", async () => {
      buttons.forEach((b) => (b.disabled = true));
      status.textContent = "Saving…";
      try {
        for (const id of messageIds) await send("PUT", `/api/admin/feedback/${id}`, { status: value });
        status.textContent = value ? `Saved: ${REVIEW_LABELS[value]}` : "Back in the queue";
      } catch (err) {
        console.error(err);
        status.textContent = "Couldn’t save — check the role and try again.";
        buttons.forEach((b) => (b.disabled = false));
      }
    });
    buttons.push(button);
    actions.append(button);
  }
  actions.append(status);
  return actions;
}

// ── Panels ───────────────────────────────────────────────────────────

function emptyState(text) {
  return el("div", "empty", text);
}

function renderGaps(gaps) {
  const panel = document.getElementById("panel-gaps");
  document.getElementById("count-gaps").textContent = `(${gaps.length})`;
  if (!gaps.length) {
    panel.replaceChildren(emptyState("No unanswered questions in this period. 🎉"));
    return;
  }
  panel.replaceChildren(el("p", "hint",
    "Questions the assistant could not answer from the approved documents, grouped by topic and most asked first. " +
    "Mark “Needs a document” to hand the topic to the content team (also in the CSV export)."));
  for (const gap of gaps) {
    const item = el("article", "item");
    const head = el("div", "item-head");
    head.append(el("div", "item-title", gap.topic));
    const meta = el("div", "meta");
    meta.append(
      el("span", "pill", `Asked ${gap.count}×`),
      el("span", "", `${gap.user_count} user${gap.user_count === 1 ? "" : "s"}`),
      el("span", "", `last ${formatTime(gap.last_asked)}`),
    );
    head.append(meta);
    item.append(head);
    if (gap.examples.length > 1) {
      const list = el("ul", "examples");
      gap.examples.forEach((example) => list.append(el("li", "", example)));
      item.append(el("div", "meta", "How users asked it:"), list);
    }
    item.append(reviewButtons(gap.message_ids, gap.review_status));
    panel.append(item);
  }
}

function renderDownvoted(items) {
  const panel = document.getElementById("panel-downvoted");
  document.getElementById("count-downvoted").textContent = `(${items.length})`;
  if (!items.length) {
    panel.replaceChildren(emptyState("No 👎 answers to review in this period."));
    return;
  }
  panel.replaceChildren(el("p", "hint", "Answers users marked 👎, newest first. Check the answer against the documents, " +
    "then mark it — a wrong or missing document is a content gap."));
  for (const entry of items) {
    const item = el("article", "item");
    const head = el("div", "item-head");
    head.append(el("div", "item-title", entry.question));
    const meta = el("div", "meta");
    meta.append(
      el("span", "pill", ROUTE_LABELS[entry.route] || entry.route),
      el("span", "", entry.validation ? `check: ${VALIDATION_LABELS[entry.validation] || entry.validation}` : ""),
      el("span", "", entry.mood ? MOOD_LABELS[entry.mood] || entry.mood : ""),
      el("span", "", `${entry.user_id} · ${formatTime(entry.created_at)}`),
    );
    head.append(meta);
    item.append(head);
    if (entry.understood_as && entry.understood_as !== entry.question) {
      item.append(el("div", "meta", `Understood as: “${entry.understood_as}”`));
    }
    item.append(el("p", "quote", entry.answer));
    if (entry.sources.length) item.append(el("div", "meta", `Sources: ${entry.sources.join(" · ")}`));
    item.append(reviewButtons([entry.message_id], entry.review_status));
    panel.append(item);
  }
}

const PRIORITY_STATE = {
  high: { kind: "critical", text: "⬆ High priority" },
  normal: { kind: "neutral", text: "Normal priority" },
};
const TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"];

function renderTickets(tickets) {
  const panel = document.getElementById("panel-tickets");
  const open = tickets.filter((t) => t.status === "open" || t.status === "in_progress").length;
  document.getElementById("count-tickets").textContent = `(${open} open)`;
  if (!tickets.length) {
    panel.replaceChildren(emptyState("No support tickets yet."));
    return;
  }
  panel.replaceChildren();
  for (const ticket of tickets) {
    const item = el("article", "item");
    const head = el("div", "item-head");
    head.append(el("div", "item-title", `${ticket.ticket_ref} — ${ticket.issue_summary}`));
    const priority = PRIORITY_STATE[ticket.priority] || PRIORITY_STATE.normal;
    const meta = el("div", "meta");
    const mailState = MAIL_STATE[ticket.notification_status] || MAIL_STATE.pending;
    meta.append(el("span", `pill state ${priority.kind}`, priority.text),
      el("span", `pill state ${mailState.kind}`, mailState.text),
      el("span", "", `${ticket.user_display_name || ticket.user_id} · ${formatTime(ticket.created_at)}`));
    head.append(meta);
    item.append(head);

    const fields = el("dl", "fields");
    const add = (term, value) => {
      if (!value) return;
      fields.append(el("dt", "", term), el("dd", "", value));
    };
    add("Why offered", { frustration: "User frustrated", persistent: "Problem came back", unresolved: "Two unanswered replies",
      user_request: "User asked for a person", user_confirmed: "User raised it" }[ticket.trigger] || ticket.trigger);
    add("Screen", [ticket.site, ticket.module, ticket.form].filter(Boolean).join(" / "));
    add("Record", [ticket.record_type, ticket.record_id].filter(Boolean).join(" "));
    add("Already tried", (ticket.steps_attempted || []).join("\n"));
    add("User note", ticket.user_note);
    item.append(fields);

    const actions = el("div", "actions");
    const label = el("label", "meta", "Status ");
    const select = document.createElement("select");
    for (const status of TICKET_STATUSES) {
      const option = el("option", "", status.replace("_", " "));
      option.value = status;
      option.selected = status === ticket.status;
      select.append(option);
    }
    const saved = el("span", "done");
    select.addEventListener("change", async () => {
      select.disabled = true;
      saved.textContent = "Saving…";
      try {
        await send("PUT", `/api/admin/tickets/${ticket.ticket_id}`, { status: select.value });
        saved.textContent = "Saved";
      } catch (err) {
        console.error(err);
        saved.textContent = "Couldn’t save";
      } finally {
        select.disabled = false;
      }
    });
    label.append(select);
    actions.append(label, saved);
    item.append(actions);
    panel.append(item);
  }
}

const SEVERITY_STATE = {
  high: { kind: "critical", text: "⛔ High" },
  medium: { kind: "warning", text: "⚠ Medium" },
};

function renderSecurity(events) {
  const panel = document.getElementById("panel-security");
  const alerts = events.filter((e) => e.alert_raised).length;
  document.getElementById("count-security").textContent = `(${events.length}${alerts ? `, ${alerts} alert` : ""})`;
  if (!events.length) {
    panel.replaceChildren(emptyState("No blocked attempts recorded."));
    return;
  }
  panel.replaceChildren(el("p", "hint", "Blocked attacks and blocked answer leaks. Only a redacted excerpt is stored. " +
    "An alert is raised when one user is blocked 3 times within 15 minutes."));
  for (const event of events) {
    const item = el("article", "item");
    const head = el("div", "item-head");
    head.append(el("div", "item-title", event.label.replace(/^SEC_/, "").replaceAll("_", " ").toLowerCase()));
    const severity = SEVERITY_STATE[event.severity] || SEVERITY_STATE.medium;
    const meta = el("div", "meta");
    meta.append(el("span", `pill state ${severity.kind}`, severity.text));
    if (event.alert_raised) meta.append(el("span", "pill state critical", "🚨 Alert raised"));
    meta.append(el("span", "", `${event.user_id} · ${formatTime(event.created_at)}`));
    head.append(meta);
    item.append(head);
    if (event.query_excerpt) item.append(el("p", "quote", event.query_excerpt));
    const where = [event.site, event.module, event.form].filter(Boolean).join(" / ");
    if (where) item.append(el("div", "meta", `Screen: ${where}`));
    panel.append(item);
  }
}

// ── Ticket email (Outlook) ───────────────────────────────────────────

function renderMail(mail) {
  const summary = document.getElementById("mail-summary");
  const testButton = document.getElementById("mail-test");
  if (!mail.enabled) {
    summary.textContent = "Off — tickets are saved and shown here, but not emailed. Set ESCALATION_NOTIFIER=outlook in .env.";
  } else if (mail.missing.length) {
    summary.textContent = `Not ready — fill in these .env values and restart the server: ${mail.missing.join(", ")}`;
  } else {
    const alerts = mail.alert_recipients.length ? mail.alert_recipients.join(", ") : "not emailed";
    summary.textContent = `On (${mail.method}) — from ${mail.sender} · tickets to ${mail.ticket_recipients.join(", ")}` +
      ` · security alerts to ${alerts}`;
  }
  testButton.disabled = !mail.enabled || mail.missing.length > 0;
}

document.getElementById("mail-test").addEventListener("click", async () => {
  const button = document.getElementById("mail-test");
  const result = document.getElementById("mail-test-result");
  button.disabled = true;
  result.textContent = "Sending…";
  try {
    const response = await fetch(`/api/admin/notifier/test?${query()}`, { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    result.textContent = data.sent
      ? `✅ Sent to ${data.to.join(", ")} — check the inbox.`
      : data.reason === "not_configured"
        ? `Not configured: ${data.missing.join(", ")}`
        : `⛔ Failed: ${data.error}`;
  } catch (err) {
    console.error(err);
    result.textContent = "Couldn’t send — check the role and the server.";
  } finally {
    button.disabled = false;
  }
});

const MAIL_STATE = {
  sent: { kind: "good", text: "📧 Emailed" },
  failed: { kind: "critical", text: "⛔ Email failed" },
  not_configured: { kind: "warning", text: "⚠ Not emailed (mail not set up)" },
  pending: { kind: "neutral", text: "Email pending" },
  logged: { kind: "neutral", text: "Not emailed (mail off)" },
};

// ── Health tab (Phase 6) ─────────────────────────────────────────────

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
// has a hover tooltip; the numbers are also in the tables below for screen readers.
function chart(container, days, series, { kind = "bar", format = (v) => String(v), label }) {
  // drawn close to the card's real width (~300px) so the axis text stays readable when scaled
  const width = 340, height = 160, left = 46, bottom = 22, top = 12;
  const plotW = width - left - 8, plotH = height - top - bottom;
  const totals = days.map((d) => series.reduce((sum, s) => sum + (Number(d[s.key]) || 0), 0));
  const max = Math.max(...totals, 0) || 1;
  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": label, class: "chart" });
  // recessive grid: baseline + max line with its value
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

function serviceBadge(name, result) {
  const badge = el("span", `pill state ${result.ok ? "good" : "critical"}`,
    `${result.ok ? "✓" : "⛔"} ${name} ${result.ok ? `${result.ms} ms` : "DOWN"}`);
  return badge;
}

function fmtSeconds(v) {
  return v === null || v === undefined ? "—" : `${v} s`;
}

function renderHealth(h) {
  document.getElementById("health-updated").textContent =
    `Live checks just now · server up ${Math.round(h.uptime_s / 60)} min` +
    (h.process.ram_mb ? ` · memory ${h.process.ram_mb} MB · CPU ${h.process.cpu_pct}%` : "");
  const services = document.getElementById("health-services");
  services.replaceChildren(...Object.entries(h.services).map(([name, r]) => serviceBadge(name, r)));

  const d = h.last_24h;
  const open = h.open_alerts.length;
  document.getElementById("count-health").textContent = open ? `(${open} alert${open > 1 ? "s" : ""})` : "";
  document.getElementById("health-tiles").replaceChildren(
    tile("Questions (24 h)", d.requests, `${d.answered} answered · ${d.errors} failed`),
    tile("Response time (24 h)", fmtSeconds(d.p95_latency_s), `95% faster than this · median ${fmtSeconds(d.p50_latency_s)}`),
    tile("Errors (24 h)", d.error_rate_pct === null ? "—" : `${d.error_rate_pct}%`, `limit ${h.thresholds.error_rate_pct}%`,
      d.errors ? { kind: "warning", text: `⚠ ${d.errors} failed` } : { kind: "good", text: "✓ None" }),
    tile("OpenAI cost today", `$${h.cost_today_usd.toFixed(2)}`, `alert above $${h.thresholds.daily_cost_usd.toFixed(2)}`),
    tile("Fallbacks (24 h)", d.fallback_rate_pct === null ? "—" : `${d.fallback_rate_pct}%`,
      "fell back to rules or had a failed OpenAI call"),
    tile("Open alerts", open, open ? h.open_alerts.map((a) => a.rule).join(", ") : "all rules healthy",
      open ? { kind: "critical", text: "⛔ Investigate" } : { kind: "good", text: "✓ Healthy" }),
  );

  chart(document.getElementById("chart-requests"), h.daily,
    [{ key: "answered", name: "Answered", cls: "bar-a" },
     { key: "unanswered_or_other", name: "Other (no answer, clarify, small talk, blocked, errors)", cls: "bar-b" }],
    { label: "Questions per day", format: (v) => String(Math.round(v)) });
  chart(document.getElementById("chart-latency"), h.daily, [{ key: "p95_latency_s", name: "95th percentile" }],
    { kind: "line", label: "Response time per day", format: (v) => `${Number(v).toFixed(0)} s` });
  chart(document.getElementById("chart-cost"), h.daily, [{ key: "cost_usd", name: "Cost", cls: "bar-a" }],
    { label: "OpenAI cost per day", format: (v) => `$${Number(v).toFixed(2)}` });
  chart(document.getElementById("chart-check"), h.daily,
    [{ key: "checked_ok", name: "✓ Passed / approved", cls: "bar-good" },
     { key: "repaired", name: "🔧 Repaired", cls: "bar-warn" },
     { key: "refused_or_not_found", name: "⛔ Refused / not in documents", cls: "bar-bad" }],
    { label: "Answer check per day", format: (v) => String(Math.round(v)) });

  const llm = document.getElementById("health-llm");
  llm.replaceChildren();
  const head = llm.insertRow();
  ["Purpose", "Model", "Calls", "Failed", "Avg time", "Tokens in / out", "Cost"].forEach((t) => head.append(el("th", "", t)));
  if (!h.llm.length) llm.insertRow().append(el("td", "", "No OpenAI calls in this period"));
  h.llm.forEach((r) => {
    const row = llm.insertRow();
    row.append(el("td", "", r.purpose), el("td", "", r.model), el("td", "num", r.calls),
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
    const row = stages.insertRow();
    const bar = el("td", "bar-cell");
    const fill = el("span", "meter");
    fill.style.width = `${Math.max(2, (100 * s.avg_ms) / slowest)}%`;
    bar.append(fill);
    row.append(el("td", "", s.stage.replaceAll("_", " ")), el("td", "num", s.runs),
      el("td", "num", `${(s.avg_ms / 1000).toFixed(2)} s`), el("td", "num", `${(s.max_ms / 1000).toFixed(1)} s`), bar);
  });

  const t = h.thresholds;
  document.getElementById("health-thresholds").textContent =
    `Checked every few minutes over the last ${t.window_minutes} min (rates need ≥ ${t.min_requests} questions): ` +
    `errors > ${t.error_rate_pct}% · response time > ${t.p95_latency_s} s · fallbacks > ${t.fallback_rate_pct}% · ` +
    `answered < ${t.answered_pct_min}% · cost > $${t.daily_cost_usd}/day · a service down.`;
  const alerts = document.getElementById("health-alerts");
  if (!h.recent_alerts.length) {
    alerts.replaceChildren(emptyState("No health alerts yet."));
  } else {
    alerts.replaceChildren(...h.recent_alerts.map((a) => {
      const item = el("div", "item-head alert-row");
      const state = a.resolved_at ? { kind: "good", text: "✓ Resolved" }
        : { kind: a.severity === "critical" ? "critical" : "warning", text: a.severity === "critical" ? "⛔ Open" : "⚠ Open" };
      item.append(el("div", "", `${a.rule.replaceAll("_", " ")} — ${a.message}`));
      const meta = el("div", "meta");
      meta.append(el("span", `pill state ${state.kind}`, state.text),
        el("span", "", `raised ${formatTime(a.raised_at)}${a.resolved_at ? ` · resolved ${formatTime(a.resolved_at)}` : ""}`));
      item.append(meta);
      return item;
    }));
  }
}

async function loadHealth() {
  try {
    const response = await fetch(`/api/admin/health?${query({ days: Math.max(Number(daysEl.value), 14) })}`);
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    const h = await response.json();
    h.daily.forEach((d) => { d.unanswered_or_other = Math.max(0, d.requests - d.answered); });
    renderHealth(h);
  } catch (err) {
    console.error(err);
    document.getElementById("health-updated").textContent = "Health numbers unavailable (needs the audit store).";
  }
}

document.getElementById("health-check").addEventListener("click", async () => {
  const result = document.getElementById("health-check-result");
  result.textContent = "Checking…";
  try {
    const response = await fetch(`/api/admin/health/check?${query()}`, { method: "POST" });
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    const data = await response.json();
    result.textContent = data.changes.length
      ? data.changes.map((c) => `${c.change}: ${c.rule}`).join(" · ")
      : `No change · ${data.open_alerts.length} open alert(s)`;
    loadHealth();
  } catch (err) {
    console.error(err);
    result.textContent = "Couldn’t run the check.";
  }
});

// ── Audit tab (Phase 6) ──────────────────────────────────────────────

async function searchAudit(event) {
  if (event) event.preventDefault();
  const results = document.getElementById("audit-results");
  results.replaceChildren(el("p", "hint", "Searching…"));
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
      results.replaceChildren(emptyState("No audit records match."));
      return;
    }
    const table = el("table", "mini wide audit-table");
    const head = table.insertRow();
    ["When", "User", "What", "Question / details", "Route", "Status", "Check", "Time", "Cost"].forEach((t) =>
      head.append(el("th", "", t)));
    events.forEach((e) => {
      const row = table.insertRow();
      const what = e.event_type === "chat" ? (e.question_text || "—") : JSON.stringify(e.details || {});
      row.append(el("td", "", formatTime(e.created_at)), el("td", "", e.user_id || "—"), el("td", "", e.event_type),
        el("td", "wrap", what), el("td", "", e.route || ""), el("td", "", e.status || ""), el("td", "", e.grounding || ""),
        el("td", "num", e.latency_ms ? `${(e.latency_ms / 1000).toFixed(1)} s` : ""),
        el("td", "num", e.cost_usd ? `$${e.cost_usd.toFixed(4)}` : ""));
      row.title = `request ${e.request_id || "—"}${e.answer_preview ? `\nanswer: ${e.answer_preview}` : ""}`;
    });
    results.replaceChildren(el("p", "hint", `${events.length} record(s) — point at a row for its request id and answer.`),
      table);
  } catch (err) {
    console.error(err);
    results.replaceChildren(emptyState("Couldn’t search the audit trail."));
  }
}

document.getElementById("audit-form").addEventListener("submit", searchAudit);

// ── Load ─────────────────────────────────────────────────────────────

async function load() {
  refreshEl.disabled = true;
  showMessage("Loading…");
  exportEl.href = `/api/admin/content-gaps.csv?${query({ days: Math.max(Number(daysEl.value), 30) })}`;
  try {
    const response = await fetch(`/api/admin/overview?${query({
      days: daysEl.value, include_reviewed: includeReviewedEl.checked,
    })}`);
    if (response.status === 403) {
      consoleEl.hidden = true;
      showMessage(`🔒 The feedback console needs the SUPPORT_ADMIN role. “${groupEl.value}” can’t open it.`, true);
      return;
    }
    if (response.status === 503) {
      consoleEl.hidden = true;
      showMessage("The feedback console is unavailable because the database is down.", true);
      return;
    }
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    const data = await response.json();
    renderTiles(data.summary);
    renderBreakdown("validation-table", data.summary.breakdown.validation, VALIDATION_LABELS);
    renderBreakdown("mood-table", data.summary.breakdown.mood, MOOD_LABELS);
    renderBreakdown("route-table", data.summary.breakdown.route, ROUTE_LABELS);
    renderGaps(data.content_gaps);
    renderDownvoted(data.downvoted);
    renderTickets(data.tickets);
    renderSecurity(data.security_events);
    renderMail(data.mail);
    loadHealth();
    consoleEl.hidden = false;
    showMessage("");
  } catch (err) {
    console.error(err);
    showMessage("Couldn’t load the console. Is the server running?", true);
  } finally {
    refreshEl.disabled = false;
  }
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => {
      const active = t === tab;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", String(active));
      document.getElementById(`panel-${t.dataset.tab}`).hidden = !active;
    });
    if (tab.dataset.tab === "audit" && !document.getElementById("audit-results").childElementCount) searchAudit();
  });
});

[groupEl, daysEl, includeReviewedEl].forEach((control) => control.addEventListener("change", load));
refreshEl.addEventListener("click", load);
load();
