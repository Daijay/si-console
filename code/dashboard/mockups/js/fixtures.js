/* Fake data, one entry per screen state. The shape here is the shape the
   proposed GET /api/ui/state snapshot should return (see docs/UI_SPEC.md).
   Screen text is never stored here: only string ids and parameters.
   The one exception is `said`, the visitor's own words from speech to text. */
(function () {
  const agents = (coord, a1, a2, guard) => ({ coord, a1, a2, guard });
  const OFF = agents("off", "off", "off", "off");
  const SAID = { en: "Buy XLK", zh: "买入 XLK" };

  const T = {
    you: { time: "14:02:09", who: "you", said: SAID },
    task: { time: "14:02:11", who: "coord", key: "ui_tx_task", params: { agent: "@a1" }, tool: 'create_task(task_id="signal-0007")' },
    rank: { time: "14:02:14", who: "a1", key: "ui_tx_rank", tool: 'rules_engine(replay_date="2022-12-30")' },
    prop: { time: "14:02:17", who: "a2", key: "ui_tx_propose", tool: 'propose_order(ticker="XLK", amount=2000)' },
    chk: { time: "14:02:19", who: "guard", key: "ui_tx_check", tool: "request_approval(order-0007)" },
    block: { time: "14:02:19", who: "guard", key: "ui_tx_block", tool: "shell_run: SHELL_DENY" },
    fill: { time: "14:02:31", who: "a2", key: "ui_tx_filled", tool: 'update_task_status("order-0007", "done")' },
  };

  const E = {
    ptt: ["14:02:09", "ui_ev_ptt"],
    task: ["14:02:11", "ui_ev_task", { id: "signal-0007" }],
    work: ["14:02:12", "ui_ev_working", { agent: "@a1", id: "signal-0007" }],
    tool: ["14:02:14", "ui_ev_tool", { tool: "rules_engine" }],
    ask: ["14:02:19", "ui_ev_approval", { id: "order-0007" }],
    green: ["14:02:30", "ui_ev_green"],
    red: ["14:02:30", "ui_ev_red"],
    done: ["14:02:31", "ui_ev_done", { id: "order-0007" }],
  };

  const ORDER = {
    agent: "a2", risk: "high", action: "ui_act_buy", why: "ui_why_rank",
    params: { amount: 2000, ticker: "XLK", months: 3 },
    secondsLeft: 107, timeout: 120,
    checks: [["ui_chk_kill", true], ["ui_chk_tool", true], ["ui_chk_risk_pass", true], ["ui_chk_human", true]],
    verdict: "ui_guard_pass",
    command: 'propose_order(ticker="XLK", amount=2000)',
  };

  const COST = { usd: 0.042, cap: 5, calls: 11 };
  const JUDGE = { score: 0.86, tier: "T2" };

  /* Graph edges: you-coord, coord-a1, coord-a2, a2-guard (also a1-guard), guard-button */
  const base = {
    layout: "status", word: "ui_w_ready", round: 0, max: 3, mode: "booth", agents: OFF,
    transcript: [], events: [], edges: {}, cost: COST, judge: null,
  };
  const make = (o) => Object.assign({}, base, o);

  const asked = {
    round: 2, agents: agents("done", "done", "working", "done"), judge: JUDGE,
    transcript: [T.you, T.task, T.rank, T.prop, T.chk], events: [E.ptt, E.task, E.work, E.tool, E.ask],
    edges: { "you-coord": "lit", "coord-a1": "lit", "coord-a2": "lit", "a2-guard": "lit", "guard-button": "active" },
  };
  const approval = (o) => make(Object.assign({ layout: "approval", word: "ui_w_waiting", approval: ORDER }, asked, o));
  const after = (o, extra) => make(Object.assign({}, asked, o, {
    events: o.events || asked.events.concat(extra || []),
  }));

  window.STATES = {
    boot: make({ word: "ui_w_boot", sub: "ui_sub_boot", dots: true, agents: agents("unknown", "unknown", "unknown", "unknown"), cost: null }),
    attract: make({ layout: "attract" }),
    scenario: make({ layout: "scenario", word: "ui_w_choose" }),
    ready: make({ word: "ui_w_ready", sub: "ui_sub_ready" }),
    listening: make({ word: "ui_w_listening", sub: "ui_sub_listening", mic: true, events: [] }),
    transcribing: make({ word: "ui_w_thinking", sub: "ui_sub_transcribing", dots: true, events: [E.ptt] }),
    "not-understood": make({ word: "ui_w_again", sub: "ui_sub_again", events: [E.ptt, ["14:02:10", "ui_ev_unknown"]], transcript: [{ time: "14:02:09", who: "you", said: { en: "Make me rich", zh: "让我发财" } }] }),
    thinking: make({
      word: "ui_w_thinking", sub: "ui_sub_thinking", subParams: { agent: "@coord" }, dots: true, round: 1,
      agents: agents("working", "queued", "off", "off"), transcript: [T.you], events: [E.ptt, E.task], edges: { "you-coord": "active" },
    }),
    working: make({
      word: "ui_w_thinking", sub: "ui_sub_working", subParams: { agent: "@a1" }, dots: true, round: 2, judge: JUDGE,
      agents: agents("done", "working", "queued", "off"), transcript: [T.you, T.task, T.rank], events: [E.ptt, E.task, E.work, E.tool],
      edges: { "you-coord": "lit", "coord-a1": "active" },
    }),
    approval: approval(),
    "approval-urgent": approval({ approval: Object.assign({}, ORDER, { secondsLeft: 9 }) }),
    "approval-medium": approval({
      agents: agents("done", "working", "off", "done"),
      edges: { "you-coord": "lit", "coord-a1": "lit", "a1-guard": "lit", "guard-button": "active" },
      transcript: [{ time: "14:02:09", who: "you", said: { en: "Make slides on 2022", zh: "做一份 2022 年的幻灯片" } }, T.task, { time: "14:02:19", who: "guard", key: "ui_tx_check", tool: "request_approval(narration-0008)" }],
      events: [E.ptt, E.work, ["14:02:19", "ui_ev_approval", { id: "narration-0008" }]],
      approval: Object.assign({}, ORDER, { agent: "a1", risk: "medium", action: "ui_act_slides", why: "ui_why_slides", params: { count: 3 }, command: 'make_slides(title="2022 bear market")', checks: [["ui_chk_kill", true], ["ui_chk_tool", true], ["ui_chk_human", true]] }),
    }),
    "reject-confirm": approval({ confirmRed: true }),
    approved: after({ word: "ui_w_approved", sub: "ui_sub_approved", dots: true, edges: { "you-coord": "lit", "coord-a2": "lit", "a2-guard": "lit", "guard-button": "lit" } }, [E.green]),
    done: after({
      word: "ui_w_done", sub: "ui_sub_done", subParams: { amount: 2000, ticker: "XLK" }, icon: "check", round: 3,
      agents: agents("done", "done", "done", "done"), transcript: asked.transcript.concat(T.fill),
      edges: { "you-coord": "lit", "coord-a1": "lit", "coord-a2": "lit", "a2-guard": "lit", "guard-button": "lit" },
    }, [E.green, E.done]),
    rejected: after({ word: "ui_w_rejected", sub: "ui_sub_rejected", icon: "cross", agents: agents("queued", "done", "blocked", "done"), edges: { "you-coord": "lit" } }, [E.red, ["14:02:30", "ui_ev_blocked", { id: "order-0007", code: "HUMAN_REJECT" }]]),
    expired: after({ word: "ui_w_expired", sub: "ui_sub_expired", icon: "clock", agents: agents("off", "done", "queued", "done"), edges: {} }, [["14:04:19", "ui_ev_expired", { id: "order-0007" }]]),
    "risk-blocked": after({
      word: "ui_w_blocked", sub: "ui_sub_risk", subParams: { reason: "@ui_reason_MAX_SECTOR" }, icon: "stop",
      agents: agents("done", "done", "blocked", "blocked"), edges: { "you-coord": "lit", "coord-a2": "lit", "a2-guard": "lit" },
      transcript: [T.you, T.task, T.rank, T.prop, Object.assign({}, T.block, { tool: "propose_order: MAX_SECTOR" })],
      events: [E.task, E.work, E.tool, ["14:02:20", "ui_ev_blocked", { id: "order-0007", code: "MAX_SECTOR" }]],
      verdictCard: { verdict: "ui_guard_block", checks: [["ui_chk_kill", true], ["ui_chk_tool", true], ["ui_chk_risk_fail", false]] },
    }),
    "guard-block": after({
      word: "ui_w_blocked", sub: "ui_sub_guard", subParams: { tool: "shell_run" }, icon: "stop", judge: null,
      agents: agents("done", "blocked", "off", "blocked"), edges: { "you-coord": "lit", "coord-a1": "lit", "a1-guard": "lit" },
      transcript: [T.you, T.task, T.block],
      events: [E.ptt, E.task, E.work, ["14:02:20", "ui_ev_blocked", { id: "signal-0007", code: "GUARD_BLOCK" }]],
      verdictCard: { verdict: "ui_guard_block", checks: [["ui_chk_kill", true], ["ui_chk_tool_deny", false]] },
    }),
    escalate: after({
      word: "ui_w_escalate", sub: "ui_sub_escalate", subParams: { max: 3 }, round: 3, judge: null,
      agents: agents("blocked", "off", "off", "off"), edges: { "you-coord": "lit" }, transcript: [T.you, T.task],
      events: [E.ptt, E.task, E.work, ["14:02:44", "ui_ev_blocked", { id: "signal-0007", code: "ROUND_LIMIT" }]],
    }),
    "task-blocked": after({
      word: "ui_w_stopped", sub: "ui_sub_stopped", subParams: { reason: "@ui_reason_STUCK" }, icon: "stop", judge: null,
      agents: agents("off", "blocked", "off", "off"), edges: { "you-coord": "lit", "coord-a1": "lit" }, transcript: [T.you, T.task],
      events: [E.ptt, E.task, E.work, ["14:07:12", "ui_ev_blocked", { id: "signal-0007", code: "STUCK" }]],
    }),
    "soft-freeze": make({ word: "ui_w_paused", sub: "ui_sub_paused", icon: "pause", agents: agents("queued", "off", "off", "off"), events: [E.ptt, ["14:02:10", "ui_ev_freeze"]], transcript: [{ time: "14:02:09", who: "you", said: { en: "Stop", zh: "停下" } }] }),
    frozen: make({ layout: "frozen", word: "ui_w_frozen", agents: agents("frozen", "frozen", "frozen", "frozen") }),
    resume: make({ layout: "resume", word: "ui_w_still_frozen", agents: agents("frozen", "frozen", "frozen", "frozen") }),
    "toast-no-proposal": make({ word: "ui_w_ready", sub: "ui_sub_ready", toast: "no_proposal" }),
    "toast-language": make({ word: "ui_w_ready", sub: "ui_sub_ready", toast: "language_switched" }),
    replay: make({
      word: "ui_w_thinking", sub: "ui_sub_working", subParams: { agent: "@a1" }, dots: true, round: 2, mode: "replay", banner: "ui_f_replay",
      agents: agents("done", "working", "queued", "off"), transcript: [T.you, T.task, T.rank], events: [["14:02:08", "ui_ev_net"], E.ptt, E.task, E.work],
      edges: { "you-coord": "lit", "coord-a1": "active" }, cost: COST,
    }),
    "api-down": make({ layout: "fault", fault: "api", word: "ui_w_offline", lastWord: "ui_w_thinking", agents: agents("unknown", "unknown", "unknown", "unknown"), cost: null }),
    "net-lost": make({ layout: "fault", fault: "net", word: "ui_w_offline", events: [["14:02:08", "ui_ev_net"]] }),
    "mic-missing": make({ layout: "fault", fault: "mic", word: "ui_w_novoice", events: [["14:02:08", "ui_ev_mic"]] }),
    "models-down": make({ layout: "fault", fault: "models", word: "ui_w_stopped", round: 1, agents: agents("blocked", "off", "off", "off"), events: [E.ptt, E.task, ["14:02:41", "ui_ev_models"]] }),
    "vault-error": make({ layout: "fault", fault: "vault", word: "ui_w_stopped", events: [["14:02:08", "ui_ev_vault"]] }),
    "cost-cap": make({ layout: "fault", fault: "cost", word: "ui_w_stopped", cost: { usd: 5, cap: 5, calls: 1291 }, events: [["17:40:02", "ui_ev_cost"]] }),
  };
})();
