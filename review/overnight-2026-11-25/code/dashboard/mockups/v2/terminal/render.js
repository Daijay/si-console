// SI Console UI v2, direction TERMINAL. Renders from window.V2 only.
(function () {
  "use strict";
  var V2 = window.V2;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = text;
    return n;
  }
  function ledDot(color, mode) {
    var s = el("span", "led" + (mode === "on" || mode === "blink" ? " " + mode : ""));
    s.style.color = color;
    if (mode === "on" || mode === "blink") s.style.backgroundColor = color;
    return s;
  }
  function wordClass(state) {
    return { idle: "amb", listening: "grn", thinking: "amb", approval: "amb",
      approved: "grn", rejected: "red", frozen: "red", error: "red" }[state];
  }
  function tapeStr(n, state) {
    var t = V2.tapeForState(state).slice(-n);
    return t.map(function (e) { return e.t + " " + e.who + " " + e.text; }).join("   |   ");
  }
  function kv(k, v, vcls) {
    var r = el("div", "kv");
    r.appendChild(el("span", "k", k));
    r.appendChild(el("span", vcls || "", v));
    return r;
  }
  function wave(active) {
    var w = el("div", "wave" + (active ? "" : " idle"));
    V2.WAVEFORM.forEach(function (h) {
      var b = el("i");
      b.style.height = (active ? h : 8) + "%";
      w.appendChild(b);
    });
    return w;
  }
  function pips(used, max) {
    var p = el("div", "pips");
    for (var i = 0; i < max; i++) p.appendChild(el("i", i < used ? "on" : ""));
    return p;
  }

  // ---- per-state hero body. Same content both screens, CSS scales it.
  function heroBody(screen, snap) {
    var st = snap.state, b = el("div", "body"), P = V2.PROPOSAL, M = V2.METERS, E = V2.ERROR;
    var mini = screen === "mini";
    function big(text, cls) { b.appendChild(el("div", "big" + (cls ? " " + cls : ""), text)); }
    function big2(text, cls) { b.appendChild(el("div", "big2" + (cls ? " " + cls : ""), text)); }
    function sub(text) { b.appendChild(el("div", "sub", text)); }
    if (st === "idle") {
      big(V2.ATTRACT.line1, "amb");
      big(V2.ATTRACT.line2, "grn");
      sub(V2.ATTRACT.line3);
      sub(snap.strings.no_proposal + "  " + V2.SCENARIO.replayWeek + " REPLAY");
    } else if (st === "listening") {
      b.appendChild(wave(true));
      big2("MIC OPEN", "grn");
      sub("VOICE PROPOSES. THE GREEN BUTTON EXECUTES.");
    } else if (st === "thinking") {
      big("ROUND " + M.roundUsed + " / " + M.roundMax, "amb");
      b.appendChild(pips(M.roundUsed, M.roundMax));
      b.appendChild(kv("DEEPSEEK " + M.deepseekModel, M.deepseekMs + "ms"));
      b.appendChild(kv("WORKING", "sig-0142  " + V2.TASKS[0].note));
      if (!mini) b.appendChild(kv("LAST TOOL", "web_search utilities  Bocha " + M.bochaMs + "ms"));
    } else if (st === "approval") {
      big(P.action + " " + P.ticker + " " + P.shares + " @ " + P.price.toFixed(2));
      big2(V2.money(P.amount) + "   RISK " + P.riskScore + " " + P.riskLabel, "grn");
      b.appendChild(kv(V2.label("countdown", snap.lang), P.approvalLeftS + "s LEFT OF " + P.approvalExpiresS + "s", "amb"));
      if (!mini) {
        b.appendChild(kv("RISK CHECK", P.riskCheck, "grn"));
        b.appendChild(kv("CAP", P.capUsedPct.toFixed(1) + "% / " + P.capMaxPct.toFixed(1) + "%"));
      }
      var row = el("div", "btnrow");
      var g = el("div", "apbtn g", snap.lang === "zh" ? "绿色 批准" : "GREEN APPROVE");
      var r = el("div", "apbtn r", snap.lang === "zh" ? "红色 拒绝" : "RED REJECT");
      row.appendChild(g); row.appendChild(r);
      b.appendChild(row);
    } else if (st === "approved") {
      big("FILLED " + P.taskId, "grn");
      big2(P.action + " " + P.ticker + " " + P.shares + " @ " + P.price.toFixed(2) + "  " + V2.money(P.amount));
      sub("PORTFOLIO " + V2.money(V2.SCENARIO.portfolioValue) + "  DAY " + V2.money(V2.SCENARIO.portfolioDay) + " (" + V2.pct(V2.SCENARIO.portfolioDayPct) + ")");
      if (!mini) b.appendChild(kv("NEXT", "AGENT 2 working  risk-0142 done"));
    } else if (st === "rejected") {
      var s = el("div", "big strike", P.action + " " + P.ticker + " " + P.shares + " @ " + P.price.toFixed(2));
      b.appendChild(s);
      big2("BLOCKED  HUMAN_REJECT", "red");
      sub("COORD: " + snap.rosterStatus.coord + "  new proposal next");
    } else if (st === "frozen") {
      big("ALL AGENTS FROZEN", "red");
      big2("KILL SWITCH LATCHED", "red");
      sub(snap.strings.press_green_to_resume);
      if (!mini) sub(snap.strings.software_freeze);
    } else if (st === "error") {
      big(E.code, "red");
      big2(E.text);
      b.appendChild(kv("RETRY IN", E.retryInS + "s"));
      b.appendChild(kv("LAST OK", E.lastOk));
      if (!mini) b.appendChild(kv("GUARD", "watching"));
    }
    return b;
  }

  function plStrip(screen, lang, snap) {
    var S = V2.SCENARIO, M = V2.METERS;
    var p = el("div", "pl");
    function item(k, v, cls) {
      p.appendChild(el("span", "k", k));
      p.appendChild(el("span", cls || "", v));
    }
    item(V2.label("portfolio", lang), V2.money(S.portfolioValue));
    item("DAY", V2.money(S.portfolioDay) + " (" + V2.pct(S.portfolioDayPct) + ")", "dn");
    if (screen === "monitor") item("CASH", V2.money(V2.cashForState(snap.state)));
    item(lang === "zh" ? V2.label("costToday", "zh") : "COST", "$" + M.costTodayUsd.toFixed(2) + " / $" + M.costCapUsd.toFixed(2));
    if (screen === "monitor") {
      item("MODE", "BOOTH");
      item("REPLAY", S.replayWeek);
    }
    return p;
  }

  function ledRow(snap) {
    var r = el("span");
    var map = [["C", "#2ecc71", snap.leds.coord], ["1", "#e8ecf1", snap.leds.agent1],
      ["2", "#4aa8ff", snap.leds.agent2], ["G", "#f5c542", snap.leds.guard]];
    map.forEach(function (m, i) {
      if (i) r.appendChild(document.createTextNode("  "));
      r.appendChild(ledDot(m[1], m[2]));
      r.appendChild(document.createTextNode(" " + m[0]));
    });
    return r;
  }

  function taskBook(snap) {
    var p = el("div", "panel book grow");
    // The queue is one static fixture, but the order task follows the
    // state: it fills on approved, blocks on rejected, and blocks with
    // KILL_SWITCH on frozen, the same rule as bridge.py on_kill.
    function dispStatus(tk) {
      if (tk.id === "ord-0142" && snap.state === "approved") return "done";
      if (tk.id === "ord-0142" && snap.state === "rejected") return "blocked";
      if (tk.id === "ord-0142" && snap.state === "frozen") return "blocked";
      return tk.status;
    }
    var doneCount = V2.TASKS.filter(function (t) { return dispStatus(t) === "done"; }).length;
    var t = el("div", "ptitle");
    t.appendChild(el("span", "", V2.label("taskQueue", snap.lang)));
    t.appendChild(el("span", "r", doneCount + " DONE / 6"));
    p.appendChild(t);
    var cols = el("div", "cols");
    ["ID", "AGENT", "TYPE", "TKR", "AMOUNT", "RND", "RISK", "STATUS"].forEach(function (c) {
      cols.appendChild(el("span", "", c));
    });
    p.appendChild(cols);
    var shortAgent = { signal: "signal", risk: "risk", execution: "exec", coordinator: "coord" };
    var shortType = { signal: "signal", risk_check: "risk", order: "order", research: "res", narration: "narr" };
    V2.TASKS.forEach(function (tk) {
      var ds = dispStatus(tk);
      var row = el("div", "row " + ds);
      row.appendChild(el("span", "", tk.id));
      row.appendChild(el("span", "mut", shortAgent[tk.agent] || tk.agent));
      row.appendChild(el("span", "mut", shortType[tk.type] || tk.type));
      row.appendChild(el("span", "", tk.ticker || "-"));
      row.appendChild(el("span", "amt", tk.amount ? "$" + tk.amount.toLocaleString("en-US") : "-"));
      row.appendChild(el("span", "mut", "R" + tk.round));
      var rk = el("span", tk.risk === "pass" ? "grn" : "mut", tk.risk);
      row.appendChild(rk);
      var st = el("span", ds === "done" ? "grn" : ds === "working" ? "amb" : ds === "blocked" ? "red" : "dim", ds.toUpperCase());
      row.appendChild(st);
      p.appendChild(row);
    });
    var d = el("div", "depth");
    var f = el("i");
    f.style.width = Math.round(doneCount / 6 * 100) + "%";
    d.appendChild(f);
    p.appendChild(d);
    var foot = el("div", "bookfoot");
    var next = V2.TASKS.filter(function (t) { return t.status === "queued"; })[0];
    foot.appendChild(el("div", "", "NEXT UP  " + next.id + "  " + next.note + (next.ticker ? "  " + next.ticker : "")));
    foot.appendChild(el("div", "dim", "STUCK WATCHDOG 300s   ROUND LIMIT 3   ONE CLAIM PER AGENT"));
    p.appendChild(foot);
    return p;
  }

  function handoff(snap) {
    var p = el("div", "panel hand");
    var t = el("div", "ptitle");
    t.appendChild(el("span", "", V2.label("handoff", snap.lang)));
    t.appendChild(el("span", "r", "COORD > SIGNAL > RISK > GUARD"));
    p.appendChild(t);
    var chain = el("div", "chain");
    var nodes = [
      { n: "COORD", c: "#2ecc71", s: snap.rosterStatus.coord },
      { n: "AGENT 1", c: "#e8ecf1", s: snap.rosterStatus.agent1 },
      { n: "AGENT 2", c: "#4aa8ff", s: snap.rosterStatus.agent2 },
      { n: "GUARD", c: "#f5c542", s: snap.rosterStatus.guard }
    ];
    nodes.forEach(function (nd, i) {
      if (i) chain.appendChild(el("span", "arr", ">"));
      var box = el("div", "node");
      box.appendChild(el("div", "", nd.n)).style.color = nd.c;
      box.appendChild(el("span", "st mut", nd.s));
      chain.appendChild(box);
    });
    p.appendChild(chain);
    var ext = el("div", "ext");
    ext.appendChild(document.createTextNode("HERMES external  "));
    ext.appendChild(el("span", "pur", snap.rosterStatus.hermes));
    ext.appendChild(document.createTextNode("  research only, never approve, never execute"));
    p.appendChild(ext);
    return p;
  }

  function hardware(snap) {
    var p = el("div", "panel hw");
    var t = el("div", "ptitle");
    t.appendChild(el("span", "", V2.label("hardware", snap.lang)));
    t.appendChild(el("span", "r", "GPIO"));
    p.appendChild(t);
    var rows = [
      ["GREEN BTN", "g", snap.lang === "zh" ? "批准 / 2020" : "APPROVE / 2020"],
      ["RED BTN", "r", snap.lang === "zh" ? "拒绝 / 2022" : "REJECT / 2022"],
      ["KILL", "k", "LATCHING  FREEZE ALL"],
      ["PUSH TO TALK", "", "HOLD TO SPEAK"],
      ["EN / 中文", "", snap.lang === "zh" ? "中文 ACTIVE" : "EN ACTIVE"]
    ];
    rows.forEach(function (r) {
      var row = el("div", "row");
      row.appendChild(el("span", "k", r[0]));
      var b = el("span", "btn " + r[1], r[2]);
      row.appendChild(b);
      p.appendChild(row);
    });
    return p;
  }

  function sectors(snap) {
    var p = el("div", "panel sect");
    var t = el("div", "ptitle");
    t.appendChild(el("span", "", V2.label("sectors", snap.lang) + " / 2022 REPLAY"));
    t.appendChild(el("span", "r", "11 ETFS"));
    p.appendChild(t);
    var g = el("div", "grid");
    V2.SECTORS.forEach(function (s) {
      var row = el("div", "row");
      row.appendChild(el("span", "amb", s.ticker));
      row.appendChild(el("span", "mut", s.name));
      row.appendChild(el("span", "px", s.price.toFixed(2)));
      row.appendChild(el("span", "chg " + (s.chg >= 0 ? "up" : "dn"), V2.pct(s.chg)));
      g.appendChild(row);
    });
    p.appendChild(g);
    return p;
  }

  function roster(snap) {
    var p = el("div", "panel roster");
    var t = el("div", "ptitle");
    t.appendChild(el("span", "", V2.label("agents", snap.lang)));
    t.appendChild(el("span", "r", "5 ROSTER"));
    p.appendChild(t);
    var ledKey = { coord: snap.leds.coord, agent1: snap.leds.agent1, agent2: snap.leds.agent2, guard: snap.leds.guard, hermes: "off" };
    V2.ROSTER.forEach(function (a) {
      var row = el("div", "row");
      row.appendChild(ledDot(a.color, ledKey[a.id]));
      row.appendChild(el("span", "nm", a.name)).style.color = a.color;
      var rl = el("span", "rl");
      rl.appendChild(document.createTextNode(a.role));
      // COORD has role and tier both "coordinator". Show the tier
      // only when it adds information.
      if (a.tier !== a.role) rl.appendChild(el("span", "tier", a.tier));
      row.appendChild(rl);
      var st = snap.rosterStatus[a.id];
      row.appendChild(el("span", "st " + (st === "working" ? "grn" : st === "frozen" || st === "offline" ? "red" : st === "checking" ? "yel" : "mut"), st.toUpperCase()));
      p.appendChild(row);
    });
    return p;
  }

  function riskPanel(snap) {
    var P = V2.PROPOSAL;
    var p = el("div", "panel risk");
    var t = el("div", "ptitle");
    t.appendChild(el("span", "", V2.label("risk", snap.lang)));
    t.appendChild(el("span", "r", P.taskId));
    p.appendChild(t);
    var v = el("div", "val");
    v.appendChild(el("span", "grn", String(P.riskScore)));
    v.appendChild(el("small", "", " / 100  " + P.riskLabel));
    p.appendChild(v);
    var bar = el("div", "bar");
    var fill = el("div", "fill");
    fill.style.width = P.riskScore + "%";
    bar.appendChild(fill);
    var mark = el("div", "mark");
    mark.style.left = P.riskScore + "%";
    bar.appendChild(mark);
    p.appendChild(bar);
    var sc = el("div", "scale");
    sc.appendChild(el("span", "", "0 LOW"));
    sc.appendChild(el("span", "", "50 MED"));
    sc.appendChild(el("span", "", "100 HIGH"));
    p.appendChild(sc);
    var f = el("div", "facts");
    f.appendChild(el("div", "", "ACTION  "));
    f.lastChild.appendChild(el("b", "", P.action + " " + P.ticker + " " + P.shares + " @ " + P.price.toFixed(2)));
    f.appendChild(el("div", "", "AMOUNT  "));
    f.lastChild.appendChild(el("b", "", V2.money(P.amount)));
    f.appendChild(el("div", "", "RISK CHECK  "));
    f.lastChild.appendChild(el("b", "", P.riskCheck));
    f.appendChild(el("div", "", "CAP  "));
    f.lastChild.appendChild(el("b", "", P.capUsedPct.toFixed(1) + "% / " + P.capMaxPct.toFixed(1) + "%"));
    p.appendChild(f);
    return p;
  }

  function meters(snap) {
    var M = V2.METERS;
    var p = el("div", "panel meters grow");
    var t = el("div", "ptitle");
    t.appendChild(el("span", "", V2.label("meters", snap.lang)));
    t.appendChild(el("span", "r", M.apiStatus.toUpperCase()));
    p.appendChild(t);
    function row(k, v) {
      var r = el("div", "row");
      r.appendChild(el("span", "k", k));
      r.appendChild(el("span", "", v));
      p.appendChild(r);
    }
    row("DEEPSEEK " + M.deepseekModel, M.deepseekMs + "ms");
    row("TOKENS IN / OUT", M.tokensIn + " / " + M.tokensOut);
    row("BOCHA SEARCH", M.bochaMs + "ms");
    row(V2.label("round", snap.lang), M.roundUsed + " / " + M.roundMax);
    row(V2.label("costToday", snap.lang), "$" + M.costTodayUsd.toFixed(2) + " / $" + M.costCapUsd.toFixed(2));
    var bar = el("div", "bar");
    var f = el("i");
    f.style.width = Math.round(M.costTodayUsd / M.costCapUsd * 100) + "%";
    bar.appendChild(f);
    p.appendChild(bar);
    p.appendChild(pips(M.roundUsed, M.roundMax)).style.margin = "0 10px 10px";
    return p;
  }

  function renderMonitor(root, snap) {
    var top = el("div", "topbar");
    top.appendChild(el("span", "brand", "SI CONSOLE // TERMINAL"));
    top.appendChild(el("span", "mut", "MODE BOOTH"));
    top.appendChild(el("span", "mut", "REPLAY " + V2.SCENARIO.replayWeek));
    top.appendChild(el("span", "sp"));
    top.appendChild(ledRow(snap));
    top.appendChild(el("span", snap.lang === "zh" ? "yel" : "amb", snap.lang === "zh" ? "中文" : "EN"));
    top.appendChild(el("span", "mut", "11:42:19"));
    root.appendChild(top);

    var tape = el("div", "tape");
    tape.appendChild(el("b", "", V2.label("tape", snap.lang)));
    tape.appendChild(document.createTextNode(tapeStr(8, snap.state)));
    root.appendChild(tape);

    var main = el("div", "main");
    var cl = el("div", "col l");
    cl.appendChild(taskBook(snap));
    cl.appendChild(handoff(snap));
    cl.appendChild(hardware(snap));
    var cc = el("div", "col c");
    var hero = el("div", "panel hero grow");
    var w = el("div", "word " + wordClass(snap.state), snap.word);
    hero.appendChild(w);
    hero.appendChild(el("div", "sent", snap.sentence));
    hero.appendChild(heroBody("monitor", snap));
    var log = el("div", "herolog");
    log.appendChild(el("b", "", V2.label("tape", snap.lang) + "  "));
    V2.tapeForState(snap.state).slice(-5).forEach(function (e, i) {
      if (i) log.appendChild(el("br"));
      log.appendChild(el("span", "lt", e.t + " "));
      log.appendChild(document.createTextNode(e.who + " " + e.text));
    });
    hero.appendChild(log);
    cc.appendChild(hero);
    cc.appendChild(sectors(snap));
    var cr = el("div", "col r");
    cr.appendChild(roster(snap));
    cr.appendChild(riskPanel(snap));
    cr.appendChild(meters(snap));
    main.appendChild(cl); main.appendChild(cc); main.appendChild(cr);
    root.appendChild(main);
    root.appendChild(plStrip("monitor", snap.lang, snap));
  }

  function renderMini(root, snap) {
    var top = el("div", "topbar");
    top.appendChild(el("span", "brand", "SI CONSOLE // TERMINAL"));
    top.appendChild(el("span", "mut", "BOOTH " + V2.SCENARIO.replay));
    top.appendChild(el("span", "sp"));
    top.appendChild(ledRow(snap));
    top.appendChild(el("span", snap.lang === "zh" ? "yel" : "amb", snap.lang === "zh" ? "中文" : "EN"));
    root.appendChild(top);

    var tape = el("div", "tape");
    tape.appendChild(document.createTextNode(tapeStr(4, snap.state)));
    root.appendChild(tape);

    var hero = el("div", "hero");
    hero.appendChild(el("div", "word " + wordClass(snap.state), snap.word));
    hero.appendChild(el("div", "sent", snap.sentence));
    hero.appendChild(heroBody("mini", snap));
    var foot = el("div", "minifoot");
    var rs = V2.ROSTER.map(function (a) { return a.name + " " + snap.rosterStatus[a.id]; }).join("  |  ");
    foot.appendChild(el("span", "k", V2.label("agents", snap.lang)));
    foot.appendChild(document.createTextNode(rs));
    foot.appendChild(el("br"));
    var top3 = V2.SECTORS.slice().sort(function (a, b) { return b.chg - a.chg; }).slice(0, 3)
      .map(function (s) { return s.ticker + " " + V2.pct(s.chg); }).join("  |  ");
    foot.appendChild(el("span", "k", V2.label("top", snap.lang)));
    foot.appendChild(document.createTextNode(top3));
    hero.appendChild(foot);
    root.appendChild(hero);
    root.appendChild(plStrip("mini", snap.lang, snap));
  }

  window.V2Render = function (screen, state, lang) {
    var snap = V2.stateSnapshot(state, lang);
    var root = document.getElementById("screen");
    root.className = screen;
    root.textContent = "";
    if (screen === "monitor") renderMonitor(root, snap);
    else renderMini(root, snap);
  };
})();
