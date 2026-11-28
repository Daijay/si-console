/* Node smoke test for js/live.js. No browser, no network: it loads the
   real strings and fixtures, feeds a live snapshot through the adapter
   and checks that the approval command survives to the render state.
   Run from code/: node dashboard/mockups/js/test-live.js
*/
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const here = __dirname;
const read = (f) => fs.readFileSync(path.join(here, f), "utf8");

const ctx = {
  console,
  window: {},
  document: { body: { dataset: {} }, documentElement: {} },
  location: { search: "" },
  fetch: async () => ({ ok: true, status: 200, json: async () => snapshot }),
  setInterval: () => 0,
  Date,
  URLSearchParams,
  JSON,
  Object,
  Number,
  Error,
};
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(read("strings.js"), ctx);
vm.runInContext(read("fixtures.js"), ctx);
vm.runInContext(`window.UI = { lang: "en", state: "ready", paint() {} };`, ctx);
// common.js defines UI.h / UI.t but calls UI.start at load time. Stub it.
vm.runInContext(`UI.start = (render) => { captured = render; };`, ctx);
vm.runInContext(read("common.js"), ctx);

const snapshot = {
  console_state: "ui_w_waiting",
  round: 2,
  max_rounds: 3,
  mode: "booth",
  replay: "2022",
  lang: "en",
  agents: { coord: "done", a1: "done", a2: "working", guard: "done" },
  kill_active: false,
  resume_required: false,
  software_freeze: false,
  approval: {
    task_id: "order-001",
    agent: "a2",
    risk: "high",
    action: { id: "ui_act_buy", params: { ticker: "XLK", amount: 2000 } },
    command: "update_task_status(order-001, done)",
    checks: [["ui_chk_human", true]],
    verdict: "ui_guard_pass",
    expires_at: "2026-11-28T12:00:00+00:00",
    secondsLeft: 96,
    timeout: 120,
    reject_proposed: false,
  },
  cost: { usd: 0.04, cap: 5, calls: 11 },
  judge: null,
  faults: { net: false, mic: false, models: false, vault: false, cost_cap: false },
  said: "",
};

vm.runInContext(read("live.js"), ctx);

setImmediate(() => {
  // Render the live state through the real mini renderer and check that
  // the exact command lands in the markup, escaped and verbatim.
  // common.js replaced the stub with the real UI.start; put it back
  // so mini.js hands us its renderer without touching the DOM.
  vm.runInContext(`UI.start = (render) => { captured = render; };`, ctx);
  vm.runInContext(read("mini.js"), ctx);
  const html = vm.runInContext(`captured(window.STATES.live, 0)`, ctx);
  const live = ctx.window.STATES.live;
  const fail = (msg) => {
    console.error("FAIL:", msg);
    process.exit(1);
  };
  if (!live) fail("no live snapshot");
  if (live.layout !== "approval") fail("layout is not approval");
  if (live.approval.command !== snapshot.approval.command)
    fail("approval command was lost");
  if (live.approval.secondsLeft !== 96) fail("secondsLeft was lost");
  if (ctx.window.UI.state !== "live") fail("UI did not switch to live");
  if (!html.includes("update_task_status(order-001, done)"))
    fail("exact command is missing from the rendered approval screen");
  console.log(
    "live adapter OK: command, countdown and layout reached the rendered screen"
  );
});
