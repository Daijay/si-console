/* SI Console UI v2, direction: ORDERBOOK.
   Pure function of window.V2. Builds both screens for all 8 states.
   window.V2Render(screen, state, lang). No external resources. */
(function () {
  "use strict";

  var LED_COLORS = { coord: "#2ecc71", agent1: "#e8ecf1", agent2: "#4aa8ff", guard: "#f5c542" };
  var LED_LABELS = { coord: "COORD", agent1: "AGENT 1", agent2: "AGENT 2", guard: "GUARD" };
  var STATE_COLOR = {
    idle: "white", listening: "blue", thinking: "white", approval: "yellow",
    approved: "green", rejected: "red", frozen: "red", error: "red"
  };
  var MAX_AMOUNT = 12500;

  function ledsHtml(snap) {
    var out = "";
    ["coord", "agent1", "agent2", "guard"].forEach(function (k) {
      out += '<span class="led ' + snap.leds[k] + '" style="--c:' + LED_COLORS[k] + '"></span>' + LED_LABELS[k];
    });
    return out;
  }

  function ledDots(snap) {
    var out = "";
    ["coord", "agent1", "agent2", "guard"].forEach(function (k) {
      out += '<div><span class="led ' + snap.leds[k] + '" style="--c:' + LED_COLORS[k] + '"></span>' + LED_LABELS[k] + '</div>';
    });
    return out;
  }

  function waveHtml(active) {
    var cls = active ? "wave" : "wave idle";
    var bars = V2.WAVEFORM.map(function (v) {
      return '<span style="height:' + v + '%"></span>';
    }).join("");
    return '<div class="' + cls + '">' + bars + "</div>";
  }

  function polar(cx, cy, r, deg) {
    var a = deg * Math.PI / 180;
    return [cx + r * Math.cos(a), cy - r * Math.sin(a)];
  }
  function arcPath(cx, cy, r, a0, a1) {
    var p0 = polar(cx, cy, r, a0), p1 = polar(cx, cy, r, a1);
    return "M" + p0[0].toFixed(1) + "," + p0[1].toFixed(1) +
      " A" + r + "," + r + " 0 0 1 " + p1[0].toFixed(1) + "," + p1[1].toFixed(1);
  }
  // Semicircle gauge, 0 left, 100 right. Green 0-40, yellow 40-70, red 70-100.
  function gaugeSvg(score, label, w) {
    w = w || 220;
    var h = Math.round(w * 0.68);
    var cx = w / 2, cy = h - 40, r = w / 2 - 14;
    function seg(a0, a1, color) {
      return '<path d="' + arcPath(cx, cy, r, a0, a1) + '" fill="none" stroke="' + color +
        '" stroke-width="13" stroke-linecap="butt"/>';
    }
    var ang = 180 - score * 1.8;
    var tip = polar(cx, cy, r - 16, ang);
    var needle = '<line x1="' + cx + '" y1="' + cy + '" x2="' + tip[0].toFixed(1) +
      '" y2="' + tip[1].toFixed(1) + '" stroke="#e8ecf1" stroke-width="3"/>' +
      '<circle cx="' + cx + '" cy="' + cy + '" r="6" fill="#e8ecf1"/>';
    return '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '">' +
      seg(180, 108, "#2ecc71") + seg(108, 54, "#f5c542") + seg(54, 0, "#ff5a5a") + needle +
      '<text x="' + cx + '" y="' + (cy - 30) + '" fill="#e8ecf1" font-size="34" font-weight="700" text-anchor="middle" font-family="monospace">' + score + "</text>" +
      '<text x="' + cx + '" y="' + (cy + 22) + '" fill="#f5c542" font-size="15" font-weight="700" text-anchor="middle">' + label + "</text>" +
      '<text x="12" y="' + (cy + 36) + '" fill="#9aa3b0" font-size="12">0</text>' +
      '<text x="' + (w - 12) + '" y="' + (cy + 36) + '" fill="#9aa3b0" font-size="12" text-anchor="end">100</text>' +
      "</svg>";
  }

  function capBar(used, max) {
    var pctW = Math.round(used / max * 100);
    return '<div class="bar-track" style="margin-top:6px"><div class="bar-fill yellow" style="width:' + pctW + '%"></div></div>' +
      '<div class="muted" style="font-size:14px;margin-top:4px">CAP ' + used.toFixed(1) + "% OF " + max.toFixed(1) + "%</div>";
  }

  var AGENT_SHORT = { coordinator: "COORD", signal: "SIGNAL", risk: "RISK", execution: "EXEC" };

  function bookRows(state, mini, lang) {
    var rows = "";
    var groups = [[V2.label("fills", lang), ["done", "working"]], [V2.label("bids", lang), ["queued"]]];
    // Mini is 800x480: only the FILLS group fits under the hero.
    if (mini) groups = groups.slice(0, 1);
    groups.forEach(function (g) {
      var label = g[0], wanted = g[1];
      var items = V2.TASKS.filter(function (t) { return wanted.indexOf(t.status) >= 0; });
      if (!items.length) return;
      if (!mini) rows += '<div class="book-group">' + label + "</div>";
      items.forEach(function (t) {
        var status = t.status;
        var displayStatus = status.toUpperCase();
        var strike = "";
        var note = t.note;
        if (state === "rejected" && t.id === "ord-0142") {
          status = "blocked";
          displayStatus = "BLOCKED";
          strike = " strike";
          note = "rejected by human";
        }
        if (state === "approved" && t.id === "ord-0142") {
          status = "done";
          displayStatus = "FILLED";
          note = "filled 11:42:21";
        }
        if (state === "frozen" && t.id === "ord-0142") {
          status = "blocked";
          displayStatus = "BLOCKED";
          strike = " strike";
          note = "blocked KILL_SWITCH";
        }
        var depthW = t.amount > 0 ? Math.max(6, Math.round(t.amount / MAX_AMOUNT * 100)) : 0;
        var amount = t.amount > 0 ? V2.money(t.amount) : "-";
        var ticker = t.ticker || "-";
        if (mini) {
          rows += '<div class="book-row ' + status + '"><span class="depth" style="width:' + depthW + '%"></span>' +
            '<span class="mono">' + t.id + "</span><span class=\"mono" + strike + '">' + ticker + "</span>" +
            '<span class="mono' + strike + '">' + amount + "</span><span>" + displayStatus + "</span></div>";
        } else {
          rows += '<div class="book-row ' + status + '"><span class="depth" style="width:' + depthW + '%"></span>' +
            '<span class="mono">' + t.id + '</span><span>' + (AGENT_SHORT[t.agent] || t.agent.toUpperCase()) + "</span><span>" + t.type.toUpperCase() + "</span>" +
            '<span class="mono' + strike + '">' + ticker + '</span><span class="mono' + strike + '">' + amount + "</span>" +
            "<span class=\"mono\">R" + t.round + "</span><span>" + t.risk.toUpperCase() + "</span>" +
            '<span class="muted">' + note + "</span></div>";
        }
      });
    });
    return rows;
  }

  function sectorBookHtml(lang) {
    var rows = V2.SECTORS.map(function (s) {
      var up = s.chg >= 0;
      var w = Math.min(100, Math.round(Math.abs(s.chg) / 2.5 * 100));
      return '<div class="sector-row"><span class="mono"><b>' + s.ticker + "</b></span><span>" + s.name.toUpperCase() +
        '</span><span class="mono">' + s.price.toFixed(2) + '</span><span class="mono ' + (up ? "green" : "red") + '">' + V2.pct(s.chg) + "</span>" +
        '<span class="bar-track" style="display:block"><span class="bar-fill ' + (up ? "" : "red") + '" style="display:block;width:' + w + '%"></span></span></div>';
    }).join("");
    return '<div class="sector-head"><span class="book-title" style="font-size:16px">' + V2.label("sectors", lang) + " &mdash; 11 ETFS</span>" +
      '<span class="panel-h">WEEK ' + V2.SCENARIO.replayWeek + "</span></div>" +
      '<div class="sector-cols"><span>TICKER</span><span>SECTOR</span><span>PRICE</span><span>CHANGE</span><span>MOMENTUM</span></div>' + rows;
  }

  function tapeHtml(state, n, lang) {
    var items = V2.tapeForState(state).slice(-n);
    var out = '<div class="tape-label">' + V2.label("tape", lang) + "</div>";
    return out + items.map(function (e) {
      return '<div><span class="muted mono">' + e.t + '</span> <b>' + e.who + "</b> " + e.text + "</div>";
    }).join("");
  }

  function rosterHtml(snap) {
    return V2.ROSTER.map(function (a) {
      var st = snap.rosterStatus[a.id] || "idle";
      var dot = LED_COLORS[a.id] ? '<span class="led on" style="--c:' + LED_COLORS[a.id] + '"></span>' : '<span class="led on" style="--c:#b48cff"></span>';
      // COORD has tier "coordinator" and role "coordinator". Showing
      // both repeats the word, so hide the tier when it equals the role.
      var tier = a.tier.toUpperCase() === a.role.toUpperCase() ? "—" : a.tier.toUpperCase();
      return '<div class="roster-row">' + dot + a.name + "<span>" + a.role.toUpperCase() + "</span><span>" + st.toUpperCase() + '</span><span class="muted">' + tier + "</span></div>";
    }).join("");
  }

  function pnlLine(state) {
    var s = V2.SCENARIO, m = V2.METERS;
    return "PF " + V2.money(s.portfolioValue) + " &nbsp; DAY " + V2.signed(s.portfolioDay) + " (" + V2.pct(s.portfolioDayPct) +
      ") &nbsp; CASH " + V2.money(V2.cashForState(state)) + " &nbsp; COST $" + m.costTodayUsd.toFixed(2) + " / $" + m.costCapUsd.toFixed(2);
  }

  function proposalBlock() {
    var p = V2.PROPOSAL;
    return '<div class="mono" style="font-size:20px">' + p.taskId.toUpperCase() + " &middot; " + p.action + " " + p.ticker +
      " &middot; " + p.shares + " SHARES @ " + p.price.toFixed(2) + " &middot; " + V2.money(p.amount) + "</div>" +
      '<div style="font-size:16px;margin-top:4px">RISK CHECK <b class="green">PASS</b> &middot; CAP ' + p.capUsedPct.toFixed(1) + "% OF " + p.capMaxPct.toFixed(1) + "%</div>";
  }

  function approveBtns(lang) {
    var zh = lang === "zh";
    return '<div class="btn-row"><div class="btn-green">' + (zh ? "绿色 &mdash; 批准" : "GREEN &mdash; APPROVE") +
      '</div><div class="btn-red">' + (zh ? "红色 &mdash; 拒绝" : "RED &mdash; REJECT") + "</div></div>";
  }

  /* ---------------- monitor hero per state ---------------- */
  function monitorHero(state, snap) {
    var p = V2.PROPOSAL, m = V2.METERS, s = V2.SCENARIO;
    var word = '<div class="state-word ' + STATE_COLOR[state] + '">' + snap.word + "</div>";
    var sent = '<div class="sentence">' + snap.sentence + "</div>";
    if (state === "idle") {
      return '<div class="attract1">' + V2.ATTRACT.line1 + '</div><div class="attract2">' + V2.ATTRACT.line2 + '</div>' +
        '<div class="attract3">' + V2.ATTRACT.line3 + "</div>" +
        '<div class="sub" style="margin-top:16px">MODE BOOTH &middot; REPLAY ' + s.replay + " &middot; WEEK " + s.replayWeek + "</div>" +
        '<div class="tiles">' + ["XLE", "XLU", "XLK", "XLY"].map(function (tk) {
          var sec = V2.SECTORS.filter(function (x) { return x.ticker === tk; })[0];
          return '<div class="tile"><div class="t">' + sec.ticker + " &middot; " + sec.name.toUpperCase() + '</div><div class="v mono ' + (sec.chg >= 0 ? "green" : "red") + '">' + V2.pct(sec.chg) + "</div></div>";
        }).join("") + "</div>" +
        '<div class="steps"><b>1</b> HOLD THE MIC BUTTON AND SPEAK &nbsp; <b>2</b> AGENTS WORK &nbsp; <b>3</b> YOU PRESS GREEN TO APPROVE</div>';
    }
    if (state === "listening") {
      return word + sent + waveHtml(true) +
        '<div class="sub">MIC LIVE &middot; PUSH TO TALK &middot; ' + snap.sentenceId.toUpperCase() + "</div>" +
        '<div class="steps">VOICE PIPELINE: MIC FIFINE AM8 &middot; STT SENSEVOICE SMALL (OFFLINE) &middot; TTS PIPER<br>LANG EN &middot; SAY IT AGAIN IF THE CONSOLE DOES NOT UNDERSTAND</div>' +
        '<div class="steps">TRY SAYING: &ldquo;STATUS&rdquo; &middot; &ldquo;PORTFOLIO VALUE&rdquo; &middot; &ldquo;SWITCH TO CHINESE&rdquo;<br>FIXED VOCABULARY ONLY &middot; ANYTHING ELSE GETS &ldquo;I DID NOT UNDERSTAND&rdquo;</div>';
    }
    if (state === "thinking") {
      return word + sent +
        '<div class="meter-row"><span>AGENT 1 &middot; RULES</span><div class="bar-track"><div class="bar-fill" style="width:61%"></div></div><span class="mono">1840ms</span></div>' +
        '<div class="meter-row"><span>BOCHA SEARCH</span><div class="bar-track"><div class="bar-fill" style="width:21%"></div></div><span class="mono">620ms</span></div>' +
        '<div class="meter-row"><span>TOKENS IN / OUT</span><div class="bar-track"><div class="bar-fill yellow" style="width:46%"></div></div><span class="mono">1842/317</span></div>' +
        '<div class="sub">ROUND ' + m.roundUsed + " OF " + m.roundMax + " &middot; MODEL " + m.deepseekModel.toUpperCase() + "</div>" +
        '<div class="mini-tape">' + tapeHtml(state, 3, snap.lang) + "</div>";
    }
    if (state === "approval") {
      return word + sent +
        '<div class="gauge-row">' + gaugeSvg(p.riskScore, p.riskLabel, 280) +
        '<div class="gauge-cap">' + proposalBlock() +
        '<div style="margin-top:10px"><span class="big-num yellow mono">' + p.approvalLeftS + 's</span><span style="font-size:17px"> LEFT OF ' + p.approvalExpiresS + "s</span></div>" +
        capBar(p.capUsedPct, p.capMaxPct) + "</div></div>" +
        approveBtns(snap.lang) +
        '<div class="steps">TYPE MARKET &middot; TIF DAY &middot; VENUE PAPER REPLAY<br>GUARD: KILL OFF &middot; RISK PASS &middot; APPROVED_BY HUMAN &mdash; PENDING</div>' +
        '<div class="hero-foot">IF GREEN: FILL 141 XLE &middot; ORD-0142 DONE &middot; CASH ' + V2.money(s.cash - p.amount) +
        '<br>WHY NOW: XLE ' + V2.pct(V2.SECTORS[0].chg) + " &middot; RRG LEADING &middot; XLU " + V2.pct(V2.SECTORS[1].chg) + " &middot; XLK " + V2.pct(V2.SECTORS[7].chg) + "</div>";
    }
    if (state === "approved") {
      return word + sent +
        '<div style="margin-top:10px">' + proposalBlock() + "</div>" +
        '<div class="sub">FILLED ' + V2.money(p.amount) + " " + p.ticker + " &middot; CASH NOW " + V2.money(s.cash - p.amount) + "</div>" +
        '<div class="sub">AGENT 2 WORKING &middot; NEXT RISK CHECK &middot; ROUND ' + m.roundUsed + " OF " + m.roundMax + "</div>" +
        '<div class="ticket">' +
        '<div><div class="t">SIDE</div><div class="v green">BUY</div></div>' +
        '<div><div class="t">SHARES</div><div class="v mono">141</div></div>' +
        '<div><div class="t">PRICE</div><div class="v mono">88.42</div></div>' +
        '<div><div class="t">AMOUNT</div><div class="v mono">' + V2.money(p.amount) + '</div></div>' +
        '<div><div class="t">FILLED</div><div class="v mono">11:42:21</div></div>' +
        '<div><div class="t">RISK</div><div class="v">23 LOW</div></div>' +
        "</div>" +
        '<div class="steps">POSITION: XLE 141 SHARES @ 88.42 &middot; VALUE ' + V2.money(p.shares * p.price) + "<br>PORTFOLIO: CASH " + V2.money(s.cash - p.amount) + " + POSITIONS " + V2.money(s.portfolioValue - s.cash + p.amount) + " = " + V2.money(s.portfolioValue) + "</div>";
    }
    if (state === "rejected") {
      return word + sent +
        '<div style="margin-top:10px"><span class="mono" style="font-size:20px;text-decoration:line-through">' + p.action + " " + p.ticker + " " + V2.money(p.amount) + "</span></div>" +
        '<div class="sub" style="color:#ff5a5a">HUMAN_REJECT &middot; ORD-0142 BLOCKED &middot; COORD ROUTING NEW PROPOSAL</div>' +
        '<div class="sub">NO MONEY MOVED &middot; CASH STILL ' + V2.money(s.cash) + "</div>" +
        '<div class="steps">NEXT: SIG-0144 WEEKLY SCAN ON XLK &middot; QUEUED<br>GUARD: NO ORDER RAN &middot; EXECUTED_AT STILL BLANK &middot; NO DOUBLE FILL</div>';
    }
    if (state === "frozen") {
      return word + sent +
        '<div class="sub" style="margin-top:10px">ALL AGENTS FROZEN &middot; CLAIMS CANCELLED &middot; WORKING TASKS BLOCKED</div>' +
        '<div class="sub">' + snap.strings.press_green_to_resume + "</div>" +
        '<div class="steps">RESUME: <b>1</b> FLIP THE KILL SWITCH OFF &nbsp; <b>2</b> PRESS GREEN ONCE &nbsp; <b>3</b> COORD PICKS UP THE NEXT QUEUED TASK<br>' +
        "OLD BLOCKED TASKS STAY BLOCKED &middot; NOTHING AUTO-RESUMES</div>" +
        '<div class="sub muted">KILL SWITCH IS LATCHING &middot; NOTHING RUNS UNTIL IT IS OFF</div>';
    }
    /* error */
    return word + sent +
      '<div class="sub" style="margin-top:10px;color:#ff5a5a">ERROR ' + V2.ERROR.code + " &middot; LAST OK " + V2.ERROR.lastOk + "</div>" +
      '<div class="sub">' + V2.ERROR.text + "</div>" +
      '<div class="sub">RETRY IN ' + V2.ERROR.retryInS + "s &middot; RECORDED FALLBACK READY &middot; GUARD STILL WATCHING</div>";
  }

  /* ---------------- mini hero per state ---------------- */
  function miniHero(state, snap) {
    var p = V2.PROPOSAL, m = V2.METERS, s = V2.SCENARIO;
    var book = '<div class="book"><div class="book-cols"><span>TASK</span><span>TICKER</span><span>AMOUNT</span><span>STATUS</span></div>' +
      bookRows(state, true, snap.lang) + "</div>";
    if (state === "idle") {
      return '<div class="attract1">' + V2.ATTRACT.line1 + '</div><div class="attract2">' + V2.ATTRACT.line2 + '</div>' +
        '<div class="attract3">' + V2.ATTRACT.line3 + "</div>" + book;
    }
    if (state === "listening") {
      return waveHtml(true) + '<div class="mid-line">MIC LIVE &middot; PUSH TO TALK</div>' + book;
    }
    if (state === "thinking") {
      return '<div class="meter-row"><span>AGENT 1 &middot; RULES</span><div class="bar-track"><div class="bar-fill" style="width:61%"></div></div><span class="mono">1840ms</span></div>' +
        '<div class="meter-row"><span>BOCHA SEARCH</span><div class="bar-track"><div class="bar-fill" style="width:21%"></div></div><span class="mono">620ms</span></div>' +
        '<div class="mid-line">ROUND ' + m.roundUsed + " OF " + m.roundMax + " &middot; " + m.deepseekModel.toUpperCase() + "</div>" + book;
    }
    if (state === "approval") {
      return '<div class="prop-action green">' + p.action + " " + p.ticker + "</div>" +
        '<div class="prop-detail mono">' + p.shares + " SHARES @ " + p.price.toFixed(2) + " &middot; " + V2.money(p.amount) + "</div>" +
        '<div style="display:flex;gap:16px;align-items:center">' + gaugeSvg(p.riskScore, p.riskLabel, 160) +
        '<div><div class="countdown mono">' + p.approvalLeftS + 's</div><div class="mid-line">LEFT OF ' + p.approvalExpiresS + "s</div>" +
        '<div class="mid-line">RISK CHECK <b class="green">PASS</b></div></div></div>' +
        approveBtns(snap.lang);
    }
    if (state === "approved") {
      return '<div class="big-line green">FILLED ' + V2.money(p.amount) + " " + p.ticker + "</div>" +
        '<div class="mid-line">ORD-0142 DONE &middot; CASH NOW ' + V2.money(s.cash - p.amount) + "</div>" + book;
    }
    if (state === "rejected") {
      return '<div class="big-line red">HUMAN_REJECT</div>' +
        '<div class="mid-line"><span style="text-decoration:line-through">' + p.action + " " + p.ticker + " " + V2.money(p.amount) + "</span> &middot; NO MONEY MOVED</div>" +
        '<div class="mid-line">COORD ROUTING NEW PROPOSAL</div>' + book;
    }
    if (state === "frozen") {
      return '<div class="big-line red">ALL AGENTS FROZEN</div>' +
        '<div class="mid-line">' + snap.strings.press_green_to_resume + "</div>" +
        '<div class="mid-line">KILL SWITCH IS LATCHING &middot; NOTHING RUNS UNTIL IT IS OFF</div>';
    }
    return '<div class="big-line red">' + V2.ERROR.code + "</div>" +
      '<div class="mid-line">' + V2.ERROR.text + "</div>" +
      '<div class="mid-line">RETRY IN ' + V2.ERROR.retryInS + "s &middot; RECORDED FALLBACK READY &middot; GUARD STILL WATCHING</div>";
  }

  var HERO_FOOT = {
    idle: "PAPER MONEY ONLY &middot; NOTHING REAL TRADES &middot; TOP MOVERS: XLE " + V2.pct(V2.SECTORS[0].chg) + " &middot; XLU " + V2.pct(V2.SECTORS[1].chg) + " &middot; XLY " + V2.pct(V2.SECTORS[8].chg),
    listening: "VOICE PROPOSES &middot; BUTTONS EXECUTE &middot; NOTHING RUNS ON VOICE ALONE",
    thinking: "COORD PICKS FROM A FIXED MENU OF 12 ACTIONS &middot; CODE VALIDATES EVERY PICK &middot; PLAIN TEXT NEVER EXECUTES",
    approval: "",
    approved: "NEXT: AGENT 2 RISK CHECK ON SIG-0144 &middot; WEEKLY SCAN QUEUED &middot; CASH " + V2.money(V2.SCENARIO.cash - V2.PROPOSAL.amount),
    rejected: "COORD WILL PROPOSE AGAIN WHEN THE SIGNAL SCAN FINISHES &middot; NOTHING IS STUCK",
    frozen: "KILL SWITCH IS A LATCHING SWITCH ON ITS OWN PIN &middot; SOFTWARE CANNOT OVERRIDE IT",
    error: "BOOTH MODE FALLS BACK TO RECORDED RUNS IF DEEPSEEK STAYS DOWN &middot; NO REAL MONEY AT RISK"
  };

  /* ---------------- render ---------------- */
  window.V2Render = function (screen, state, lang) {
    var snap = V2.stateSnapshot(state, lang);
    var root = document.getElementById("screen");
    var s = V2.SCENARIO, m = V2.METERS;
    var langLabel = lang === "zh" ? "EN | \u4e2d\u6587" : "EN | \u4e2d\u6587";
    if (screen === "monitor") {
      var dim = (state === "frozen" || state === "error") ? " dim" : "";
      var pending = "";
      if (state === "approval" || state === "thinking") {
        pending = '<div class="pending-strip">PENDING ' + V2.PROPOSAL.taskId.toUpperCase() + " &middot; " + V2.PROPOSAL.action + " " + V2.PROPOSAL.ticker +
          " " + V2.money(V2.PROPOSAL.amount) + " &middot; RISK " + V2.PROPOSAL.riskScore + " " + V2.PROPOSAL.riskLabel +
          (state === "approval" ? " &middot; " + V2.PROPOSAL.approvalLeftS + "s LEFT" : "") + "</div>";
      } else if (state === "approved") {
        pending = '<div class="pending-strip" style="color:#2ecc71;border-color:#1d3a28;background:#0f1a13">FILLED ' + V2.PROPOSAL.taskId.toUpperCase() + " &middot; " + V2.PROPOSAL.action + " " + V2.PROPOSAL.ticker +
          " " + V2.money(V2.PROPOSAL.amount) + " &middot; 11:42:21</div>";
      } else if (state === "rejected") {
        pending = '<div class="pending-strip" style="color:#ff5a5a;border-color:#3a1d1d;background:#1a0f0f">REJECTED ' + V2.PROPOSAL.taskId.toUpperCase() + " &middot; " + V2.PROPOSAL.action + " " + V2.PROPOSAL.ticker +
          " " + V2.money(V2.PROPOSAL.amount) + " &middot; HUMAN_REJECT</div>";
      }
      var counts = "6 TASKS &middot; 2 DONE &middot; 1 WORKING &middot; 3 QUEUED";
      if (state === "approved") counts = "6 TASKS &middot; 3 DONE &middot; 0 WORKING &middot; 3 QUEUED";
      if (state === "rejected") counts = "6 TASKS &middot; 2 DONE &middot; 0 WORKING &middot; 3 QUEUED &middot; 1 BLOCKED";
      if (state === "frozen") counts = "6 TASKS &middot; 2 DONE &middot; 0 WORKING &middot; 3 QUEUED &middot; 1 BLOCKED";
      root.className = "monitor" + dim;
      root.innerHTML =
        '<div class="topbar"><div class="brand">SI CONSOLE <small>ORDER BOOK &middot; BOOTH &middot; REPLAY ' + s.replay + " &middot; WEEK " + s.replayWeek + '</small></div>' +
        '<div class="top-mid mono">' + V2.label("round", lang) + " " + m.roundUsed + " / " + m.roundMax + " &middot; " + m.deepseekModel.toUpperCase() + " " + m.deepseekMs + "ms</div>" +
        '<div class="top-right"><span class="mono">' + langLabel + "</span><br>" + ledsHtml(snap) + "</div></div>" +
        '<div class="main">' +
        '<div class="panel book"><div class="book-head"><span class="book-title">' + V2.label("orderBook", lang) + "</span>" +
        '<span class="panel-h">' + counts + "</span></div>" + pending +
        '<div class="book-cols"><span>TASK</span><span>AGENT</span><span>TYPE</span><span>TICKER</span><span>AMOUNT</span><span>RND</span><span>RISK</span><span>NOTE</span></div>' +
        bookRows(state, false, lang) + sectorBookHtml(lang) + "</div>" +
        '<div class="right">' +
        '<div class="panel hero">' + monitorHero(state, snap) +
        (HERO_FOOT[state] ? '<div class="hero-foot">' + HERO_FOOT[state] + "</div>" : "") + "</div>" +
        '<div class="panel roster">' + rosterHtml(snap) + "</div>" +
        '<div class="panel handoff"><span><b>COORD</b> <span class="muted">&rarr;</span> <b>AGENT 1</b> <span class="muted">&rarr;</span> <b>AGENT 2</b> <span class="muted">&rarr;</span> <b class="yellow">GUARD</b></span><span class="muted mono">' + V2.label("handoff", lang) + "</span></div>" +
        "</div></div>" +
        '<div class="bottom"><div class="panel tape">' + tapeHtml(state, 3, lang) + '</div>' +
        '<div class="panel pnl"><div class="big mono">PF ' + V2.money(s.portfolioValue) + ' <span class="red">' + V2.signed(s.portfolioDay) + " (" + V2.pct(s.portfolioDayPct) + ')</span></div>' +
        '<div class="small">CASH ' + V2.money(V2.cashForState(state)) + " &middot; COST $" + m.costTodayUsd.toFixed(2) + " / $" + m.costCapUsd.toFixed(2) +
        " &middot; TOKENS " + m.tokensIn + " / " + m.tokensOut + " &middot; BOCHA " + m.bochaMs + "ms</div></div></div>";
    } else {
      var dimMini = (state === "frozen" || state === "error") ? " dim" : "";
      root.className = "mini" + dimMini;
      root.innerHTML =
        '<div class="topbar"><span>SI CONSOLE &middot; ORDER BOOK</span><span class="mono">' + V2.label("round", lang) + " " + m.roundUsed + "/" + m.roundMax + " &middot; " + langLabel + "</span></div>" +
        '<div class="state-line"><div class="state-word ' + STATE_COLOR[state] + '">' + snap.word + '</div><div class="leds">' + ledDots(snap) + "</div></div>" +
        '<div class="sentence">' + snap.sentence + '</div>' +
        '<div class="hero">' + miniHero(state, snap) + "</div>" +
        '<div class="pnl mono">' + pnlLine(state) + "</div>";
    }
  };
})();
