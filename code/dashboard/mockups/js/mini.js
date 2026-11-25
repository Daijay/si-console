/* 5 inch status screen: one render function from a state snapshot. */
(function () {
  const h = UI.h;

  const bar = (s) => `
    <header class="bar">
      <span class="mode">${h("ui_mode_" + s.mode)}</span>
      <span class="round">${h("ui_round", { n: s.round, max: s.max })}</span>
      ${UI.langBadge()}
    </header>`;

  const tiles = (s) => `<div class="tiles">${UI.AGENTS.map((a) => `
    <div class="tile who-${a} ${s.agents[a]}">
      <b>${h("ui_agent_" + a)}</b><small>${h("ui_st_" + s.agents[a])}</small>
    </div>`).join("")}</div>`;

  const risk = (level) => {
    const n = level === "high" ? 3 : 2;
    return `<span class="risk">${[1, 2, 3].map((i) => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}${h("ui_risk_" + level)}</span>`;
  };

  const layouts = {
    status(s) {
      const word = UI.t(s.word);
      /* Long English words wrap to two lines at a size still readable at 2 m. */
      const two = UI.lang === "en" && word.length > 10 && word.includes(" ");
      return `${bar(s)}
        ${s.banner ? `<div class="banner">${h(s.banner)}</div>` : ""}
        <main class="state" aria-live="polite">
          <div class="row enter">${s.icon ? UI.icon(s.icon) : ""}<h1 class="word ${two ? "two" : ""}" data-fit="72" style="flex:1;min-width:0">${h(s.word)}</h1></div>
          ${s.sub ? `<p class="sub">${h(s.sub, s.subParams)}</p>` : ""}
          ${s.mic ? UI.meter(22) : ""}
          ${s.dots ? '<div class="dots"><i></i><i></i><i></i></div>' : ""}
        </main>
        ${tiles(s)}
        ${s.toast ? `<div class="toast" role="status">${h(s.toast)}</div>` : ""}`;
    },

    approval(s) {
      const a = s.approval;
      return `<section class="approval" role="alertdialog" aria-label="${h("ui_w_waiting")}">
        <div class="ap-head"><h1 class="ap-word">${h("ui_w_waiting")}</h1><span class="ap-time ${a.secondsLeft <= 15 ? "urgent" : ""}">${h("ui_ap_seconds", { s: a.secondsLeft })}</span></div>
        <div class="ap-clock"><i style="--from:${a.secondsLeft / a.timeout};--secs:${a.secondsLeft}s"></i></div>
        <div class="ap-meta"><span><span class="chip who-${a.agent}">${h("ui_ap_asks", { agent: "@" + a.agent })}</span> &nbsp;${h("ui_round", { n: s.round, max: s.max })}</span>${risk(a.risk)}</div>
        <p class="ap-action"><span data-fit="36">${s.confirmRed ? h("ui_ap_confirm_red") : h(a.action, a.params)}</span></p>
        <div class="pads">
          <div class="pad yes"><i class="btn"></i><span>${h("ui_ap_green_top")}</span><strong>${h("ui_ap_green_main")}</strong></div>
          <div class="pad no"><i class="btn"></i><span>${h("ui_ap_red_top")}</span><strong>${h("ui_ap_red_main")}</strong></div>
        </div>
      </section>`;
    },

    frozen(s) {
      return `<section class="frozen" role="alert">
        ${UI.langBadge("corner")}
        <h1 class="word">${h(s.word)}</h1>
        <p>${h("ui_fz_body")}</p>
        <p class="step">${h("ui_fz_step")}</p>
      </section>`;
    },

    resume(s) {
      return `<section class="resume" role="alert">
        <div class="top"><h1 class="word" data-fit="64">${h(s.word)}</h1><p class="sub">${h("ui_rs_body")}</p></div>
        <div class="go">${h("ui_rs_step")}</div>
      </section>`;
    },

    scenario(s) {
      return `${bar(s)}<section class="choose">
        <h1 class="word" data-fit="56">${h(s.word)}</h1>
        <div class="years">
          <div class="year" style="--b:var(--approve)"><span>${h("ui_sc_green")}</span><strong>2020</strong></div>
          <div class="year" style="--b:var(--reject)"><span>${h("ui_sc_red")}</span><strong>2022</strong></div>
        </div>
      </section>`;
    },

    attract(s, prompt) {
      const other = UI.lang === "en" ? "zh" : "en";
      return `<section class="attract">
        ${UI.langBadge("corner")}
        <h1 class="head">${h("ui_at_head")}</h1>
        <p class="alt" lang="${other}">${h("ui_at_head", null, other)}</p>
        <div class="prompt"><small>${h("ui_at_try")}</small><strong data-prompt data-fit="32">${h("ui_at_prompt_" + (prompt + 1))}</strong></div>
        <div class="lamps">${UI.AGENTS.map((a) => `<i class="who-${a}"></i>`).join("")}</div>
      </section>`;
    },

    fault(s) {
      const f = "ui_f_" + s.fault;
      return `<section class="fault" role="alert">
        <div class="hatch"></div>
        <div class="body">
          <h1 data-fit="48">${UI.icon(UI.FAULT_ICON[s.fault])}${h(f + "_title")}</h1>
          <p>${h(f + "_body", { cap: s.cost ? s.cost.cap : 0 })}</p>
          <p class="next">${h(f + "_next")}</p>
        </div>
        <div class="foot"><span>${s.lastWord ? h("ui_f_api_last", { word: "@" + s.lastWord }) : ""}</span>${UI.langBadge()}</div>
        <div class="hatch" style="height:16px"></div>
      </section>`;
    },
  };

  UI.start((s, prompt) => layouts[s.layout](s, prompt));
})();
