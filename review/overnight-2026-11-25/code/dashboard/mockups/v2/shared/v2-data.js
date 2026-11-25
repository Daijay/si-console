// SI Console dashboard mockups v2. Shared data for all 5 directions.
// Static fixtures only. No server, no fetch, no keys.
// Every number is fake but plausible. Real shapes come from the
// Nov 23 scratch code: bridge.py, coordinator.py, guard.py, tools.py.
// Strings come from code/dashboard/strings.json (15 ids, EN + ZH).
// The repo copy of strings.json could not be re-read this run
// (GitHub read path rate limited, HTTP 429), so this file copies the
// Nov 23 strings.json text exactly. If the repo strings.json grew,
// merge the new ids here before building the real dashboard.
(function () {
  "use strict";

  var STRINGS = {
    en: {
      approval_expired: "Approval expired.",
      approval_pending: "Approval pending. Press green to approve, red to reject.",
      choose_scenario: "Choose scenario. Green is 2020. Red is 2022.",
      did_not_understand: "I did not understand. Please say it again.",
      escalate_to_human: "Escalate to human.",
      kill_active: "Kill active. All agents frozen.",
      language_switched: "Language switched.",
      no_proposal: "No proposal ready.",
      portfolio_ready: "Here is your portfolio value.",
      press_green_to_resume: "Kill released. Press green once to resume.",
      proposal_received: "Proposal received. Press green to approve, red to reject.",
      reject_proposed: "Reject proposed. Press red to confirm.",
      risk_blocked: "Risk blocked this proposal.",
      software_freeze: "Software freeze on. The physical kill switch is the real stop.",
      status_ready: "Here is the current status."
    },
    zh: {
      approval_expired: "批准已过期。",
      approval_pending: "等待批准。按绿色批准，按红色拒绝。",
      choose_scenario: "请选择场景。绿色是2020年，红色是2022年。",
      did_not_understand: "我没听懂，请再说一次。",
      escalate_to_human: "请人工处理。",
      kill_active: "急停已触发，所有智能体已冻结。",
      language_switched: "语言已切换。",
      no_proposal: "暂无提议。",
      portfolio_ready: "这是你的投资组合价值。",
      press_green_to_resume: "急停已解除，按一次绿色恢复。",
      proposal_received: "已收到提议。按绿色批准，按红色拒绝。",
      reject_proposed: "已提议拒绝。按红色确认。",
      risk_blocked: "风控阻止了这项提议。",
      software_freeze: "软件冻结已开启。物理急停才是真正的停止。",
      status_ready: "这是当前状态。"
    }
  };

  // 8 states every direction must cover, on both screens.
  var STATES = ["idle", "listening", "thinking", "approval", "approved", "rejected", "frozen", "error"];

  // Big state word per state, EN and ZH. Mini screen shows this at 64px+.
  var STATE_WORD = {
    idle: { en: "IDLE", zh: "待机" },
    listening: { en: "LISTENING", zh: "聆听中" },
    thinking: { en: "THINKING", zh: "思考中" },
    approval: { en: "APPROVAL", zh: "等待批准" },
    approved: { en: "APPROVED", zh: "已批准" },
    rejected: { en: "REJECTED", zh: "已拒绝" },
    frozen: { en: "FROZEN", zh: "已冻结" },
    error: { en: "OFFLINE", zh: "离线" }
  };

  // Sentence id spoken/shown per state. From strings.json only.
  var STATE_SENTENCE = {
    idle: "status_ready",
    listening: "status_ready",
    thinking: "status_ready",
    approval: "proposal_received",
    approved: "portfolio_ready",
    rejected: "reject_proposed",
    frozen: "kill_active",
    error: "did_not_understand"
  };

  // LED states per state. Values: on, blink, off.
  // COORD green, AGENT 1 white, AGENT 2 blue, GUARD yellow.
  var STATE_LEDS = {
    idle: { coord: "off", agent1: "off", agent2: "off", guard: "on" },
    listening: { coord: "blink", agent1: "off", agent2: "off", guard: "on" },
    thinking: { coord: "on", agent1: "blink", agent2: "off", guard: "on" },
    approval: { coord: "on", agent1: "on", agent2: "off", guard: "blink" },
    approved: { coord: "on", agent1: "on", agent2: "blink", guard: "on" },
    rejected: { coord: "on", agent1: "off", agent2: "off", guard: "on" },
    frozen: { coord: "blink", agent1: "off", agent2: "off", guard: "blink" },
    error: { coord: "off", agent1: "off", agent2: "off", guard: "blink" }
  };

  // Agent roster. Status per state is filled by stateRoster().
  var ROSTER = [
    { id: "coord", name: "COORD", color: "#2ecc71", role: "coordinator", tier: "coordinator" },
    { id: "agent1", name: "AGENT 1", color: "#e8ecf1", role: "signal", tier: "worker" },
    { id: "agent2", name: "AGENT 2", color: "#4aa8ff", role: "risk", tier: "worker" },
    { id: "guard", name: "GUARD", color: "#f5c542", role: "guard", tier: "code" },
    { id: "hermes", name: "HERMES", color: "#b48cff", role: "external", tier: "research only" }
  ];

  var ROSTER_STATUS = {
    idle: { coord: "idle", agent1: "idle", agent2: "idle", guard: "watching", hermes: "idle" },
    listening: { coord: "listening", agent1: "idle", agent2: "idle", guard: "watching", hermes: "idle" },
    thinking: { coord: "routing", agent1: "working", agent2: "idle", guard: "watching", hermes: "idle" },
    approval: { coord: "waiting", agent1: "done", agent2: "done", guard: "checking", hermes: "idle" },
    approved: { coord: "routing", agent1: "idle", agent2: "working", guard: "watching", hermes: "idle" },
    rejected: { coord: "routing", agent1: "idle", agent2: "idle", guard: "watching", hermes: "idle" },
    frozen: { coord: "frozen", agent1: "frozen", agent2: "frozen", guard: "frozen", hermes: "frozen" },
    error: { coord: "offline", agent1: "offline", agent2: "offline", guard: "watching", hermes: "offline" }
  };

  // Sector rotation, paper portfolio, 2022 replay scenario.
  // Tickers are the real allow list from config.py. Prices and
  // changes are fake, dated to the 2022 replay week.
  var SCENARIO = {
    mode: "booth",
    replay: "2022",
    replayWeek: "2022-06-13",
    portfolioStart: 100000,
    portfolioValue: 98412.55,
    portfolioDay: -412.30,
    portfolioDayPct: -0.42,
    cash: 23150.00
  };

  var SECTORS = [
    { ticker: "XLE", name: "Energy", price: 88.42, chg: 2.31 },
    { ticker: "XLU", name: "Utilities", price: 71.08, chg: 0.84 },
    { ticker: "XLP", name: "Staples", price: 76.55, chg: 0.41 },
    { ticker: "XLV", name: "Health", price: 131.20, chg: 0.12 },
    { ticker: "XLB", name: "Materials", price: 84.17, chg: -0.33 },
    { ticker: "XLI", name: "Industrials", price: 99.64, chg: -0.58 },
    { ticker: "XLF", name: "Financials", price: 33.91, chg: -0.72 },
    { ticker: "XLK", name: "Tech", price: 132.86, chg: -1.94 },
    { ticker: "XLY", name: "Discretionary", price: 141.03, chg: -2.18 },
    { ticker: "XLRE", name: "Real Estate", price: 41.77, chg: -1.05 },
    { ticker: "XLC", name: "Comms", price: 58.29, chg: -1.62 }
  ];

  // Task queue. Shapes from vault.py TaskNote: id, agent, type,
  // status, ticker, amount, round, risk_check. Order-book style:
  // queued = bids, working = fills in progress, done = fills.
  var TASKS = [
    { id: "sig-0142", agent: "signal", type: "signal", status: "done", ticker: "XLE", amount: 12500, round: 2, risk: "pass", note: "RRG: XLE leading" },
    { id: "risk-0142", agent: "risk", type: "risk_check", status: "done", ticker: "XLE", amount: 12500, round: 1, risk: "pass", note: "cap 12.5% ok" },
    { id: "ord-0142", agent: "execution", type: "order", status: "working", ticker: "XLE", amount: 12500, round: 1, risk: "pass", note: "awaiting green" },
    { id: "res-0143", agent: "signal", type: "research", status: "queued", ticker: "XLU", amount: 0, round: 0, risk: "-", note: "Bocha: utilities" },
    { id: "nar-0143", agent: "coordinator", type: "narration", status: "queued", ticker: "", amount: 0, round: 0, risk: "-", note: "speak proposal" },
    { id: "sig-0144", agent: "signal", type: "signal", status: "queued", ticker: "XLK", amount: 0, round: 0, risk: "-", note: "weekly scan" }
  ];

  // The pending proposal. The approval state shows this.
  // Risk gauge 0-100. Approval expires after 120 s (ASSUMED).
  var PROPOSAL = {
    taskId: "ord-0142",
    action: "BUY",
    ticker: "XLE",
    shares: 141,
    price: 88.42,
    amount: 12500,
    riskScore: 23,
    riskLabel: "LOW",
    riskCheck: "pass",
    capUsedPct: 12.5,
    capMaxPct: 25.0,
    approvalExpiresS: 120,
    approvalLeftS: 87
  };

  // Meters. DeepSeek daily cap is $5.00 (config.py default).
  // Latency and tokens are fake, in the range the Nov 23 code sees.
  var METERS = {
    deepseekMs: 1840,
    deepseekModel: "deepseek-flash",
    tokensIn: 1842,
    tokensOut: 317,
    costTodayUsd: 1.84,
    costCapUsd: 5.00,
    bochaMs: 620,
    roundUsed: 2,
    roundMax: 3,
    api: "DeepSeek",
    apiStatus: "ok"
  };

  // Event tape. One line per real event type the system emits:
  // tool calls, GUARD checks, rounds, claims, button presses.
  var TAPE = [
    { t: "11:42:07", who: "COORD", text: "create_task sig-0142" },
    { t: "11:42:09", who: "AGENT 1", text: "run_rules_engine XLE +2.31%" },
    { t: "11:42:11", who: "AGENT 1", text: "web_search utilities Bocha 620ms" },
    { t: "11:42:14", who: "AGENT 2", text: "risk_check pass cap 12.5%" },
    { t: "11:42:15", who: "GUARD", text: "check_tool propose_order SAFE" },
    { t: "11:42:16", who: "COORD", text: "request_approval ord-0142" },
    { t: "11:42:16", who: "GUARD", text: "approval pending, 120s" },
    { t: "11:42:19", who: "COORD", text: "speak_sentence proposal_received" }
  ];

  // Voice waveform levels, 0-100, one per bar. Active in listening.
  var WAVEFORM = [12, 28, 44, 62, 78, 88, 72, 55, 38, 24, 16, 30, 52, 70, 84, 66, 42, 22, 10, 18, 36, 58, 74, 60, 40, 26];

  // Error state facts. error/offline shows the last failure.
  var ERROR = {
    code: "API_TIMEOUT",
    text: "DeepSeek did not answer in 15s. Recorded fallback ready.",
    retryInS: 5,
    lastOk: "11:41:58"
  };

  // Attract mode lines for idle. Shown to strangers at the booth.
  var ATTRACT = {
    line1: "TALK TO DISPATCH.",
    line2: "PRESS TO APPROVE.",
    line3: "Hold the mic button and speak. The agents work. You press the green button."
  };

  // Panel labels, EN and ZH. Sentences live in strings.json. Labels
  // are UI chrome, not sentences, so they live here. Renderers must
  // look labels up by lang, never hardcode English panel titles.
  var LABELS = {
    en: {
      taskQueue: "TASK QUEUE — ORDER BOOK",
      orderBook: "ORDER BOOK — TASK QUEUE",
      risk: "RISK — PENDING ACTION",
      agents: "AGENT ROSTER",
      meters: "LATENCY / TOKENS / COST",
      sectors: "SECTORS",
      tape: "EVENT TAPE",
      portfolio: "PORTFOLIO",
      costToday: "COST TODAY",
      countdown: "COUNTDOWN",
      round: "ROUND",
      handoff: "HANDOFF",
      voice: "VOICE — PUSH TO TALK",
      hardware: "HARDWARE",
      top: "TOP",
      fills: "FILLS",
      bids: "BIDS"
    },
    zh: {
      taskQueue: "任务队列 · 订单簿",
      orderBook: "订单簿 · 任务队列",
      risk: "风险 · 待处理操作",
      agents: "智能体名单",
      meters: "延迟 / 令牌 / 成本",
      sectors: "板块",
      tape: "事件记录",
      portfolio: "投资组合",
      costToday: "今日成本",
      countdown: "倒计时",
      round: "回合",
      handoff: "交接",
      voice: "语音 · 按住说话",
      hardware: "硬件",
      top: "热门",
      fills: "已成交",
      bids: "委托"
    }
  };

  function label(key, lang) {
    var l = LABELS[lang === "zh" ? "zh" : "en"];
    return l[key] || LABELS.en[key] || key;
  }

  // The event tape is one static fixture in v1, which shows approval
  // events during idle. That is wrong. The tape follows the state:
  // idle shows boot events only, thinking shows the run up to the
  // risk check, approval shows the full run, approved and rejected
  // and frozen append their own closing event, error shows the
  // timeout. Renderers show the last N entries of this list.
  function tapeForState(state) {
    var boot = [
      { t: "11:41:58", who: "BRIDGE", text: "vault scan complete, 6 tasks" },
      { t: "11:41:59", who: "GUARD", text: "watching, kill off" }
    ];
    var run = [
      { t: "11:42:07", who: "COORD", text: "create_task sig-0142" },
      { t: "11:42:09", who: "AGENT 1", text: "run_rules_engine XLE +2.31%" },
      { t: "11:42:11", who: "AGENT 1", text: "web_search utilities Bocha 620ms" },
      { t: "11:42:14", who: "AGENT 2", text: "risk_check pass cap 12.5%" },
      { t: "11:42:15", who: "GUARD", text: "check_tool propose_order SAFE" },
      { t: "11:42:16", who: "COORD", text: "request_approval ord-0142" },
      { t: "11:42:16", who: "GUARD", text: "approval pending, 120s" },
      { t: "11:42:19", who: "COORD", text: "speak_sentence proposal_received" }
    ];
    if (state === "idle") return boot;
    if (state === "listening") return boot.concat([
      { t: "11:42:05", who: "COORD", text: "PTT pressed, mic open" }
    ]);
    if (state === "thinking") return boot.concat(run.slice(0, 4));
    if (state === "approval") return boot.concat(run);
    if (state === "approved") return boot.concat(run).concat([
      { t: "11:42:21", who: "EXECUTION", text: "fill ord-0142 141 XLE @ 88.42" }
    ]);
    if (state === "rejected") return boot.concat(run).concat([
      { t: "11:42:21", who: "COORD", text: "HUMAN_REJECT ord-0142 blocked" }
    ]);
    if (state === "frozen") return boot.concat(run).concat([
      { t: "11:42:20", who: "GUARD", text: "KILL_SWITCH all working blocked" }
    ]);
    if (state === "error") return boot.concat(run.slice(0, 4)).concat([
      { t: "11:42:17", who: "DEEPSEEK", text: "API_TIMEOUT 15s, retry 5s" }
    ]);
    return boot.concat(run);
  }

  // Cash follows the state. In approved the fill went through, so
  // cash is start cash minus the order amount (23150 - 12500 =
  // 10650). The portfolio total does not change: cash 10650 +
  // positions 87762.55 = 98412.55. Every other state shows start
  // cash. Renderers must use this for every cash display, never
  // SCENARIO.cash directly.
  function cashForState(state) {
    return state === "approved" ? SCENARIO.cash - PROPOSAL.amount : SCENARIO.cash;
  }

  // Helpers. Renderers use these, they do not reimplement them.
  function money(n) {
    return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  function signed(n, suffix) {
    var s = (n >= 0 ? "+" : "") + n.toFixed(2) + (suffix || "");
    return s;
  }
  function pct(n) {
    return (n >= 0 ? "+" : "") + n.toFixed(2) + "%";
  }
  // The task queue is one static fixture, but the order task follows
  // the state, the same way the real bridge does. On approved the
  // order fills. On rejected it blocks with HUMAN_REJECT. On frozen
  // the kill switch blocks every working task with KILL_SWITCH
  // (bridge.py on_kill). Renderers must call this, not TASKS, when
  // they show the queue.
  function tasksForState(state) {
    return TASKS.map(function (t) {
      var c = {};
      Object.keys(t).forEach(function (k) { c[k] = t[k]; });
      if (t.id === "ord-0142") {
        if (state === "approved") { c.status = "done"; c.note = "filled 11:42:21"; }
        if (state === "rejected") { c.status = "blocked"; c.note = "rejected by human"; }
        if (state === "frozen") { c.status = "blocked"; c.note = "blocked KILL_SWITCH"; }
      }
      return c;
    });
  }
  function stateSnapshot(state, lang) {
    lang = lang === "zh" ? "zh" : "en";
    return {
      state: state,
      lang: lang,
      word: STATE_WORD[state][lang],
      sentence: STRINGS[lang][STATE_SENTENCE[state]],
      sentenceId: STATE_SENTENCE[state],
      leds: STATE_LEDS[state],
      rosterStatus: ROSTER_STATUS[state],
      strings: STRINGS[lang]
    };
  }

  window.V2 = {
    STRINGS: STRINGS,
    STATES: STATES,
    STATE_WORD: STATE_WORD,
    STATE_SENTENCE: STATE_SENTENCE,
    STATE_LEDS: STATE_LEDS,
    ROSTER: ROSTER,
    ROSTER_STATUS: ROSTER_STATUS,
    SCENARIO: SCENARIO,
    SECTORS: SECTORS,
    TASKS: TASKS,
    PROPOSAL: PROPOSAL,
    METERS: METERS,
    TAPE: TAPE,
    WAVEFORM: WAVEFORM,
    ERROR: ERROR,
    ATTRACT: ATTRACT,
    money: money,
    signed: signed,
    pct: pct,
    tasksForState: tasksForState,
    tapeForState: tapeForState,
    cashForState: cashForState,
    label: label,
    stateSnapshot: stateSnapshot
  };
})();
