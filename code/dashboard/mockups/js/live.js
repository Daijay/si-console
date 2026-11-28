/* Live adapter. Maps GET /api/ui/state into the same snapshot shape the
   mockups already render. Included only by mini.html and monitor.html;
   the frozen ?state=... pages keep using fixtures.js for review.
   Fail safe: any bad reply shows api-down, never a stale screen. */
(function () {
  if (!window.UI || !window.STATES) return;

  const DEFAULTS = window.STATES["ready"];
  const APPROVAL_BASE = window.STATES["approval"] || {};
  const OFFLINE = window.STATES["api-down"];

  /* The snapshot uses string ids, not sentences. UI.t resolves them.
     An unknown id must never be painted as a raw id: fall back to
     the offline screen instead. */
  const safe = (id) => {
    const langs = ["en", "zh"];
    return langs.every((l) => window.STRINGS[l] && window.STRINGS[l][id]);
  };

  function map(s) {
    if (!s || typeof s !== "object") throw new Error("bad snapshot");
    if (!safe(s.console_state)) throw new Error("bad console_state");
    const out = Object.assign({}, DEFAULTS, {
      layout: "status",
      word: s.console_state,
      round: Number(s.round) || 0,
      max: Number(s.max_rounds) || 3,
      mode: s.mode,
      agents: s.agents || DEFAULTS.agents,
      cost: s.cost || DEFAULTS.cost,
      judge: s.judge || null,
      said: s.said || "",
    });

    if (s.kill_active) out.word = "ui_w_frozen";
    else if (s.resume_required) out.word = "ui_w_still_frozen";
    else if (s.faults && s.faults.vault) out.word = "ui_w_offline";

    if (s.approval && !s.kill_active && !s.resume_required) {
      const a = s.approval;
      out.layout = "approval";
      out.word = "ui_w_waiting";
      out.approval = Object.assign({}, APPROVAL_BASE.approval || {}, {
        task_id: a.task_id,
        agent: a.agent,
        risk: a.risk,
        // The renderers call h(a.action, a.params): action must be the
        // string id, with its parameters alongside. The API's nested
        // {id, params} shape is unpacked here.
        action: (a.action && a.action.id) || "ui_act_buy",
        params: (a.action && a.action.params) || {},
        command: a.command || "",
        why: a.why || { id: "ui_why_rank", params: {} },
        checks: a.checks || [],
        verdict: a.verdict || "ui_guard_pass",
        secondsLeft: Number(a.secondsLeft) || 0,
        timeout: Number(a.timeout) || 120,
        reject_proposed: !!a.reject_proposed,
      });
      if (Number(a.secondsLeft) <= 20) out.word = "ui_w_expired";
    }

    if (s.outcome && s.outcome.id) out.outcome = s.outcome;
    if (s.faults && s.faults.cost_cap) out.word = "ui_w_offline";
    return out;
  }

  let lastOk = 0;
  let lastState = "";
  async function tick() {
    try {
      const response = await fetch("/api/ui/state", { cache: "no-store" });
      if (!response.ok) throw new Error("HTTP " + response.status);
      const snapshot = await response.json();
      const mapped = map(snapshot);
      lastOk = Date.now();
      window.STATES["live"] = mapped;
      window.UI.lang = snapshot.lang === "zh" ? "zh" : "en";
      if (window.UI.state !== "live") window.UI.state = "live";
      lastState = JSON.stringify(snapshot);
    } catch (err) {
      console.warn("ui snapshot:", err);
      /* Three missed polls (3 s) and the screen goes offline. A single
         hiccup must not cover an approval with a fault screen. */
      if (Date.now() - lastOk > 3000 || !lastState) {
        window.UI.state = "api-down";
      }
    }
    if (window.UI.paint) window.UI.paint();
  }

  window.UI.state = "live";
  tick();
  setInterval(tick, 1000);
})();
