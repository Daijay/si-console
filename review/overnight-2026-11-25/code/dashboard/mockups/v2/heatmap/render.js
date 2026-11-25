// SI Console UI v2, direction HEATMAP. Static renderer.
// Pure function of window.V2. No fetch, no external resources.
(function () {
  "use strict";

  var V = window.V2;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = text;
    return n;
  }

  function ledDot(id, color, mode) {
    var d = el("span", "led led-" + mode);
    d.style.background = mode === "off" ? "#2a2f38" : color;
    d.title = id;
    return d;
  }

  // Tile fill: dark mix of the move color so white text stays AA.
  function tileStyle(chg) {
    var i = Math.min(Math.abs(chg) / 2.5, 1);
    var mix = 0.10 + 0.30 * i;
    var base = [20, 24, 29];
    var col, bar, val;
    if (chg > 0.05) { col = [46, 204, 113]; bar = "#2ecc71"; val = "#4be38a"; }
    else if (chg < -0.05) { col = [255, 90, 90]; bar = "#ff5a5a"; val = "#ff7a7a"; }
    else { col = [154, 163, 173]; bar = "#9aa3ad"; val = "#c7cdd4"; }
    var fill = "rgb(" + base.map(function (b, k) {
      return Math.round(b + (col[k] - b) * mix);
    }).join(",") + ")";
    return { fill: fill, bar: bar, val: val };
  }

  function stateColor(state) {
    return {
      idle: "#9aa3ad", listening: "#6ee7ff", thinking: "#4aa8ff",
      approval: "#f5c542", approved: "#2ecc71", rejected: "#ff5a5a",
      frozen: "#b48cff", error: "#ff5a5a"
    }[state];
  }

  function chipLine(state, lang) {
    var P = V.PROPOSAL, M = V.METERS, E = V.ERROR;
    switch (state) {
      case "idle": return lang === "zh" ? "对调度说话，按下批准。" : "TALK TO DISPATCH. PRESS TO APPROVE.";
      case "listening": return lang === "zh" ? "按住麦克风按钮" : "HOLD THE MIC BUTTON";
      case "thinking": return "ROUND " + M.roundUsed + " OF " + M.roundMax + "  ·  DEEPSEEK " + M.deepseekMs + "ms";
      case "approval": return P.approvalLeftS + "s LEFT  ·  " + (lang === "zh" ? "按绿色或红色" : "PRESS GREEN OR RED");
      case "approved": return "ORDER FILLED  ·  " + P.action + " " + P.ticker + " " + P.shares + " @ " + P.price.toFixed(2);
      case "rejected": return "HUMAN_REJECT  ·  " + (lang === "zh" ? "正在准备新提议" : "NEW PROPOSAL NEXT");
      case "frozen": return lang === "zh" ? "急停已开启" : "KILL SWITCH ON";
      case "error": return E.code + "  ·  RETRY IN " + E.retryInS + "s";
      default: return "";
    }
  }

  function heatmapEl(snap, compact) {
    var grid = el("div", "heatmap" + (compact ? "" : " heatmap-cols6"));
    if (!compact) {
      grid.appendChild(stateChipEl(snap));
    }
    var sectors = V.SECTORS.slice().sort(function (a, b) { return b.chg - a.chg; });
    sectors.forEach(function (s) {
      var st = tileStyle(s.chg);
      var t = el("div", "tile" + (s.ticker === "XLE" ? " tile-xle" : ""));
      t.style.background = st.fill;
      var bar = el("div", "tile-bar");
      bar.style.background = st.bar;
      t.appendChild(bar);
      var tk = el("div", "tile-ticker", s.ticker);
      t.appendChild(tk);
      if (!compact) {
        t.appendChild(el("div", "tile-name", s.name));
        t.appendChild(el("div", "tile-price", s.price.toFixed(2)));
      }
      var ch = el("div", "tile-chg", V.pct(s.chg));
      ch.style.color = st.val;
      t.appendChild(ch);
      if (s.ticker === "XLE") {
        var tagText = null;
        if (snap.state === "approval") tagText = snap.lang === "zh" ? "提议" : "PROPOSAL";
        else if (snap.state === "approved") tagText = snap.lang === "zh" ? "已成交" : "FILLED";
        if (tagText) {
          var tag = el("div", "tile-tag", tagText);
          t.appendChild(tag);
        }
      }
      grid.appendChild(t);
    });
    // Mini keeps the round counter as the last grid cell.
    if (compact) {
      var rc = el("div", "tile tile-round");
      rc.appendChild(el("div", "tile-round-label", V.label("round", snap.lang)));
      rc.appendChild(el("div", "tile-round-num", V.METERS.roundUsed + " / " + V.METERS.roundMax));
      grid.appendChild(rc);
    }
    return grid;
  }

  function voiceRingEl(snap, compact) {
    var wrap = el("div", "panel voice");
    wrap.appendChild(el("div", "panel-title", V.label("voice", snap.lang)));
    var active = snap.state === "listening";
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 200 200");
    svg.setAttribute("class", "ring");
    var c = 2 * Math.PI * 84;
    var bg = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    bg.setAttribute("cx", "100"); bg.setAttribute("cy", "100"); bg.setAttribute("r", "84");
    bg.setAttribute("class", "ring-bg");
    svg.appendChild(bg);
    var arc = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    arc.setAttribute("cx", "100"); arc.setAttribute("cy", "100"); arc.setAttribute("r", "84");
    arc.setAttribute("class", "ring-arc" + (active ? " ring-arc-on" : ""));
    arc.setAttribute("stroke-dasharray", (active ? c * 0.72 : c * 0.18) + " " + c);
    svg.appendChild(arc);
    var mid = document.createElementNS("http://www.w3.org/2000/svg", "text");
    mid.setAttribute("x", "100"); mid.setAttribute("y", "96");
    mid.setAttribute("class", "ring-mid");
    mid.textContent = active ? "MIC" : "IDLE";
    svg.appendChild(mid);
    var sub = document.createElementNS("http://www.w3.org/2000/svg", "text");
    sub.setAttribute("x", "100"); sub.setAttribute("y", "122");
    sub.setAttribute("class", "ring-sub");
    sub.textContent = active ? "LISTENING" : "PUSH TO TALK";
    svg.appendChild(sub);
    wrap.appendChild(svg);
    var bars = el("div", "wave");
    V.WAVEFORM.forEach(function (v) {
      var b = el("div", "wave-bar" + (active ? " wave-on" : ""));
      b.style.height = Math.max(4, Math.round(v * (compact ? 0.28 : 0.5))) + "px";
      bars.appendChild(b);
    });
    wrap.appendChild(bars);
    return wrap;
  }

  function meterRow(label, value, frac, cls) {
    var r = el("div", "meter-row");
    r.appendChild(el("span", "meter-label", label));
    var bar = el("div", "meter-bar");
    var fill = el("div", "meter-fill" + (cls ? " " + cls : ""));
    fill.style.width = Math.round(frac * 100) + "%";
    bar.appendChild(fill);
    r.appendChild(bar);
    r.appendChild(el("span", "meter-value", value));
    return r;
  }

  function rightColEl(snap) {
    var col = el("div", "rightcol");
    col.appendChild(voiceRingEl(snap, false));
    var meters = el("div", "panel meters");
    meters.appendChild(el("div", "panel-title", V.label("meters", snap.lang)));
    meters.appendChild(meterRow("DEEPSEEK", V.METERS.deepseekMs + "ms", V.METERS.deepseekMs / 3000, ""));
    meters.appendChild(meterRow("BOCHA", V.METERS.bochaMs + "ms", V.METERS.bochaMs / 3000, ""));
    meters.appendChild(meterRow("TOKENS IN", String(V.METERS.tokensIn), V.METERS.tokensIn / 4000, ""));
    meters.appendChild(meterRow("TOKENS OUT", String(V.METERS.tokensOut), V.METERS.tokensOut / 1000, ""));
    var model = el("div", "meter-model", V.METERS.deepseekModel + "  ·  " + V.METERS.apiStatus.toUpperCase());
    meters.appendChild(model);
    col.appendChild(meters);
    var cost = el("div", "panel cost");
    cost.appendChild(el("div", "panel-title", V.label("portfolio", snap.lang)));
    var sc = V.SCENARIO;
    var pv = el("div", "cost-value", V.money(sc.portfolioValue));
    cost.appendChild(pv);
    var day = el("div", "cost-day", "DAY " + V.money(sc.portfolioDay) + " (" + V.pct(sc.portfolioDayPct) + ")");
    day.style.color = sc.portfolioDay < 0 ? "#ff7a7a" : "#4be38a";
    cost.appendChild(day);
    cost.appendChild(el("div", "cost-cash", "CASH " + V.money(V.cashForState(snap.state))));
    cost.appendChild(meterRow("API COST", "$" + V.METERS.costTodayUsd.toFixed(2) + " / $" + V.METERS.costCapUsd.toFixed(2),
      V.METERS.costTodayUsd / V.METERS.costCapUsd, "cost-fill"));
    col.appendChild(cost);
    var risk = el("div", "panel risk");
    risk.appendChild(el("div", "panel-title", V.label("risk", snap.lang)));
    risk.appendChild(riskGaugeEl(false));
    col.appendChild(risk);
    var tasks = el("div", "panel tasks");
    tasks.appendChild(el("div", "panel-title", V.label("taskQueue", snap.lang)));
    V.tasksForState(snap.state).forEach(function (t) {
      var row = el("div", "task-row");
      row.appendChild(el("span", "task-id", t.id));
      row.appendChild(el("span", "task-type", t.type));
      row.appendChild(el("span", "task-ticker", t.ticker || "-"));
      row.appendChild(el("span", "task-amt", t.amount ? V.money(t.amount) : "-"));
      var st = el("span", "task-status task-" + t.status, t.status.toUpperCase());
      row.appendChild(st);
      tasks.appendChild(row);
    });
    col.appendChild(tasks);
    return col;
  }

  function riskGaugeEl(big) {
    var g = el("div", "risk-gauge" + (big ? " risk-big" : ""));
    var P = V.PROPOSAL;
    var head = el("div", "risk-head");
    head.appendChild(el("span", "risk-score", "RISK " + P.riskScore));
    head.appendChild(el("span", "risk-label", P.riskLabel + "  ·  CHECK " + P.riskCheck.toUpperCase()));
    g.appendChild(head);
    var bar = el("div", "risk-bar");
    ["risk-zone-low", "risk-zone-med", "risk-zone-high"].forEach(function (z) {
      bar.appendChild(el("div", "risk-zone " + z));
    });
    var mark = el("div", "risk-mark");
    mark.style.left = P.riskScore + "%";
    bar.appendChild(mark);
    g.appendChild(bar);
    var cap = el("div", "risk-cap", "CAP " + P.capUsedPct.toFixed(1) + "% OF " + P.capMaxPct.toFixed(1) + "%  ·  " +
      P.action + " " + P.ticker + " " + P.shares + " @ " + P.price.toFixed(2) + "  ·  " + V.money(P.amount));
    g.appendChild(cap);
    return g;
  }

  function rosterStripEl(snap) {
    var strip = el("div", "roster");
    strip.appendChild(el("div", "panel-title", V.label("agents", snap.lang)));
    var chain = el("div", "chain");
    V.ROSTER.forEach(function (a, i) {
      if (i > 0) chain.appendChild(el("span", "chain-arrow", "->"));
      var chip = el("div", "agent-chip");
      var st = snap.rosterStatus[a.id];
      var active = st === "working" || st === "routing" || st === "listening" || st === "checking";
      if (active) chip.classList.add("agent-active");
      if (st === "frozen" || st === "offline") chip.classList.add("agent-dead");
      var dot = el("span", "agent-dot");
      dot.style.background = a.color;
      chip.appendChild(dot);
      chip.appendChild(el("span", "agent-name", a.name));
      chip.appendChild(el("span", "agent-status", st.toUpperCase()));
      chain.appendChild(chip);
    });
    strip.appendChild(chain);
    return strip;
  }

  function tapeEl(snap) {
    var t = el("div", "tape");
    t.appendChild(el("div", "panel-title", V.label("tape", snap.lang)));
    var lines = el("div", "tape-lines");
    V.tapeForState(snap.state).slice(-4).forEach(function (e) {
      var row = el("div", "tape-row");
      row.appendChild(el("span", "tape-time", e.t));
      row.appendChild(el("span", "tape-who", e.who));
      row.appendChild(el("span", "tape-text", e.text));
      lines.appendChild(row);
    });
    t.appendChild(lines);
    return t;
  }

  function headerEl(snap, compact) {
    var h = el("div", "header");
    var left = el("div", "header-left");
    left.appendChild(el("span", "brand", "SI CONSOLE"));
    left.appendChild(el("span", "header-sep", "|"));
    left.appendChild(el("span", "header-mode", compact ? "BOOTH · 2022" : "BOOTH  ·  REPLAY " + V.SCENARIO.replay + "  ·  WEEK " + V.SCENARIO.replayWeek));
    h.appendChild(left);
    var right = el("div", "header-right");
    right.appendChild(el("span", "round-tag", snap.lang === "zh" ? "回合 " + V.METERS.roundUsed + "/" + V.METERS.roundMax :
      (compact ? "RND " + V.METERS.roundUsed + "/" + V.METERS.roundMax : "ROUND " + V.METERS.roundUsed + "/" + V.METERS.roundMax)));
    var leds = el("div", "leds");
    var ledNames = compact ? ["COORD", "A1", "A2", "GUARD"] : ["COORD", "AGENT 1", "AGENT 2", "GUARD"];
    [["COORD", "#2ecc71", snap.leds.coord], ["AGENT 1", "#e8ecf1", snap.leds.agent1],
     ["AGENT 2", "#4aa8ff", snap.leds.agent2], ["GUARD", "#f5c542", snap.leds.guard]].forEach(function (l, i) {
      var item = el("span", "led-item");
      item.appendChild(ledDot(l[0], l[1], l[2]));
      item.appendChild(el("span", "led-name", ledNames[i]));
      leds.appendChild(item);
    });
    right.appendChild(leds);
    var langTag = el("span", "lang-tag", compact ? "EN/中文" : (snap.lang === "zh" ? "中文" : "EN / 中文"));
    right.appendChild(langTag);
    h.appendChild(right);
    return h;
  }

  function tileExtraEl(snap) {
    var P = V.PROPOSAL;
    switch (snap.state) {
      case "idle":
        return el("div", "state-extra", V.ATTRACT.line3);
      case "listening": {
        var w = el("div", "wave state-wave");
        V.WAVEFORM.forEach(function (v) {
          var b = el("div", "wave-bar wave-on");
          b.style.height = Math.max(4, Math.round(v * 0.5)) + "px";
          w.appendChild(b);
        });
        return w;
      }
      case "thinking":
        return el("div", "state-extra", "TOOL run_rules_engine · XLE");
      case "approval":
        return el("div", "state-extra", P.action + " " + P.ticker + " " + P.shares + " @ " + P.price.toFixed(2) + " · " + V.money(P.amount));
      case "approved":
        return el("div", "state-extra", "CASH " + V.money(V.SCENARIO.cash - P.amount) + " AFTER FILL");
      case "rejected":
        return el("div", "state-extra", "ORDER " + P.taskId + " · HUMAN_REJECT");
      case "frozen":
        return el("div", "state-extra", snap.strings.press_green_to_resume);
      case "error":
        return el("div", "state-extra", "RECORDED FALLBACK READY");
      default:
        return null;
    }
  }

  function stateChipEl(snap) {
    // In-flow grid tile, 2x2, top-left. Never covers a sector tile.
    var chip = el("div", "tile tile-state");
    chip.style.borderColor = stateColor(snap.state);
    var w = el("div", "state-word", snap.word);
    w.style.color = stateColor(snap.state);
    chip.appendChild(w);
    chip.appendChild(el("div", "state-line", chipLine(snap.state, snap.lang)));
    var extra = tileExtraEl(snap);
    if (extra) chip.appendChild(extra);
    return chip;
  }

  function approvalCardEl(snap, compact) {
    var P = V.PROPOSAL;
    var card = el("div", "overlay-card approval-card");
    // Compact (mini) skips the word and sentence: the mini screen
    // already shows both above and below the card.
    if (!compact) {
      card.appendChild(el("div", "overlay-word", snap.word));
    }
    var prop = el("div", "prop-line", P.action + " " + P.ticker + "  ·  " + P.shares + " SHARES @ " + P.price.toFixed(2) + "  ·  " + V.money(P.amount));
    card.appendChild(prop);
    card.appendChild(riskGaugeEl(true));
    var cd = el("div", "countdown");
    cd.appendChild(el("span", "countdown-num", P.approvalLeftS + "s"));
    cd.appendChild(el("span", "countdown-of", "LEFT OF " + P.approvalExpiresS + "s"));
    var cdBar = el("div", "countdown-bar");
    var cdFill = el("div", "countdown-fill");
    cdFill.style.width = Math.round(P.approvalLeftS / P.approvalExpiresS * 100) + "%";
    cdBar.appendChild(cdFill);
    cd.appendChild(cdBar);
    card.appendChild(cd);
    var btns = el("div", "btn-row");
    var g = el("div", "btn btn-green", snap.lang === "zh" ? "按绿色 — 批准" : "PRESS GREEN — APPROVE");
    var r = el("div", "btn btn-red", snap.lang === "zh" ? "按红色 — 拒绝" : "PRESS RED — REJECT");
    btns.appendChild(g); btns.appendChild(r);
    card.appendChild(btns);
    if (!compact) {
      card.appendChild(el("div", "sentence", snap.sentence));
    }
    return card;
  }

  function overlayEl(snap, kind) {
    var ov = el("div", "overlay");
    var card = el("div", "overlay-card");
    if (kind === "frozen") {
      card.appendChild(el("div", "overlay-word frozen-word", snap.word));
      card.appendChild(el("div", "overlay-msg", snap.sentence));
      card.appendChild(el("div", "overlay-sub", snap.strings.press_green_to_resume));
      card.appendChild(el("div", "overlay-sub2", "ALL AGENTS FROZEN  ·  COORD / AGENT 1 / AGENT 2 / GUARD"));
    } else if (kind === "error") {
      card.appendChild(el("div", "overlay-word error-word", snap.word));
      card.appendChild(el("div", "overlay-code", V.ERROR.code));
      card.appendChild(el("div", "overlay-msg", V.ERROR.text));
      card.appendChild(el("div", "overlay-sub", "RETRY IN " + V.ERROR.retryInS + "s  ·  RECORDED FALLBACK READY  ·  LAST OK " + V.ERROR.lastOk));
      card.appendChild(el("div", "overlay-sub2", "GUARD STILL WATCHING"));
    } else if (kind === "rejected") {
      card.appendChild(el("div", "overlay-word rejected-word", snap.word));
      var prop = el("div", "prop-line prop-struck", V.PROPOSAL.action + " " + V.PROPOSAL.ticker + "  ·  " +
        V.PROPOSAL.shares + " SHARES @ " + V.PROPOSAL.price.toFixed(2) + "  ·  " + V.money(V.PROPOSAL.amount));
      card.appendChild(prop);
      card.appendChild(el("div", "overlay-msg", "TASK " + V.PROPOSAL.taskId + " BLOCKED  ·  HUMAN_REJECT"));
      card.appendChild(el("div", "overlay-sub", snap.sentence));
      card.appendChild(el("div", "overlay-sub2", "COORD ROUTING A NEW PROPOSAL"));
    } else if (kind === "approved") {
      card.appendChild(el("div", "overlay-word approved-word", snap.word));
      var prop2 = el("div", "prop-line", V.PROPOSAL.action + " " + V.PROPOSAL.ticker + "  ·  " +
        V.PROPOSAL.shares + " SHARES @ " + V.PROPOSAL.price.toFixed(2) + "  ·  " + V.money(V.PROPOSAL.amount));
      card.appendChild(prop2);
      card.appendChild(el("div", "overlay-msg", "ORDER FILLED  ·  PORTFOLIO " + V.money(V.SCENARIO.portfolioValue)));
      card.appendChild(el("div", "overlay-sub", snap.sentence));
      card.appendChild(el("div", "overlay-sub2", "AGENT 2 WORKING  ·  NEXT: WEEKLY SCAN sig-0144"));
    }
    ov.appendChild(card);
    return ov;
  }

  function dimHeat(root) {
    var hm = root.querySelector(".heatmap-wrap");
    if (hm) hm.classList.add("dim");
  }

  function renderMonitor(root, snap) {
    var sc = V.SCENARIO;
    root.className = "screen monitor state-" + snap.state;
    root.appendChild(headerEl(snap, false));
    var main = el("div", "main");
    var hmWrap = el("div", "heatmap-wrap");
    hmWrap.appendChild(heatmapEl(snap, false));
    main.appendChild(hmWrap);
    main.appendChild(rightColEl(snap));
    root.appendChild(main);
    var bottom = el("div", "bottom");
    bottom.appendChild(rosterStripEl(snap));
    bottom.appendChild(tapeEl(snap));
    var pl = el("div", "pl-strip");
    pl.appendChild(el("span", "pl-item", "PORTFOLIO " + V.money(sc.portfolioValue)));
    var day = el("span", "pl-item", "DAY " + V.money(sc.portfolioDay) + " (" + V.pct(sc.portfolioDayPct) + ")");
    day.style.color = "#ff7a7a";
    pl.appendChild(day);
    pl.appendChild(el("span", "pl-item", "COST TODAY $" + V.METERS.costTodayUsd.toFixed(2) + " / $" + V.METERS.costCapUsd.toFixed(2)));
    pl.appendChild(el("span", "pl-item pl-sentence", snap.sentence));
    bottom.appendChild(pl);
    root.appendChild(bottom);
    if (snap.state === "approval") {
      dimHeat(root);
      var ov = el("div", "overlay");
      ov.appendChild(approvalCardEl(snap, false));
      root.appendChild(ov);
    } else if (snap.state === "frozen") {
      dimHeat(root);
      root.appendChild(overlayEl(snap, "frozen"));
    } else if (snap.state === "error") {
      dimHeat(root);
      root.appendChild(overlayEl(snap, "error"));
    } else if (snap.state === "rejected") {
      dimHeat(root);
      root.appendChild(overlayEl(snap, "rejected"));
    } else if (snap.state === "approved") {
      root.appendChild(overlayEl(snap, "approved"));
    }
  }

  function renderMini(root, snap) {
    var sc = V.SCENARIO;
    root.className = "screen mini state-" + snap.state;
    root.appendChild(headerEl(snap, true));
    var word = el("div", "mini-word", snap.word);
    word.style.color = stateColor(snap.state);
    root.appendChild(word);
    root.appendChild(el("div", "mini-line", chipLine(snap.state, snap.lang)));
    var hero = el("div", "mini-hero");
    if (snap.state === "listening") {
      hero.appendChild(voiceRingEl(snap, true));
    } else if (snap.state === "approval") {
      hero.appendChild(approvalCardEl(snap, true));
    } else if (snap.state === "frozen") {
      var fz = el("div", "mini-msg");
      fz.appendChild(el("div", "mini-msg-big", snap.sentence));
      fz.appendChild(el("div", "mini-msg-sub", snap.strings.press_green_to_resume));
      hero.appendChild(fz);
    } else if (snap.state === "error") {
      var er = el("div", "mini-msg");
      er.appendChild(el("div", "mini-msg-big", V.ERROR.code));
      er.appendChild(el("div", "mini-msg-sub", V.ERROR.text));
      er.appendChild(el("div", "mini-msg-sub", "RETRY IN " + V.ERROR.retryInS + "s  ·  FALLBACK READY"));
      hero.appendChild(er);
    } else if (snap.state === "rejected") {
      var rj = el("div", "mini-msg");
      rj.appendChild(el("div", "mini-msg-big", snap.sentence));
      rj.appendChild(el("div", "mini-msg-sub", "TASK " + V.PROPOSAL.taskId + " BLOCKED  ·  HUMAN_REJECT"));
      hero.appendChild(rj);
    } else if (snap.state === "approved") {
      var ap = el("div", "mini-msg");
      ap.appendChild(el("div", "mini-msg-big", snap.sentence));
      ap.appendChild(el("div", "mini-msg-sub", V.PROPOSAL.action + " " + V.PROPOSAL.ticker + " " +
        V.PROPOSAL.shares + " @ " + V.PROPOSAL.price.toFixed(2) + "  ·  FILLED"));
      hero.appendChild(ap);
    } else {
      hero.appendChild(heatmapEl(snap, true));
    }
    root.appendChild(hero);
    // Frozen, error, rejected and approved already show the sentence
    // inside their message panel. Showing it again here duplicates it.
    var noSentence = { frozen: 1, error: 1, rejected: 1, approved: 1 };
    if (!noSentence[snap.state]) {
      root.appendChild(el("div", "mini-sentence", snap.sentence));
    }
    var foot = el("div", "mini-foot");
    foot.appendChild(el("span", "mini-foot-item", "PORTFOLIO " + V.money(sc.portfolioValue)));
    var day = el("span", "mini-foot-item", "DAY " + V.pct(sc.portfolioDayPct));
    day.style.color = "#ff7a7a";
    foot.appendChild(day);
    foot.appendChild(el("span", "mini-foot-item", "COST $" + V.METERS.costTodayUsd.toFixed(2) + "/$" + V.METERS.costCapUsd.toFixed(2)));
    foot.appendChild(el("span", "mini-foot-item", "ROUND " + V.METERS.roundUsed + "/" + V.METERS.roundMax));
    root.appendChild(foot);
    var roster = el("div", "mini-roster");
    V.ROSTER.forEach(function (a) {
      var st = snap.rosterStatus[a.id];
      var chip = el("span", "mini-agent");
      var dot = el("span", "agent-dot");
      dot.style.background = st === "frozen" || st === "offline" ? "#2a2f38" : a.color;
      chip.appendChild(dot);
      chip.appendChild(el("span", "mini-agent-name", a.name));
      chip.appendChild(el("span", "mini-agent-status", st.toUpperCase()));
      roster.appendChild(chip);
    });
    root.appendChild(roster);
  }

  window.V2Render = function (screen, state, lang) {
    var root = document.getElementById("screen");
    var snap = V.stateSnapshot(state, lang);
    root.innerHTML = "";
    if (screen === "mini") renderMini(root, snap);
    else renderMonitor(root, snap);
  };
})();
