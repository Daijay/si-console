# UI spec

Mockups with fake data only. Nothing is wired to the live system, and `code/si_console/` is unchanged.

- Mockups: [`code/dashboard/mockups/`](../code/dashboard/mockups/) (open `index.html`; on a state page `L` switches language, arrow keys step through states)
- Screenshots: [`docs/images/ui/`](images/ui/) as `mini/<state>-<en|zh>.png` and `monitor/<state>-<en|zh>.png`
- Research: [UI_RESEARCH.md](UI_RESEARCH.md)

## 1. Direction

Three studies, each with 5 inch idle, 5 inch approval and monitor views.

| | A, flight deck | B, cyberdeck terminal | C, product panel |
|---|---|---|---|
| Look | Dark, cockpit type, colour only for state and identity | Amber monospace, dashed rules, text tree | Light grey, round lamps, pill buttons |
| Screenshots | [idle](images/ui/directions/a-flightdeck-idle.png), [approval](images/ui/directions/a-flightdeck-approval.png), [monitor](images/ui/directions/a-flightdeck-monitor.png) | [idle](images/ui/directions/b-cyberdeck-idle.png), [approval](images/ui/directions/b-cyberdeck-approval.png), [monitor](images/ui/directions/b-cyberdeck-monitor.png) | [idle](images/ui/directions/c-product-idle.png), [approval](images/ui/directions/c-product-approval.png), [monitor](images/ui/directions/c-product-monitor.png) |
| Readable at 2 m | State word yes | Headline only; agent rows far too small | State word yes |
| Colour as state | Clear, but idle outlines looked lit | One amber hue flattens everything | White lamp vanishes on light grey; faded lamps look half on |
| Approval hard to miss | Strong split, but "waiting for you" was a small header | Weakest: two lines of text | Strong, friendly, physical |
| On camera | Good | Moody, thin text breaks up | Glare risk from a large light field |
| Matches hardware | Yes | Best match for the open frame look | Looks like another product |

**Chosen: A, with two borrowings.** A gives the clearest state reading with room for evidence. From B: monospace tool call lines with timestamps. From C: round button symbols on the approval pads, in the same left and right order as the real buttons. Fixed after critique: idle tiles are now dark with a thin colour bar, so lit means working; "Waiting for you" is the largest line of the takeover; the pulsing white frame was added.

The study screenshots use fake data and predate the final copy and layout, so they differ from the final screens.

## 2. Stack and tokens

One static web stack (HTML, CSS, plain JavaScript, no build framework), meant to be served by the existing FastAPI bridge, with one Chromium kiosk window per display.

| Page | Display | Kiosk URL (proposed) |
|---|---|---|
| `mini.html` | 5 inch, 800x480, no touch | `http://127.0.0.1:8001/ui/mini.html` |
| `monitor.html` | 15.6 inch, 1920x1080 | `http://127.0.0.1:8001/ui/monitor.html` |

- `theme/tokens.css` imports the existing `../../theme.css` for the ground, surface and ember brand colour, then adds state colours and fonts.
- All screen text comes from `code/dashboard/strings.json`, keys starting `ui_`. The spoken sentence ids are unchanged. System lines are sent as string id plus parameters, so switching language redraws instantly with no request. The visitor's own words are shown as recognised. Tool names and task ids are not translated.
- `tools/build.py` writes `js/strings.js` and the state pages. `tools/fonts.py` rebuilds the font subsets; run it after adding Chinese text.
- Live build notes: fetch `strings.json` instead of using `strings.js`; update only changed elements, because the mockup redraws the whole screen and would restart animations; install `fonts-noto-cjk` so speech outside the subset still renders.

| Token | Value | Job | Contrast |
|---|---|---|---|
| ink on ground | `#f4f6f8` on `#0e1013` | primary text | 17.6:1 |
| secondary on ground | `#bcc4cf` | detail text | 10.8:1 |
| approve / COORD | `#3ddc84`, text `#07090b` | green pad, COORD tile | 11.2:1 |
| reject | `#c4151c`, text white | red pad | 6.0:1 |
| kill | `#b30f16`, text white | frozen screen | 7.0:1 |
| AGENT 1 | `#f4f6f8` | tile | 18.4:1 |
| AGENT 2 | `#5aa9ff` | tile | 8.1:1 |
| GUARD | `#ffd23f` | tile, verdict text | 13.8:1 |
| ember | `#d09256` | product name, prompt rule | 7.2:1 |
| graph arrow | `#66707f` | idle handoff | 3.8:1 non-text |

