/* 15.6 inch monitor: one render function from a state snapshot. */
(function () {
  const h = UI.h;
  const esc = UI.esc;

  const top = (s) => `
    <header class="top">
      <div class="name">${h("ui_app")}<span>${h("ui_mode_" + s.mode)}</span></div>
      <h1 class="word" data-fit="52" aria-live="polite">${h(s.word)}</h1>
      <div class="right"><span>${h("ui_round", { n: s.round, max: s.max })}</span>${UI.langBadge()}</div>
    </header>`;

  const risk = (level) => {
    const n = level === "high" ? 3 : 2;
    return `<span class="risk">${[1, 2, 3].map((i) => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}${h("ui_risk_" + level)}</span>`;
  };

  function transcript(s) {
    const rows = s.transcript.map((m) => `
      <li class="who-${m.who} ${m.who === "you" ? "you" : ""}">
        <div class="meta"><b>${h(m.who === "you" ? "ui_node_you" : "ui_agent_" + m.who)}</b><time>${m.time}</time></div>
        <p>${m.said ? esc(m.said[UI.lang]) : h(m.key, m.params)}</p>
        ${m.tool ? `<code translate="no">${esc(m.tool).replace(/\(|, /g, "$&<wbr>")}</code>` : ""}
      </li>`).join("");
    return `<div class="col">
      <section class="panel talk"><h2>${h("ui_p_transcript")}</h2>
        ${rows ? `<ol>${rows}</ol>` : `<p class="empty">${h(s.mic || s.dots ? s.sub : "ui_empty_transcript", s.subParams)}</p>`}
      </section>
      ${s.mic ? `<div class="micbox"><h2>${UI.icon("mic")}${h("ui_mic_level")}</h2>${UI.meter(32)}</div>` : ""}
    </div>`;
  }

  /* Node centres on a 760 x 500 drawing. Order follows the real pipeline:
     the request goes down, and nothing passes the button without a press. */
  const POS = { you: [380, 34], coord: [380, 150], a1: [128, 272], a2: [632, 272], guard: [380, 392], button: [380, 496] };
  const EDGES = [
    ["you", "coord", "you-coord", "coord"], ["coord", "a1", "coord-a1", "a1"], ["coord", "a2", "coord-a2", "a2"],
    ["a1", "guard", "a1-guard", "guard"], ["a2", "guard", "a2-guard", "guard"], ["guard", "button", "guard-button", "coord"],
  ];
  const W = 252, H = 68;

  /* Trim an edge so it starts and ends on the box borders. */
  function edge(from, to, state, colour) {
    const [x1, y1] = POS[from], [x2, y2] = POS[to];
    const dx = x2 - x1, dy = y2 - y1;
    const cut = Math.min(dx ? (W / 2 + 2) / Math.abs(dx) : 1, dy ? (H / 2 + 2) / Math.abs(dy) : 1);
    const sx = x1 + dx * cut, sy = y1 + dy * cut;
    const len = Math.hypot(dx, dy) * (1 - 2 * cut);
    const deg = (Math.atan2(dy, dx) * 180) / Math.PI;
    return `<div class="edge who-${colour} ${state || ""}" style="left:${sx}px;top:${sy}px;width:${len}px;transform:rotate(${deg}deg)">${state === "active" ? '<span class="packet"><i></i></span><span class="packet late"><i></i></span>' : ""}</div>`;
  }

  function node(id, cls, title, small) {
    const [x, y] = POS[id];
    return `<div class="node who-${id} ${cls}" style="left:${x - W / 2}px;top:${y - H / 2}px"><b>${title}</b>${small ? `<small>${small}</small>` : ""}</div>`;
  }

  function graph(s) {
    const edges = EDGES.map(([a, b, id, c]) => edge(a, b, s.edges[id], c)).join("");
    const agents = UI.AGENTS.map((a) =>
      node(a, s.agents[a], h("ui_agent_" + a), `${h("ui_role_" + a)} / ${h("ui_st_" + s.agents[a])}`)).join("");
    return `<section class="panel graphwrap"><h2>${h("ui_p_graph")}</h2>
      <div class="graph">${edges}${node("you", "", h("ui_node_you"))}${agents}${node("button", s.layout === "approval" ? "gate" : "", h("ui_node_button"))}</div>
    </section>`;
  }

  function log(s) {
    const rows = s.events.slice(-4).map(([time, key, p]) => `<li><time>${time}</time><span>${h(key, p)}</span></li>`).join("");
    return `<section class="panel log"><h2>${h("ui_p_log")}</h2>${rows ? `<ol>${rows}</ol>` : `<p class="empty">${h("ui_empty_log")}</p>`}</section>`;
  }

  const verdict = (v) => `
    <h3>${h("ui_p_guard")}</h3>
    <p class="verdict">${h(v.verdict)}</p>
    <ul class="checks">${v.checks.map(([key, ok]) => `<li class="${ok ? "" : "fail"}">${UI.icon(ok ? "check" : "cross")}${h(key)}</li>`).join("")}</ul>`;

  function card(s) {
    if (s.layout === "approval") {
      const a = s.approval;
      return `<section class="panel card"><h2>${h("ui_p_approval")}</h2>
        <div class="ask" role="alertdialog">
          <div class="meta"><span class="chip who-${a.agent}">${h("ui_ap_asks", { agent: "@" + a.agent })}</span>${risk(a.risk)}</div>
          <p class="action">${h(a.action, a.params)}</p>
          ${a.command ? `<p class="command-line"><code>${UI.esc(a.command)}</code></p>` : ""}
          <p class="riskwhy"><span>${h("ui_risk_" + a.risk + "_why")}</span><span>${h("ui_ap_seconds", { s: a.secondsLeft })}</span></p>
        </div>
        <h3>${h("ui_p_why")}</h3><p class="why">${h(a.why, a.params)}</p>
        ${verdict(a)}
      </section>`;
    }
    const busy = s.sub && s.round;
    let body = busy ? `<p class="result">${h(s.sub, s.subParams)}</p>` : `<p class="empty">${h("ui_empty_card")}</p>`;
    if (s.verdictCard) body += verdict(s.verdictCard);
    const title = !busy ? "ui_p_decision" : s.icon ? "ui_last_result" : "ui_p_now";
    return `<section class="panel card"><h2>${h(title)}</h2>${body}</section>`;
  }

  function stats(s) {
    const c = s.cost, j = s.judge;
    return `<div class="stats">
      <section class="panel"><h2>${h("ui_p_cost")}</h2>
        <p class="big">${c ? UI.money(c.usd, c.usd < 1 ? 3 : 2) : "-"}</p>
        <div class="gauge"><i style="--v:${c ? Math.max(0.01, Math.min(1, c.usd / c.cap)) : 0}"></i></div>
        <p class="note">${c ? h("ui_p_calls_cap", { n: c.calls, cap: c.cap }) : h("ui_st_unknown")}</p>
      </section>
      <section class="panel"><h2>${h("ui_p_judge")}</h2>
        <p class="big">${j ? j.score.toFixed(2) : "-"}</p>
        <div class="gauge"><i style="--v:${j ? j.score : 0}"></i></div>
        <p class="note">${j ? h("ui_p_judge_what", { tier: j.tier }) : h("ui_p_judge_none")}</p>
      </section>
    </div>`;
  }

  function pads(s) {
    const a = s.approval;
    const phrase = (c) => `${h("ui_ap_" + c + "_top")}${UI.lang === "en" ? " " : "，"}${h("ui_ap_" + c + "_main")}`;
    return `<div class="countdown"><i style="--from:${a.secondsLeft / a.timeout};--secs:${a.secondsLeft}s"></i></div>
      <div class="pads">
        <div class="pad yes"><i class="btn"></i>${phrase("green")}</div>
        <div class="pad no"><i class="btn"></i>${s.confirmRed ? h("ui_ap_confirm_red") : phrase("red")}</div>
      </div>`;
  }

  const dashboard = (s) => `${top(s)}
    ${s.banner ? `<div class="banner">${h(s.banner)}</div>` : ""}
    <main class="grid">
      ${transcript(s)}
      <div class="col">${graph(s)}${log(s)}</div>
      <div class="col">${card(s)}${stats(s)}</div>
    </main>
    ${s.layout === "approval" ? pads(s) : ""}
    ${s.toast ? `<div class="toast" role="status">${h(s.toast)}</div>` : ""}`;

  const layouts = {
    status: dashboard,
    approval: dashboard,

    frozen: (s) => `<section class="frozen" role="alert">
      ${UI.langBadge("corner")}
      <h1 class="word">${h(s.word)}</h1><p>${h("ui_fz_body")}</p><p class="step">${h("ui_fz_step")}</p>
    </section>`,

    resume: (s) => `<section class="resume" role="alert">
      <div class="upper"><h1 class="word" data-fit="120">${h(s.word)}</h1><p>${h("ui_rs_body")}</p></div>
      <div class="go">${h("ui_rs_step")}</div>
    </section>`,

    scenario: (s) => `${top(s)}<section class="choose">
      <p>${h("ui_sc_note")}</p>
      <div class="years">
        <div class="year" style="--b:var(--approve)"><span>${h("ui_sc_green")}</span><strong>2020</strong></div>
        <div class="year" style="--b:var(--reject)"><span>${h("ui_sc_red")}</span><strong>2022</strong></div>
      </div></section>`,

    attract(s, prompt) {
      const other = UI.lang === "en" ? "zh" : "en";
      return `<section class="attract">
        ${UI.langBadge("corner")}
        <h1 class="head">${h("ui_at_head")}</h1>
        <p class="alt" lang="${other}">${h("ui_at_head", null, other)}</p>
        <div class="prompt"><small>${h("ui_at_try")}</small><strong data-prompt>${h("ui_at_prompt_" + (prompt + 1))}</strong></div>
        <p class="rule">${h("ui_at_rule")}</p>
        <div class="lamps">${UI.AGENTS.map((a) => `<div class="who-${a}"><i></i>${h("ui_agent_" + a)}</div>`).join("")}</div>
      </section>`;
    },

    fault(s) {
      const f = "ui_f_" + s.fault;
      const gone = s.fault === "api"; /* no live data behind an API outage */
      return `${gone ? "" : dashboard(s)}
        <div class="dim ${gone ? "full" : ""}" role="alert">
          ${gone ? UI.langBadge("corner") : ""}
          <div class="fault"><div class="hatch"></div><div class="body">
            <h1 data-fit="64">${UI.icon(UI.FAULT_ICON[s.fault])}${h(f + "_title")}</h1>
            <p>${h(f + "_body", { cap: s.cost ? s.cost.cap : 0 })}</p>
            <p class="next">${h(f + "_next")}</p>
            ${s.lastWord ? `<p class="next">${h("ui_f_api_last", { word: "@" + s.lastWord })}</p>` : ""}
          </div></div>
        </div>`;
    },
  };

  UI.start((s, prompt) => layouts[s.layout](s, prompt));
})();
