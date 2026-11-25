// SI Console UI v2, direction: hud. Renders both screens from window.V2.
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var CYAN = "#59d8ff";
  var AMBER = "#f5c542";
  var GREEN = "#2ecc71";
  var RED = "#ff8a76";
  var DIM = "#2a5a70";
  var FRAME = "#1c4256";

  function svgEl(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }

  function htmlEl(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }

  // Ring arc fraction per state (0-1). Frozen and error use a broken ring.
  var ARC_FRAC = {
    idle: 0.06, listening: 0.18, thinking: 0.55, approval: 0.725,
    approved: 1.0, rejected: 0.35, frozen: 0.5, error: 0.25
  };

  function buildRing(V, state, snap) {
    var svg = svgEl("svg", { viewBox: "0 0 400 400", role: "img" });
    var cx = 200, cy = 200;

    svg.appendChild(svgEl("circle", { cx: cx, cy: cy, r: 192, fill: "none", stroke: FRAME, "stroke-width": 1 }));
    svg.appendChild(svgEl("circle", { cx: cx, cy: cy, r: 140, fill: "none", stroke: "#12303f", "stroke-width": 1 }));

    // Tick marks around the outer frame.
    for (var i = 0; i < 60; i++) {
      var a = (i * 6) * Math.PI / 180;
      var long = i % 5 === 0;
      var r1 = long ? 176 : 184, r2 = 192;
      svg.appendChild(svgEl("line", {
        x1: (cx + r1 * Math.sin(a)).toFixed(1), y1: (cy - r1 * Math.cos(a)).toFixed(1),
        x2: (cx + r2 * Math.sin(a)).toFixed(1), y2: (cy - r2 * Math.cos(a)).toFixed(1),
        stroke: long ? "#3d7d99" : DIM, "stroke-width": long ? 2 : 1
      }));
    }

    // Voice waveform ring: 26 radial bars.
    var active = state === "listening" || state === "thinking";
    for (var j = 0; j < 26; j++) {
      var ang = j * (360 / 26);
      var h = 8 + V.WAVEFORM[j] * 0.28;
      var g = svgEl("g", { transform: "rotate(" + ang + " 200 200)" });
      g.appendChild(svgEl("rect", {
        x: 197, y: (200 - 158 - h).toFixed(1), width: 6, height: h.toFixed(1),
        fill: active ? CYAN : DIM, opacity: active ? 0.95 : 0.55
      }));
      svg.appendChild(g);
    }

    // State arc on r=170.
    var C = 2 * Math.PI * 170;
    var frac = ARC_FRAC[state] || 0;
    var arcColor = (state === "frozen" || state === "error") ? AMBER : CYAN;
    var arc = svgEl("circle", {
      cx: cx, cy: cy, r: 170, fill: "none", stroke: arcColor,
      "stroke-width": 3, "stroke-linecap": "butt",
      "stroke-dasharray": (C * frac).toFixed(1) + " " + C.toFixed(1)
    });
    if (state === "thinking") {
      // Spinning arc: no attribute rotation, CSS rotates the element
      // around its own center (transform-box fill-box in style.css).
      arc.setAttribute("class", "arc-spin");
    } else {
      arc.setAttribute("transform", "rotate(-90 200 200)");
    }
    svg.appendChild(arc);

    // Broken ring overlay for frozen and error.
    if (state === "frozen" || state === "error") {
      svg.appendChild(svgEl("circle", {
        cx: cx, cy: cy, r: 170, fill: "none", stroke: arcColor,
        "stroke-width": 3, "stroke-dasharray": "5 11", opacity: 0.55,
        transform: "rotate(-90 200 200)"
      }));
    }
    return svg;
  }

  function btnRow(lang) {
    var row = htmlEl("div", "btn-row");
    var g = htmlEl("span", "btn-chip btn-green");
    g.appendChild(htmlEl("span", "dot"));
    g.appendChild(document.createTextNode(lang === "zh" ? "绿色 批准" : "GREEN APPROVE"));
    var r = htmlEl("span", "btn-chip btn-red");
    r.appendChild(htmlEl("span", "dot"));
    r.appendChild(document.createTextNode(lang === "zh" ? "红色 拒绝" : "RED REJECT"));
    row.appendChild(g); row.appendChild(r);
    return row;
  }

  function ringCenter(V, state, snap, lang, screen) {
    var wrap = htmlEl("div", "ring-center");
    var word = htmlEl("div", "state-word", snap.word);
    wrap.appendChild(word);
    var sent = htmlEl("div", "sentence", snap.sentence);
    wrap.appendChild(sent);

    if (state === "idle") {
      var at = htmlEl("div", "proposal-block");
      at.appendChild(htmlEl("div", "proposal-line", V.ATTRACT.line1 + " " + V.ATTRACT.line2));
      at.appendChild(htmlEl("div", "proposal-sub", V.ATTRACT.line3));
      wrap.appendChild(at);
    }

    if (state === "approval") {
      var pb = htmlEl("div", "proposal-block");
      var p = V.PROPOSAL;
      pb.appendChild(htmlEl("div", "proposal-line mono",
        p.action + " " + p.ticker + "  " + p.shares + " @ " + V.money(p.price).replace("$", "") + "  " + V.money(p.amount)));
      pb.appendChild(htmlEl("div", "proposal-sub mono",
        "RISK " + p.riskScore + " " + p.riskLabel + "  ·  cap " + p.capUsedPct + "% / " + p.capMaxPct + "%  ·  " + p.taskId));
      pb.appendChild(htmlEl("div", "countdown mono", p.approvalLeftS + "s"));
      pb.appendChild(htmlEl("div", "countdown-sub", lang === "zh" ? "剩余时间，共 120 秒" : "left of 120s"));
      // Buttons live inside the ring on the monitor, where the ring is
      // big enough. On mini they go below the ring instead, so the
      // arc never crosses the chips.
      if (screen === "monitor") pb.appendChild(btnRow(lang));
      wrap.appendChild(pb);
    }

    if (state === "approved") {
      var ap = htmlEl("div", "proposal-block");
      var q = V.PROPOSAL;
      ap.appendChild(htmlEl("div", "proposal-line mono",
        "FILLED " + q.action + " " + q.ticker + " " + q.shares + " @ " + q.price.toFixed(2)));
      ap.appendChild(htmlEl("div", "proposal-sub mono",
        "PORTFOLIO " + V.money(V.SCENARIO.portfolioValue) + "  ·  " + V.money(q.amount)));
      wrap.appendChild(ap);
    }

    if (state === "rejected") {
      var rp = htmlEl("div", "proposal-block");
      rp.appendChild(htmlEl("div", "proposal-sub mono", "ord-0142  ·  HUMAN_REJECT  ·  blocked"));
      rp.appendChild(htmlEl("div", "proposal-sub", lang === "zh" ? "协调员重新规划新提议。" : "Coordinator routes a new proposal."));
      wrap.appendChild(rp);
    }

    if (state === "frozen") {
      wrap.appendChild(htmlEl("div", "frozen-note", snap.strings.press_green_to_resume));
    }

    if (state === "error") {
      wrap.appendChild(htmlEl("div", "error-code mono", V.ERROR.code));
      var en = htmlEl("div", "error-note", V.ERROR.text);
      wrap.appendChild(en);
      wrap.appendChild(htmlEl("div", "proposal-sub mono",
        "retry in " + V.ERROR.retryInS + "s  ·  last ok " + V.ERROR.lastOk));
    }
    return wrap;
  }

  function topbar(V, snap, lang, compact) {
    var bar = htmlEl("div", "topbar");
    bar.appendChild(htmlEl("div", "brand", "SI CONSOLE // HUD"));
    var pl = htmlEl("div", "pl-strip mono");
    var s = V.SCENARIO;
    var day = V.signed(s.portfolioDay) + " (" + V.pct(s.portfolioDayPct) + ")";
    if (compact) {
      pl.innerHTML = "";
      pl.appendChild(document.createTextNode(V.money(s.portfolioValue) + "  "));
      var d = htmlEl("span", s.portfolioDay < 0 ? "neg" : "pos", day);
      pl.appendChild(d);
      pl.appendChild(document.createTextNode("  " + s.replayWeek));
    } else {
      pl.innerHTML = "";
      pl.appendChild(document.createTextNode("PORTFOLIO " + V.money(s.portfolioValue) + "   DAY "));
      pl.appendChild(htmlEl("span", s.portfolioDay < 0 ? "neg" : "pos", day));
      pl.appendChild(document.createTextNode("   CASH " + V.money(V.cashForState(snap.state)) + "   2022 REPLAY " + s.replayWeek));
    }
    bar.appendChild(pl);
    var ls = htmlEl("div", "lang-switch mono");
    var en = htmlEl("span", lang === "en" ? "active" : "", "EN");
    var zh = htmlEl("span", lang === "zh" ? "active" : "", "中文");
    ls.appendChild(en); ls.appendChild(document.createTextNode(" | ")); ls.appendChild(zh);
    bar.appendChild(ls);
    return bar;
  }

  function rosterPanel(V, snap, lang) {
    var p = htmlEl("div", "panel");
    p.appendChild(htmlEl("div", "panel-label", V.label("agents", lang)));
    V.ROSTER.forEach(function (a) {
      var row = htmlEl("div", "roster-row");
      var dot = htmlEl("span", "dot");
      dot.style.background = a.color;
      var led = snap.leds[a.id === "coord" ? "coord" : a.id === "agent1" ? "agent1" : a.id === "agent2" ? "agent2" : a.id === "guard" ? "guard" : "coord"];
      if (led === "off") dot.style.opacity = "0.35";
      row.appendChild(dot);
      row.appendChild(htmlEl("span", "rname mono", a.name));
      row.appendChild(htmlEl("span", "rrole", a.role));
      var st = snap.rosterStatus[a.id] || "idle";
      row.appendChild(htmlEl("span", "rstatus " + st, st));
      p.appendChild(row);
    });
    return p;
  }

  function handoffPanel(V, snap, lang) {
    var p = htmlEl("div", "panel");
    p.appendChild(htmlEl("div", "panel-label", V.label("handoff", lang)));
    var svg = svgEl("svg", { viewBox: "0 0 340 64", "class": "handoff-svg" });
    var nodes = [V.ROSTER[0], V.ROSTER[1], V.ROSTER[2], V.ROSTER[3]];
    var xs = [28, 122, 216, 310];
    svg.appendChild(svgEl("line", { x1: 28, y1: 24, x2: 310, y2: 24, stroke: DIM, "stroke-width": 1 }));
    nodes.forEach(function (n, i) {
      svg.appendChild(svgEl("circle", { cx: xs[i], cy: 24, r: 6, fill: n.color }));
      var t = svgEl("text", { x: xs[i], y: 50, "text-anchor": "middle", fill: "#cfe3ec", "font-size": 12, "font-family": "monospace" });
      t.textContent = n.name;
      svg.appendChild(t);
    });
    // Handoff arrow marker removed: it overlapped the GUARD node.
    p.appendChild(svg);
    return p;
  }

  function metersPanel(V, lang) {
    var p = htmlEl("div", "panel");
    p.appendChild(htmlEl("div", "panel-label", V.label("meters", lang)));
    var m = V.METERS;
    var rows = [
      ["DEEPSEEK", m.deepseekMs + "ms  ·  " + m.deepseekModel],
      ["TOKENS", m.tokensIn + " in  /  " + m.tokensOut + " out"],
      ["BOCHA", m.bochaMs + "ms"],
      ["COST", "$" + m.costTodayUsd.toFixed(2) + " / $" + m.costCapUsd.toFixed(2) + " cap"]
    ];
    rows.forEach(function (r) {
      var row = htmlEl("div", "meter-row");
      row.appendChild(htmlEl("span", "mlabel mono", r[0]));
      row.appendChild(htmlEl("span", "mvalue mono", r[1]));
      p.appendChild(row);
    });
    var bar = htmlEl("div", "meter-bar");
    var fill = htmlEl("div", "fill");
    fill.style.width = Math.round(m.costTodayUsd / m.costCapUsd * 100) + "%";
    bar.appendChild(fill);
    p.appendChild(bar);
    var rr = htmlEl("div", "meter-row");
    rr.appendChild(htmlEl("span", "mlabel mono", V.label("round", lang)));
    var dots = htmlEl("span", "round-dots");
    for (var i = 1; i <= m.roundMax; i++) dots.appendChild(htmlEl("span", "rdot" + (i <= m.roundUsed ? " on" : "")));
    rr.appendChild(dots);
    p.appendChild(rr);
    return p;
  }

  function riskPanel(V, lang) {
    var p = htmlEl("div", "panel");
    p.appendChild(htmlEl("div", "panel-label", V.label("risk", lang)));
    var svg = svgEl("svg", { viewBox: "0 0 340 96", "class": "risk-svg" });
    // Semicircle gauge, 0-100. Arc from 180 to 0 degrees, r=70, center (170, 88).
    var r = 70, cx = 170, cy = 88;
    function arcPath(frac) {
      var a0 = Math.PI, a1 = Math.PI * (1 - frac);
      var x0 = cx + r * Math.cos(a0), y0 = cy - r * Math.sin(a0);
      var x1 = cx + r * Math.cos(a1), y1 = cy - r * Math.sin(a1);
      return "M " + x0.toFixed(1) + " " + y0.toFixed(1) + " A " + r + " " + r + " 0 0 1 " + x1.toFixed(1) + " " + y1.toFixed(1);
    }
    svg.appendChild(svgEl("path", { d: arcPath(1), fill: "none", stroke: "#0e2230", "stroke-width": 8 }));
    svg.appendChild(svgEl("path", { d: arcPath(V.PROPOSAL.riskScore / 100), fill: "none", stroke: GREEN, "stroke-width": 8 }));
    var t = svgEl("text", { x: cx, y: 62, "text-anchor": "middle", fill: "#eaf7ff", "font-size": 26, "font-family": "monospace", "font-weight": "bold" });
    t.textContent = V.PROPOSAL.riskScore;
    svg.appendChild(t);
    var t2 = svgEl("text", { x: cx, y: 84, "text-anchor": "middle", fill: "#7fb6c9", "font-size": 12, "font-family": "monospace" });
    t2.textContent = "RISK / 100";
    svg.appendChild(t2);
    p.appendChild(svg);
    var line = htmlEl("div", "risk-line mono");
    line.appendChild(htmlEl("span", "", "BUY XLE $12,500"));
    line.appendChild(htmlEl("span", "risk-low", "LOW · pass"));
    p.appendChild(line);
    var cap = htmlEl("div", "risk-line mono");
    cap.appendChild(htmlEl("span", "", "cap 12.5% / 25%"));
    cap.appendChild(htmlEl("span", "", "ord-0142"));
    p.appendChild(cap);
    return p;
  }

  function sectorsPanel(V, lang) {
    var p = htmlEl("div", "panel");
    p.appendChild(htmlEl("div", "panel-label", V.label("sectors", lang) + " — 2022-06-13"));
    V.SECTORS.forEach(function (s) {
      var row = htmlEl("div", "sector-row mono");
      row.appendChild(htmlEl("span", "stick", s.ticker));
      row.appendChild(htmlEl("span", "sname", s.name));
      row.appendChild(htmlEl("span", "sprice", s.price.toFixed(2)));
      row.appendChild(htmlEl("span", "schg " + (s.chg >= 0 ? "up" : "down"), V.pct(s.chg)));
      p.appendChild(row);
    });
    return p;
  }

  // Short agent tags keep the queue on one line per row.
  var AGENT_SHORT = { signal: "sig", risk: "risk", execution: "exec", coordinator: "coord" };

  function tasksPanel(V, state, lang) {
    var p = htmlEl("div", "panel grow");
    p.appendChild(htmlEl("div", "panel-label", V.label("taskQueue", lang)));
    V.tasksForState(state).forEach(function (t) {
      var row = htmlEl("div", "task-row mono");
      row.appendChild(htmlEl("span", "tid", t.id));
      row.appendChild(htmlEl("span", "tagent", AGENT_SHORT[t.agent] || t.agent));
      row.appendChild(htmlEl("span", "ttick", t.ticker || "—"));
      row.appendChild(htmlEl("span", "tamt", t.amount ? V.money(t.amount) : "—"));
      row.appendChild(htmlEl("span", "tstatus " + t.status, t.status));
      p.appendChild(row);
    });
    return p;
  }

  function ledsPanel(V, snap) {
    var p = htmlEl("div", "panel");
    p.appendChild(htmlEl("div", "panel-label", "LEDS — GPIO"));
    var keys = [
      ["COORD", "#2ecc71", "coord"], ["AGENT 1", "#e8ecf1", "agent1"],
      ["AGENT 2", "#4aa8ff", "agent2"], ["GUARD", "#f5c542", "guard"]
    ];
    keys.forEach(function (k) {
      var row = htmlEl("div", "led-row mono");
      var dot = htmlEl("span", "dot");
      dot.style.background = k[1];
      if (snap.leds[k[2]] === "off") dot.style.opacity = "0.3";
      row.appendChild(dot);
      row.appendChild(htmlEl("span", "lname", k[0]));
      row.appendChild(htmlEl("span", "lstate" + (snap.leds[k[2]] === "off" ? " off" : ""), snap.leds[k[2]]));
      p.appendChild(row);
    });
    return p;
  }

  function voicePanel(V, state, snap, lang) {
    var p = htmlEl("div", "panel grow");
    p.appendChild(htmlEl("div", "panel-label", V.label("voice", lang)));
    var bars = htmlEl("div", "voice-bars");
    var live = state === "listening";
    V.WAVEFORM.forEach(function (lvl) {
      var b = htmlEl("div", "vbar" + (live ? " live" : ""));
      // Flat baseline when the mic is idle: bars at 2px read as a
      // quiet line, not live audio. Live bars only while listening.
      b.style.height = live ? Math.max(3, Math.round(lvl * 0.52)) + "px" : "2px";
      bars.appendChild(b);
    });
    p.appendChild(bars);
    var line = htmlEl("div", "voice-line mono");
    line.appendChild(htmlEl("span", "", snap.sentenceId));
    line.appendChild(htmlEl("span", live ? "mic-live" : "", live ? "MIC LIVE" : "MIC IDLE"));
    p.appendChild(line);
    return p;
  }

  function tapeBar(V, count, state, lang) {
    var bar = htmlEl("div", "tapebar mono");
    bar.appendChild(htmlEl("span", "tape-label", V.label("tape", lang)));
    var evs = V.tapeForState(state).slice(-count);
    evs.forEach(function (e) {
      var ev = htmlEl("span", "tape-ev");
      ev.appendChild(htmlEl("span", "tt", e.t));
      var who = V.ROSTER.filter(function (r) { return r.name === e.who; })[0];
      var w = htmlEl("span", "tw", e.who);
      if (who) w.style.color = who.color;
      ev.appendChild(w);
      ev.appendChild(document.createTextNode(e.text));
      bar.appendChild(ev);
    });
    return bar;
  }

  function miniRoster(V, snap) {
    var row = htmlEl("div", "mini-roster mono");
    V.ROSTER.forEach(function (a) {
      var chip = htmlEl("span", "chip");
      var dot = htmlEl("span", "dot");
      dot.style.background = a.color;
      var key = a.id === "coord" ? "coord" : a.id === "agent1" ? "agent1" : a.id === "agent2" ? "agent2" : a.id === "guard" ? "guard" : "coord";
      if (snap.leds[key] === "off") dot.style.opacity = "0.35";
      chip.appendChild(dot);
      chip.appendChild(document.createTextNode(a.name + " " + (snap.rosterStatus[a.id] || "idle")));
      row.appendChild(chip);
    });
    return row;
  }

  function buildMonitor(root, V, state, snap, lang) {
    root.appendChild(topbar(V, snap, lang, false));
    var main = htmlEl("div", "main");

    var left = htmlEl("div", "rail");
    left.appendChild(rosterPanel(V, snap, lang));
    left.appendChild(handoffPanel(V, snap, lang));
    left.appendChild(tasksPanel(V, state, lang));
    left.appendChild(ledsPanel(V, snap));
    main.appendChild(left);

    var ring = htmlEl("div", "ringwrap");
    ring.appendChild(buildRing(V, state, snap));
    ring.appendChild(ringCenter(V, state, snap, lang, "monitor"));
    main.appendChild(ring);

    var right = htmlEl("div", "rail");
    right.appendChild(metersPanel(V, lang));
    right.appendChild(riskPanel(V, lang));
    right.appendChild(sectorsPanel(V, lang));
    right.appendChild(voicePanel(V, state, snap, lang));
    main.appendChild(right);

    root.appendChild(main);
    root.appendChild(tapeBar(V, 5, state, lang));
  }

  function buildMini(root, V, state, snap, lang) {
    root.appendChild(topbar(V, snap, lang, true));
    var main = htmlEl("div", "main");
    var ring = htmlEl("div", "ringwrap");
    ring.appendChild(buildRing(V, state, snap));
    ring.appendChild(ringCenter(V, state, snap, lang, "mini"));
    main.appendChild(ring);

    if (state === "approval") main.appendChild(btnRow(lang));

    // No duplicate proposal strip: the ring center already shows the
    // proposal, the fill, or the rejection. Only idle gets the extra
    // Attract lines now live inside the ring center on both screens.
    main.appendChild(miniRoster(V, snap));
    root.appendChild(main);
    root.appendChild(tapeBar(V, 2, state, lang));
  }

  window.V2Render = function (screen, state, lang) {
    var V = window.V2;
    if (!V) return;
    if (V.STATES.indexOf(state) < 0) state = "idle";
    lang = lang === "zh" ? "zh" : "en";
    var snap = V.stateSnapshot(state, lang);
    var root = document.getElementById("screen");
    root.className = screen + " st-" + state + " lang-" + lang;
    root.innerHTML = "";
    if (screen === "mini") buildMini(root, V, state, snap, lang);
    else buildMonitor(root, V, state, snap, lang);
  };
})();