Idle tile and panel borders (`#3a424e`, 1.9:1) are decoration; the name and status word carry the state.

## 3. Screens

### 5 inch status screen

Top bar (mode, round `n/3`, EN/中文), state area, four agent tiles in LED order. Takeovers replace everything: approval, frozen, resume, faults, attract. Green is drawn left of red.

### Monitor

Header (state word, round, language). Left: conversation with tool calls, plus mic level while talk is held. Centre: handoff graph (You, COORD, AGENT 1 and AGENT 2, GUARD, Your button) and event log. Right: approval card (action, risk tier, requesting agent, why, GUARD verdict and checks) or the latest result, then cost meter and judge score. During approval a full width footer repeats the two button instructions.

### Distance reading, 5 inch panel at 2 m

| Element | Size | Approx. visual angle | Verdict |
|---|---|---|---|
| State word, most states | 134 to 172 px | 24 to 31 arcmin | Reads |
| Longest English words (NEEDS A PERSON, replay) | 112 to 116 px | 20 arcmin | Reads |
| STILL FROZEN | 96 px | 17 arcmin | Marginal |
| APPROVE and REJECT | 80 px | 14 arcmin | Marginal in English; colour and position carry it |
| 批准 and 拒绝 | 96 px | about 20 arcmin | Reads |
| Choose a year | 76 px | 13 arcmin | Marginal; the years below are larger |
| WAITING FOR YOU in the takeover | 58 px | 10 arcmin | Reads from about 1.2 m |
| Tile labels and sentences | 24 to 36 px | 4 to 6 arcmin | Close range only |

These are calculations, not a test on the real panel. A five inch screen cannot carry the whole approval sentence at 2 m.

## 4. States and what drives them

"Today" means the signal exists in the skeleton. "Missing" means the bridge needs new work (section 7).

| State id | Shows | Driver today | Missing |
|---|---|---|---|
| boot | Starting, tiles "no signal" | none | first snapshot not yet received |
| attract | Both languages, rotating prompt, lamps | none | UI timer: 30 s with no events |
| scenario | Green 2020, red 2022 | `on_green_press` docstring only; no tasks yet | scenario state and red/green handling |
| ready | READY | `state.json` `current_status` empty | console state field |
| listening | LISTENING, mic level | none (GPIO23 mapped only) | `ptt` event, mic level stream |
| transcribing | THINKING | none | speech to text events |
| not-understood | SAY IT AGAIN | `match_intent` returns `unknown`, sentence `did_not_understand` | publish result |
| thinking | THINKING, COORD alive | `current_agent`, `current_status=working`; note `round` | per agent status, round |
| working | THINKING, worker alive | same | handoff events |
| approval | Takeover, high risk | `approval_pending`, `current_task_id`, `request_approval()` | action, command, agent, risk, why, checks, expiry |
| approval-urgent | Same, last 15 s inverted timer | none | `expires_at`, 120 s timeout |
| approval-medium | Same, medium risk | `tools.py` tag NEEDS APPROVAL | risk tier definition |
| reject-confirm | Red half enlarged | intent `reject_proposal` | `reject_proposed` flag |
| approved | APPROVED | `on_green_press` returns `approved` | event |
| done | DONE and result | task `status=done` | result parameters |
| rejected | REJECTED | `on_red_press`, `HUMAN_REJECT` | event |
| expired | EXPIRED | sentence `approval_expired` | the timeout itself |
| risk-blocked | BLOCKED, green does nothing | `risk_check=fail`, `risk_reason` | verdict and reason in snapshot |
| guard-block | BLOCKED, tool named | `GuardError` `GUARD_BLOCK` or `SHELL_DENY` in the loop log | verdict event |
| escalate | NEEDS A PERSON | `_escalate`, `ROUND_LIMIT`; `EscalationNeeded` | event |
| task-blocked | STOPPED with reason | `risk_reason` (STUCK, TOOL_TIMEOUT, POWER_LOSS and others) | translated reason strings for the rest of the codes |
| soft-freeze | PAUSED, switch is the real stop | intent `stop` | `software_freeze` field |
| frozen | Full red FROZEN | `kill_active` from `on_kill(True)`, `/api/health` | GPIO wiring, push event |
| resume | STILL FROZEN, press green | `resume_required` in `state.json` | expose in snapshot |
| toast-no-proposal | Toast over tiles | green or red returns `NO PROPOSAL READY` | event |
| toast-language | Toast | sentence `language_switched` | toggle handler, `lang` push |
| replay | Banner "recorded run" | `MODE`, replay settings | recorder, player, replay flag |
| api-down | Console offline, last seen state | request failure in the browser | 1 s heartbeat; offline after 3 s |
| net-lost | No internet, no recording fits | `ModelError` | network probe |
| mic-missing | Voice off | none | microphone probe |
| models-down | All providers failed | `ModelError` after the chain, `ZeroPathNeeded` | fault flag |
| vault-error | Task store error | `last_error="VAULT ERROR"` | fault flag |
| cost-cap | Budget used | `DEEPSEEK_DAILY_CAP_USD` setting only | enforcement and flag |

