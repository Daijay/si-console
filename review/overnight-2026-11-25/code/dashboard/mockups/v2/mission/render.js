(function () {
  "use strict";

  var V2 = window.V2;

  // Accent color for the state banner. Red is the hardware reject
  // button and kill switch color, used only for rejected, frozen, error.
  var STATE_COLOR = {
    idle: "#8a94a6",
    listening: "#4aa8ff",
    thinking: "#2ecc71",
    approval: "#f5c542",
    approved: "#2ecc71",
    rejected: "#e5484d",
    frozen: "#e5484d",
    error: "#e5484d"
  };

  // Handoff graph edges per state. done = finished, active = in progress.
  // Edges: 0 COORD->AGENT 1, 1 AGENT 1->AGENT 2, 2 AGENT 2->GUARD.
  var HANDOFF = {
    idle: { done: [], active: [], node: null },
    listening: { done: [], active: [], node: "coord" },
    thinking: { done: [], active: [0], node: "agent1" },
    approval: { done: [0, 1], active: [2], node: "guard" },
    approved: { done: [0, 1, 2], active: [], node: "agent2" },
    rejected: { done: [], active: [], node: "coord" },
    frozen: { done: [], active: [], node: null },
    error: { done: [], active: [], node: "guard" }
  };

  var LED_KEY = { coord: "coord", agent1: "agent1", agent2: "agent2", guard: "guard", hermes: null };

  function h(tag, cls, text) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text !== undefined && text !== null) el.textContent = text;
    return el;
  }

  function ledDot(ledState, color) {
    var d = h("span", "led led-" + ledState);
    d.style.setProperty("--led", color);
    d.title = ledState;
    return d;
  }

  function statusChip(status, color) {
    var c = h("span", "status-chip", status.toUpperCase());
    c.style.setProperty("--sc", color);
    return c;
  }

  // --- shared components -------------------------------------------------

  function rosterCards(snap) {
    var wrap = h("div", "roster");
    V2.ROSTER.forEach(function (a) {
      var card = h("div", "agent-card");
      card.style.setProperty("--ac", a.color);
      var top = h("div", "agent-top");
      var ledKey = LED_KEY[a.id];
      if (ledKey) top.appendChild(ledDot(snap.leds[ledKey], a.color));
      else top.appendChild(ledDot("off", a.color));
      top.appendChild(h("span", "agent-name", a.name));
      top.appendChild(statusChip(snap.rosterStatus[a.id], a.color));
      card.appendChild(top);
      var meta = h("div", "agent-meta");
      meta.appendChild(h("span", "agent-role", a.role));
      // COORD has role and tier both "coordinator". Show the tier
      // only when it adds information.
      if (a.tier !== a.role) meta.appendChild(h("span", "agent-tier", a.tier));
      card.appendChild(meta);
      wrap.appendChild(card);
    });
    return wrap;
  }

  function rosterStrip(snap) {
    // Compact one-row roster for the mini screen.
    var wrap = h("div", "roster-strip");
    V2.ROSTER.forEach(function (a) {
      var cell = h("div", "rs-cell");
      cell.style.setProperty("--ac", a.color);
      var ledKey = LED_KEY[a.id];
      cell.appendChild(ledDot(ledKey ? snap.leds[ledKey] : "off", a.color));
      cell.appendChild(h("div", "rs-name", a.name));
      cell.appendChild(h("div", "rs-status", snap.rosterStatus[a.id].toUpperCase()));
      wrap.appendChild(cell);
    });
    return wrap;
  }

  function handoffGraph(snap) {
    var plan = HANDOFF[snap.state];
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 640 190");
    svg.setAttribute("class", "handoff-svg");
    svg.setAttribute("role", "img");
    var nodes = [
      { id: "coord", x: 10, label: "COORD", sub: "routes" },
      { id: "agent1", x: 175, label: "AGENT 1", sub: "signal" },
      { id: "agent2", x: 340, label: "AGENT 2", sub: "risk" },
      { id: "guard", x: 505, label: "GUARD", sub: "gate" }
    ];
    var colors = { coord: "#2ecc71", agent1: "#e8ecf1", agent2: "#4aa8ff", guard: "#f5c542" };
    var ns = "http://www.w3.org/2000/svg";
    function el(name, attrs) {
      var e = document.createElementNS(ns, name);
      for (var k in attrs) e.setAttribute(k, attrs[k]);
      return e;
    }
    // Edges between node boxes (boxes 125 wide, 64 tall, y 40).
    var edges = [
      { x1: 135, x2: 175 }, { x1: 300, x2: 340 }, { x1: 465, x2: 505 }
    ];
    edges.forEach(function (e, i) {
      var line = el("line", { x1: e.x1, y1: 72, x2: e.x2, y2: 72, "class": "edge" });
      if (plan.done.indexOf(i) >= 0) line.setAttribute("class", "edge edge-done");
      if (plan.active.indexOf(i) >= 0) line.setAttribute("class", "edge edge-active");
      svg.appendChild(line);
      var arrow = el("path", { d: "M " + (e.x2 - 2) + " 66 L " + (e.x2 + 8) + " 72 L " + (e.x2 - 2) + " 78 Z", "class": "arrow" });
      if (plan.done.indexOf(i) >= 0) arrow.setAttribute("class", "arrow arrow-done");
      if (plan.active.indexOf(i) >= 0) arrow.setAttribute("class", "arrow arrow-active");
      svg.appendChild(arrow);
    });
    nodes.forEach(function (n) {
      var active = plan.node === n.id;
      var g = el("g", { "class": "node" + (active ? " node-active" : "") });
      var rect = el("rect", { x: n.x, y: 40, width: 125, height: 64, rx: 6, "class": "node-box" });
      rect.style.stroke = colors[n.id];
      if (active) rect.setAttribute("class", "node-box node-box-active");
      g.appendChild(rect);
      var t = el("text", { x: n.x + 62, y: 66, "class": "node-label", "text-anchor": "middle" });
      t.textContent = n.label;
      g.appendChild(t);
      var s = el("text", { x: n.x + 62, y: 88, "class": "node-sub", "text-anchor": "middle" });
      s.textContent = snap.rosterStatus[n.id];
      g.appendChild(s);
      svg.appendChild(g);
    });
    // HERMES feeder, dashed, research only.
    var feed = el("line", { x1: 72, y1: 40, x2: 72, y2: 16, "class": "edge edge-feed" });
    svg.appendChild(feed);
    var feedText = el("text", { x: 84, y: 24, "class": "node-sub" });
    feedText.textContent = "HERMES · research only";
    svg.appendChild(feedText);
    var wrap = h("div", "handoff");
    wrap.appendChild(h("div", "panel-title", V2.label("handoff", snap.lang)));
    wrap.appendChild(svg);
    return wrap;
  }

  function meterBar(label, display, frac, color) {
    var m = h("div", "meter");
    var top = h("div", "meter-top");
    top.appendChild(h("span", "meter-label", label));
    top.appendChild(h("span", "meter-value", display));
    m.appendChild(top);
    var track = h("div", "meter-track");
    var fill = h("div", "meter-fill");
    fill.style.width = Math.max(2, Math.min(100, Math.round(frac * 100))) + "%";
    fill.style.background = color;
    track.appendChild(fill);
    m.appendChild(track);
    return m;
  }

  function metersPanel(snap) {
    var p = h("div", "panel meters");
    p.appendChild(h("div", "panel-title", V2.label("meters", snap.lang)));
    var mt = V2.METERS;
    p.appendChild(meterBar("DeepSeek " + mt.deepseekModel, mt.deepseekMs + " ms", mt.deepseekMs / 3000, "#4aa8ff"));
    p.appendChild(meterBar("Tokens in / out", mt.tokensIn + " / " + mt.tokensOut, mt.tokensIn / 4000, "#b48cff"));
    p.appendChild(meterBar("Cost today / $5.00 cap", "$" + mt.costTodayUsd.toFixed(2) + " / $5.00", mt.costTodayUsd / mt.costCapUsd, "#2ecc71"));
    p.appendChild(meterBar("Bocha web search", mt.bochaMs + " ms", mt.bochaMs / 3000, "#8a94a6"));
    return p;
  }

  function riskGauge(snap) {
    var pr = V2.PROPOSAL;
    var p = h("div", "panel risk");
    p.appendChild(h("div", "panel-title", V2.label("risk", snap.lang)));
    var row = h("div", "risk-row");
    row.appendChild(h("span", "risk-num", String(pr.riskScore)));
    row.appendChild(h("span", "risk-label", pr.riskLabel));
    row.appendChild(h("span", "risk-check", "risk_check " + pr.riskCheck));
    p.appendChild(row);
    var track = h("div", "meter-track risk-track");
    var fill = h("div", "meter-fill");
    fill.style.width = pr.riskScore + "%";
    fill.style.background = "#2ecc71";
    track.appendChild(fill);
    p.appendChild(track);
    var cap = h("div", "risk-cap", "Position cap " + pr.capUsedPct.toFixed(1) + "% of " + pr.capMaxPct.toFixed(1) + "% max");
    p.appendChild(cap);
    return p;
  }

  function taskQueue(snap) {
    var p = h("div", "panel tasks");
    p.appendChild(h("div", "panel-title", V2.label("taskQueue", snap.lang)));
    var table = h("div", "task-table");
    var head = h("div", "task-row task-head");
    ["TASK", "AGENT", "TYPE", "TICKER", "AMOUNT", "STATUS", "ROUND"].forEach(function (t) {
      head.appendChild(h("span", "", t));
    });
    table.appendChild(head);
    V2.tasksForState(snap.state).forEach(function (t) {
      var r = h("div", "task-row");
      r.appendChild(h("span", "mono", t.id));
      r.appendChild(h("span", "", t.agent));
      r.appendChild(h("span", "", t.type));
      r.appendChild(h("span", "mono", t.ticker || "-"));
      r.appendChild(h("span", "mono", t.amount ? V2.money(t.amount) : "-"));
      r.appendChild(h("span", "task-status st-" + t.status, t.status));
      r.appendChild(h("span", "mono", String(t.round)));
      table.appendChild(r);
    });
    p.appendChild(table);
    return p;
  }

  function tapePanel(snap) {
    var p = h("div", "panel tape");
    p.appendChild(h("div", "panel-title", V2.label("tape", snap.lang)));
    var list = h("div", "tape-list");
    // Show the last 8 entries. The full per-state list is longer
    // (10 in approval, 11 in frozen), and the panel fits 8 rows.
    // Slicing keeps the closing event visible: the fill, the
    // HUMAN_REJECT, or the KILL_SWITCH is always the last row.
    V2.tapeForState(snap.state).slice(-8).forEach(function (e) {
      var row = h("div", "tape-row");
      row.appendChild(h("span", "mono tape-time", e.t));
      row.appendChild(h("span", "tape-who", e.who));
      row.appendChild(h("span", "tape-text", e.text));
      list.appendChild(row);
    });
    p.appendChild(list);
    return p;
  }

  function pnlStrip(snap) {
    var sc = V2.SCENARIO;
    var zh = snap.lang === "zh";
    var f = h("footer", "pnl");
    function cell(label, value, cls) {
      var c = h("div", "pnl-cell");
      c.appendChild(h("span", "pnl-label", label));
      c.appendChild(h("span", "pnl-value mono " + (cls || ""), value));
      return c;
    }
    f.appendChild(cell(zh ? V2.label("portfolio", "zh") + " · 模拟" : "PORTFOLIO · PAPER", V2.money(sc.portfolioValue)));
    f.appendChild(cell(zh ? "当日盈亏" : "DAY P AND L", V2.signed(sc.portfolioDay) + " (" + V2.pct(sc.portfolioDayPct) + ")", sc.portfolioDay < 0 ? "neg" : "pos"));
    f.appendChild(cell(zh ? "现金" : "CASH", V2.money(V2.cashForState(snap.state))));
    f.appendChild(cell(zh ? V2.label("costToday", "zh") + " / 上限" : "COST TODAY / CAP", "$1.84 / $5.00"));
    f.appendChild(cell(zh ? "回放" : "REPLAY", sc.replay + " · WEEK " + sc.replayWeek));
    return f;
  }

  function header(snap) {
    var hd = h("header", "topbar");
    var left = h("div", "top-left");
    left.appendChild(h("span", "brand", "SI CONSOLE"));
    left.appendChild(h("span", "top-sub", "MISSION CONTROL · BOOTH · 2022 REPLAY"));
    hd.appendChild(left);
    var right = h("div", "top-right");
    var lang = h("span", "lang-switch");
    var en = h("span", "lang-opt" + (snap.lang === "en" ? " lang-on" : ""), "EN");
    var zh = h("span", "lang-opt" + (snap.lang === "zh" ? " lang-on" : ""), "中文");
    lang.appendChild(en);
    lang.appendChild(h("span", "lang-sep", " / "));
    lang.appendChild(zh);
    right.appendChild(lang);
    right.appendChild(h("span", "top-clock mono", "11:42:19"));
    hd.appendChild(right);
    return hd;
  }

  function waveform(active) {
    var w = h("div", "waveform" + (active ? " wave-on" : ""));
    V2.WAVEFORM.forEach(function (v) {
      var b = h("div", "wave-bar");
      b.style.height = (active ? v : 8) + "%";
      w.appendChild(b);
    });
    return w;
  }

  // --- state hero (banner right side on monitor, main block on mini) ---

  function heroContent(snap, screen) {
    var st = snap.state;
    var pr = V2.PROPOSAL;
    var box = h("div", "hero hero-" + st);
    if (st === "idle") {
      box.appendChild(h("div", "attract-1", V2.ATTRACT.line1));
      box.appendChild(h("div", "attract-2", V2.ATTRACT.line2));
      box.appendChild(h("div", "attract-3", V2.ATTRACT.line3));
      return box;
    }
    if (st === "listening") {
      box.appendChild(h("div", "hero-label", V2.label("voice", snap.lang)));
      box.appendChild(waveform(true));
      box.appendChild(h("div", "hero-note", "Speak. The agents listen. Nothing executes without the green button."));
      return box;
    }
    if (st === "thinking") {
      var r = h("div", "round-big");
      r.appendChild(h("span", "round-num mono", V2.METERS.roundUsed + " / " + V2.METERS.roundMax));
      r.appendChild(h("span", "round-label", V2.label("round", snap.lang)));
      box.appendChild(r);
      box.appendChild(h("div", "hero-note", "DeepSeek " + V2.METERS.deepseekModel + " · " + V2.METERS.deepseekMs + " ms · " + V2.METERS.tokensIn + " tokens in"));
      return box;
    }
    if (st === "approval") {
      var prop = h("div", "proposal");
      prop.appendChild(h("span", "prop-action", pr.action));
      prop.appendChild(h("span", "prop-ticker mono", pr.ticker));
      prop.appendChild(h("span", "prop-detail mono", pr.shares + " @ $" + pr.price.toFixed(2) + " · " + V2.money(pr.amount)));
      box.appendChild(prop);
      var cd = h("div", "countdown");
      cd.appendChild(h("span", "cd-num mono", String(pr.approvalLeftS) + "s"));
      cd.appendChild(h("span", "cd-label", snap.lang === "zh" ? "共 " + pr.approvalExpiresS + "s · 任务 " + pr.taskId : "LEFT OF " + pr.approvalExpiresS + "s · TASK " + pr.taskId));
      box.appendChild(cd);
      var btns = h("div", "btn-row");
      var g = h("span", "btn-green", snap.lang === "zh" ? "绿色 — 批准" : "GREEN — APPROVE");
      var rd = h("span", "btn-red", snap.lang === "zh" ? "红色 — 拒绝" : "RED — REJECT");
      btns.appendChild(g);
      btns.appendChild(rd);
      box.appendChild(btns);
      if (screen === "monitor") {
        // Full risk gauge lives in the right column on monitor.
        // The banner carries the one-line risk summary only, so the
        // banner fits its 208px height.
        box.appendChild(h("div", "hero-note", (snap.lang === "zh" ? "风险" : "RISK") + " " + pr.riskScore + " " + pr.riskLabel + " · risk_check " + pr.riskCheck + " · cap " + pr.capUsedPct.toFixed(1) + "% of " + pr.capMaxPct.toFixed(1) + "%"));
      } else {
        box.appendChild(riskGauge(snap));
      }
      return box;
    }
    if (st === "approved") {
      box.appendChild(h("div", "hero-line", "FILLED — BUY XLE 141 @ $88.42 · $12,500.00"));
      box.appendChild(h("div", "hero-line hero-sub", "Cash after fill $10,650.00 · AGENT 2 running risk check"));
      box.appendChild(h("div", "hero-big mono", V2.money(V2.SCENARIO.portfolioValue)));
      return box;
    }
    if (st === "rejected") {
      var struck = h("div", "hero-line struck", "BUY XLE 141 @ $88.42 · $12,500.00");
      box.appendChild(struck);
      box.appendChild(h("div", "hero-line", "HUMAN_REJECT — task ord-0142 blocked"));
      box.appendChild(h("div", "hero-note", "Coordinator routes back to signal for a new proposal."));
      return box;
    }
    if (st === "frozen") {
      box.appendChild(h("div", "hero-line", "KILL SWITCH ENGAGED — ALL AGENTS FROZEN"));
      box.appendChild(h("div", "hero-line hero-sub", snap.strings.press_green_to_resume));
      box.appendChild(h("div", "hero-note", "Claims cancelled. Working tasks blocked with KILL_SWITCH."));
      return box;
    }
    // error
    box.appendChild(h("div", "hero-line", V2.ERROR.code + " — " + V2.ERROR.text));
    box.appendChild(h("div", "hero-line hero-sub", "RETRY IN " + V2.ERROR.retryInS + "s · LAST OK " + V2.ERROR.lastOk));
    box.appendChild(h("div", "hero-note", "Recorded fallback ready. GUARD still watching."));
    return box;
  }

  function banner(snap, screen) {
    var b = h("section", "banner");
    b.style.setProperty("--sc", STATE_COLOR[snap.state]);
    var left = h("div", "banner-left");
    left.appendChild(h("div", "state-word", snap.word));
    left.appendChild(h("div", "state-sentence", snap.sentence));
    b.appendChild(left);
    if (screen === "monitor") {
      var right = h("div", "banner-right");
      right.appendChild(heroContent(snap, screen));
      b.appendChild(right);
    }
    return b;
  }

  // --- renderers ---------------------------------------------------------

  function renderMonitor(snap) {
    var root = h("div", "mon");
    root.appendChild(header(snap));
    root.appendChild(banner(snap, "monitor"));
    var grid = h("main", "grid");
    var col1 = h("div", "col");
    col1.appendChild(h("div", "panel-title", V2.label("agents", snap.lang)));
    col1.appendChild(rosterCards(snap));
    col1.appendChild(taskQueue(snap));
    grid.appendChild(col1);
    var col2 = h("div", "col");
    col2.appendChild(handoffGraph(snap));
    var round = h("div", "panel round-panel");
    round.appendChild(h("div", "panel-title", V2.label("round", snap.lang)));
    var rb = h("div", "round-big");
    rb.appendChild(h("span", "round-num mono", V2.METERS.roundUsed + " / " + V2.METERS.roundMax));
    rb.appendChild(h("span", "round-label", "MAX 3 ROUNDS, THEN ESCALATE"));
    round.appendChild(rb);
    col2.appendChild(round);
    col2.appendChild(tapePanel(snap));
    grid.appendChild(col2);
    var col3 = h("div", "col");
    col3.appendChild(metersPanel(snap));
    col3.appendChild(riskGauge(snap));
    col3.appendChild(waveformPanel(snap));
    col3.appendChild(sectorsPanel(snap));
    grid.appendChild(col3);
    root.appendChild(grid);
    root.appendChild(pnlStrip(snap));
    return root;
  }

  function waveformPanel(snap) {
    var p = h("div", "panel wave-panel" + (snap.state === "listening" ? " wave-live" : ""));
    p.appendChild(h("div", "panel-title", V2.label("voice", snap.lang)));
    p.appendChild(waveform(snap.state === "listening"));
    p.appendChild(h("div", "wave-note", snap.state === "listening" ? "MIC LIVE" : "MIC IDLE — HOLD BUTTON TO SPEAK"));
    if (snap.state === "listening") {
      // Fixed voice vocabulary from voice_intents.py. "What is
      // happening?" matches ask_status, "What is my portfolio value?"
      // matches ask_portfolio_value. Voice proposes only.
      // One line, not two: two lines push the sectors panel off the
      // bottom of the 1080 screen (measured 32px over). The waveform
      // also shrinks while live, see .wave-live in style.css.
      var q = snap.lang === "zh"
        ? "“状态” · “投资组合多少钱”"
        : "“What is happening?” · “What is my portfolio value?”";
      var line = h("div", "try-line");
      line.appendChild(document.createTextNode("TRY: "));
      line.appendChild(h("span", "try-q", q));
      p.appendChild(line);
    }
    return p;
  }

  function sectorsPanel(snap) {
    // Top 4 sectors by change. Real tickers from the allow list.
    var top = V2.SECTORS.slice().sort(function (a, b) { return b.chg - a.chg; }).slice(0, 4);
    var p = h("div", "panel sectors");
    p.appendChild(h("div", "panel-title", V2.label("sectors", snap.lang) + " · WEEK " + V2.SCENARIO.replayWeek));
    top.forEach(function (s) {
      var row = h("div", "sector-row");
      row.appendChild(h("span", "mono sector-ticker", s.ticker));
      row.appendChild(h("span", "sector-name", s.name));
      row.appendChild(h("span", "mono sector-chg " + (s.chg >= 0 ? "pos" : "neg"), V2.pct(s.chg)));
      p.appendChild(row);
    });
    return p;
  }

  function renderMini(snap) {
    var root = h("div", "mini");
    root.appendChild(header(snap));
    var b = h("section", "banner");
    b.style.setProperty("--sc", STATE_COLOR[snap.state]);
    b.appendChild(h("div", "state-word", snap.word));
    b.appendChild(h("div", "state-sentence", snap.sentence));
    root.appendChild(b);
    var hero = h("section", "mini-hero");
    hero.appendChild(heroContent(snap, "mini"));
    root.appendChild(hero);
    root.appendChild(rosterStrip(snap));
    root.appendChild(pnlStrip(snap));
    return root;
  }

  window.V2Render = function (screen, state, lang) {
    var snap = V2.stateSnapshot(state, lang);
    // Mark the language so CSS can drop letter-spacing on Chinese
    // labels (Han characters sit on a fixed em grid; tracking breaks
    // it) and raise CJK line-height.
    document.documentElement.setAttribute("lang", snap.lang);
    var root = document.getElementById("screen");
    root.innerHTML = "";
    root.appendChild(screen === "mini" ? renderMini(snap) : renderMonitor(snap));
    document.title = "SI Console mission " + screen + " " + state + (lang === "zh" ? " zh" : "");
  };
})();