**Priority when several apply:** api-down, frozen, resume, vault-error, approval (and reject-confirm), soft-freeze, listening, transcribing, latest outcome (hold 8 s), cost-cap, models-down, net-lost, thinking or working, mic-missing, scenario, ready, attract. A missing mic or lost network must never cover an approval; in that case only the event log records it. A small badge for it on the approval screen is not mocked.

**Fail safe:** an unknown or malformed snapshot renders the offline screen.

**Offline wording:** the screen does not claim the buttons or kill switch work when it cannot reach the bridge, because the kill switch is read by software.

**Tile rules** mirror `GPIO_PIN_MAP.md`: no task = idle, working = solid, queued = slow blink, blocked = fast blink, kill = all off.

## 5. Motion

Only `transform` and `opacity` are animated (checked in the browser across all states). No canvas, WebGL, blur or JavaScript frame loop.

| Motion | Timing | Why |
|---|---|---|
| Working agent halo (tile and node) | 1600 ms ease-in-out loop | This one is alive |
| Queued marker blink | 2000 ms, stepped (0.5 Hz) | Same meaning as the slow LED |
| Blocked marker blink | 500 ms, stepped (2 Hz) | Matches fast LED, below 3 flashes per second |
| State word entrance | 200 ms, strong ease-out, 12 px rise | Shows the word changed |
| Approval takeover | 180 ms ease-out, scale 0.97 to 1 | Arrives from nowhere less abruptly |
| Approval frame pulse | 1000 ms loop | Peripheral attention while a person must act |
| Approval countdown | linear over remaining seconds, `scaleX` | Time left |
| Handoff packets | 900 ms linear, two dots 450 ms apart, active edge only | Direction of work. Lit edge without dots means finished |
| Thinking dots | 1200 ms, 200 ms stagger | Waiting without a fake progress bar |
| Mic bars | mockup 420 ms loop; live: set `scaleY` from the level, 60 ms linear | Proof the mic hears you |
| Toast | 250 ms in, hold 3 s (hold is for the live build), then remove | Momentary notice |
| Cost and judge meters | 300 ms ease-out | Value changed |
| Attract lamps | 6000 ms breathe, 750 ms stagger | Visible across the room |
| Attract prompt | changes every 6000 ms with the 200 ms entrance | Three examples |
| Frozen, resume, faults | none | Stillness reads as stopped, and the stop is never delayed |

`prefers-reduced-motion` switches all loops off. `?still` does the same for screenshots. Performance on a Pi 5 driving both displays is not measured.

## 6. Booth copy

Prompts must be recognised by `voice_intents.match_intent`, so they were run through it:

| English | Chinese | Intent |
|---|---|---|
| Buy XLK | 买入 XLK | propose_sector_move |
| Show my portfolio value | 查看投资组合市值 | ask_portfolio_value |
| Give me a status report | 现在状态 | ask_status |

The documented example "Research the 2022 bear market and make 3 slides" returns `unknown`, and so does "What is my portfolio value?" because questions are rejected. If speech to text adds a question mark, otherwise good phrases will fail. The medium risk mockup shows a slides request that needs an intake the matcher does not have yet.

Chinese text has not been reviewed by a native speaker.

## 7. Missing bridge work

### Endpoints

| Proposed | Why the current API cannot do it |
|---|---|
| Static mount `/ui/` for pages, fonts and `strings.json` | The bridge serves no files. Docs mention a dashboard on port 8000; this design assumes one server, owners to confirm |
| `GET /api/ui/state`, loopback only, no token, no shared rate limit, on in booth mode | `GET /api/state` needs the external agent token and shares a limit of 10 requests per minute; task routes return 403 in booth mode |
| `GET /api/ui/events` (server-sent events): `state`, `transcript`, `handoff`, `tool`, `log`, `toast`, `heartbeat` every 1 s | No push channel exists |
| `GET /api/ui/mic` stream, about 15 Hz while talk is held | No audio path exists |
| `GET /api/ui/telemetry`: cost today, cap, call count, latest judge choice and confidence | No route; `telemetry.py` does not store the judge's confidence |

There is deliberately **no** approve, reject or kill endpoint. Screens are read only; buttons stay on GPIO.

### Snapshot fields

`console_state, round, max_rounds, mode, replay, lang, agents{coord,a1,a2,guard}, kill_active, resume_required, software_freeze, approval{task_id, agent, risk, action{id,params}, command, why{id,params}, checks[], verdict, expires_at, reject_proposed}, outcome{code, params}, cost{usd, cap, calls}, judge{score, tier}, faults{net, mic, models, vault, cost_cap}, said`

`js/fixtures.js` is a working example of the shape. It uses short names (`secondsLeft`, `action`, `params`) that the live adapter should map.

### Behaviour the screens depend on

- No GPIO layer calls `on_green_press`, `on_red_press` or `on_kill`, and nothing drives the LEDs, push to talk or the language toggle.
- 2026-11-28: the coordinator writes `approval_request.json` and waits; the bridge polls it and arms the green button. Screens still need to render `approval.command`.
- 2026-11-28: the 120 s expiry is decided. The bridge blocks the task with `HUMAN_TIMEOUT`, runs nothing and never revives it.
- 2026-11-28: `GET /api/ui/state` and the static `/ui/` mount are live, loopback only, no token. `js/live.js` maps the snapshot into the existing fixture shape; a bad snapshot shows api-down. The exact approval command is rendered verbatim (escaped) on both screens. No approve/reject/kill endpoint exists.
- Risk tiers do not exist. Proposed: high = changes the portfolio, medium = writes a file or runs a command.
- The mapping of code roles to LEDs is not written in code. Assumed: coordinator = COORD, signal = AGENT 1, execution = AGENT 2, risk = GUARD.
- The daily cost cap is configured but not enforced.
- The offline recorded run does not exist yet.

## 8. How it was checked

A Playwright script loaded every state in both languages (132 screens) and reported: text contrast against its background (lowest 6.0:1), text outside the screen or its panel, overlapping text, overflowing boxes, raw string ids, failed fonts, console errors and any network request. Final run: 0 issues. It also confirmed that `L` switches language, an unknown state shows the offline screen, and running animations touch only `transform` and `opacity`. The script lives outside the repo.

Three refine passes followed the first build: (1) missing state words, monitor height overflow, action line under the frame, toast placement; (2) clipped footer pads, short handoff arrows, wrapped labels, code font, contradictory headings; (3) fake data that contradicted itself, a squeezed right column, larger approval verbs for distance reading.

Not checked: the real 5 inch panel and monitor, a Pi 5, a person at 2 m, camera footage, a screen reader, a native Chinese reader.
