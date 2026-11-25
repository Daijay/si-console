# UI v2 comparison: 5 directions

Status: DRAFT. Written 2026-11-25 during the overnight UI v2 run.
All 5 directions are static HTML in review/overnight-2026-11-25/code/dashboard/mockups/v2/, each
with both screens (5 inch 800x480 mini, 15.6 inch 1920x1080 monitor)
and all 8 states (idle, listening, thinking, approval, approved,
rejected, frozen, error). 90 screenshots in review/overnight-2026-11-25/docs/images/ui/v2/ (18
per direction: 8 states x 2 screens in English, plus approval in
Chinese on both screens). Shared data in
review/overnight-2026-11-25/code/dashboard/mockups/v2/shared/v2-data.js. Every number is fake
but plausible, shaped by the real code (bridge.py, coordinator.py,
guard.py, tools.py) and the real strings.json sentence ids.

How this was judged: as a stranger at a loud Maker Faire booth
(can I understand it in 5 seconds from 2 m?), as a judge on camera
(does it tell the safety story?), and by WCAG AA contrast (computed
ratios, all pairs 4.5 to 1 or better) and Chinese fit (approval shot
in zh on both screens per direction).

## Ranked recommendation

1. Mission. 2. Orderbook. 3. Terminal. 4. HUD. 5. Heatmap.

Pick Mission as the base for the real dashboard. Take the order
book panel from Orderbook and the hardware legend from Terminal.
Keep HUD as the attract-mode ring for idle only. Keep Heatmap as
a second monitor view, not the main one.

## 1. Mission

![Mission monitor approval](review/overnight-2026-11-25/docs/images/ui/v2/mission-monitor-approval.png)
![Mission mini idle](review/overnight-2026-11-25/docs/images/ui/v2/mission-mini-idle.png)

Mission control. Dark slate #0d1117, agent colors only. Big state
banner across the top with the state word, the sentence, the
proposal, the 87s countdown, and the green and red buttons in one
place. Below: agent roster cards, SVG handoff graph, round counter
2 of 3, latency and token bars, risk gauge, 6-row task queue,
event tape, voice panel, top-4 sectors, P and L strip.

Strengths: the clearest to a stranger. The approval banner answers
what is happening, what it costs, and what to press without
scrolling or hunting. The frozen banner is the best kill story:
"KILL SWITCH ENGAGED, ALL AGENTS FROZEN" plus "Claims cancelled.
Working tasks blocked with KILL_SWITCH." and the resume rule. The
mini is the cleanest of the five: 64px state word, roster cards,
one-line P and L. Contrast is the strongest measured: body 15.95
to 1, muted 7.43 to 1, red 6.18 to 1, all on #0d1117.

Weaknesses: the least distinctive visually. It could be any good
dashboard, which is fine for a booth but weak for a portfolio
screenshot. The voice panel is flat bars in every state except
listening, which reads as an empty panel on the monitor. In
listening it now shows one try-saying line ("What is happening?"
/ "What is my portfolio value?"), grounded in the voice intent
vocabulary. The sectors panel shows only the top 4, not all 11.
The mini thinking hero has about 100px of blank space under its
one note line. The mini approval risk row sits tight against the
roster strip top edge.

## 2. Orderbook

![Orderbook monitor approval](review/overnight-2026-11-25/docs/images/ui/v2/orderbook-monitor-approval.png)
![Orderbook mini idle](review/overnight-2026-11-25/docs/images/ui/v2/orderbook-mini-idle.png)

The task queue is the hero, shown as an order book: FILLS
(done and working, green depth bars by amount) over BIDS (queued),
with a sector book of all 11 ETFs below it. Right column: the
state hero with a semicircle risk gauge (23 LOW, needle), the 87s
countdown, green and red buttons, the 5-agent roster, the handoff
chain, the event tape, and the P and L strip.

Strengths: the most honest to the system. The queue IS the product,
and showing it as an order book makes the agent work legible to
anyone who has seen a trading screen. The risk gauge with a needle
is the best gauge of the five. The approved and rejected states
change the book itself ("FILLED 11:42:21", "REJECTED HUMAN_REJECT")
and the header counts, which no other direction did first. The
frozen hero says the full rule: claims cancelled, working tasks
blocked, old blocked tasks stay blocked, nothing auto-resumes.

Weaknesses: the densest direction. At a loud booth a stranger has
to read a table to understand it, while Mission hands them the
answer in a banner. The mini book shows only the 3 FILLS rows;
the 3 queued BIDS are monitor-only. The monitor heroes in
listening, approved, error, and frozen carry 90 to 150px of
breathing room under the content. The approval buttons were
hardcoded English and did not switch to Chinese; fixed in pass
4 (绿色 — 批准 / 红色 — 拒绝).

## 3. Terminal

![Terminal monitor approval](review/overnight-2026-11-25/docs/images/ui/v2/terminal-monitor-approval.png)
![Terminal mini idle](review/overnight-2026-11-25/docs/images/ui/v2/terminal-mini-idle.png)

Bloomberg-style dense terminal. Amber #ffb000 and green #33ff66
mono on near-black #0a0c0a. Ticker tape across the top, task queue
left, approval hero center, agents and risk and meters right,
sectors and P and L along the bottom. The only direction with a
hardware legend: green button approve and 2020, red button reject
and 2022, kill latching freeze all, push to talk hold to speak,
EN/中文 toggle.

Strengths: the most authentic trading desk feel, and the hardware
legend is the one panel that explains the physical console to a
stranger. The mini approval is the strongest mini of the five:
76px state word, proposal, 87s, big buttons, roster line, top
sectors, P and L strip, no overflow. Contrast is the highest
measured: amber 10.71 to 1, green 14.62 to 1 on #0a0c0a. The hero
gap was fixed in pass 4: the proposal now starts directly under
the sentence; the slack moved to the bottom of the hero panel.

Weaknesses: the risk panel shows the pending proposal in every
state, even idle, where no proposal exists yet. The ticker tape
is cut off at the right edge on both screens. The round pips sit
under the cost bar and read as part of the cost meter.

## 4. HUD

![HUD monitor approval](review/overnight-2026-11-25/docs/images/ui/v2/hud-monitor-approval.png)
![HUD mini idle](review/overnight-2026-11-25/docs/images/ui/v2/hud-mini-idle.png)

Holographic HUD. Cyan #59d8ff thin line work on deep navy-black
#05080f. A center radial ring holds the state word, with a
scanning arc, 60 tick marks, and a 26-bar voice waveform ring.
The ring changes per state: faint arc idle, bright waveform
listening, spinning arc thinking, solid countdown arc approval,
amber dashed ring frozen, short amber arc error. Roster, handoff,
task queue, LED panel, meters, risk gauge, sectors, and voice
fill the rails.

Strengths: the most beautiful and the most memorable. The ring is
the one visual a stranger will photograph. The approval countdown
as a ring arc is the clearest countdown of the five. The frozen
ring in amber with a dashed overlay is instantly different from
the error ring, which matters when the kill switch is the story.

Weaknesses: the least dense. The monitor has large black fields
around the ring, and the mini ring is small relative to the
screen with empty space above and below it. The handoff graph is
just dots on a line, the weakest of the five. The voice waveform
is now flat in non-listening states (fixed in pass 4), but the
ring's radial bars keep their dim inactive styling outside
listening. The state word overlaps the ring's top arc on the
mini approval shot. Contrast passes (body 15.69 to 1,
label 9.00 to 1) but was checked by inspection, not by meter,
before this run computed it.

## 5. Heatmap

![Heatmap monitor approval](review/overnight-2026-11-25/docs/images/ui/v2/heatmap-monitor-approval.png)
![Heatmap mini idle](review/overnight-2026-11-25/docs/images/ui/v2/heatmap-mini-idle.png)

The sector heatmap is the hero. 11 sector tiles colored by change,
XLE biggest and greenest with a PROPOSAL tag. Right column: voice
ring, latency and token meters, portfolio and cost strip, risk
gauge, 6-row task queue. Bottom: agent handoff chain, event tape,
P and L strip. Approval is a centered takeover card with the
proposal, risk bar, 87s countdown, and big green and red buttons.

Strengths: the most eye-catching at a glance. The idle screen is
a poster: the whole market in one view, XLE leading. The approval
takeover card is the most forceful of the five, with the largest
buttons. The mini heatmap is the best mini idle: the sectors tell
the story without a single sentence.

Weaknesses: the approval overlay hides the heatmap, so the most
exciting state hides the most exciting visual. The state tile has
dead space above and below its centered content. The approved
state repeated the fill fact in two lines (fixed this run to show
cash after fill). The IDLE state word is grey, the least punchy
of the five. The XLE tag is now state-aware (PROPOSAL in approval,
FILLED in approved, no tag elsewhere), fixed in pass 5.

## Cross-cutting findings (all 5 directions)

- Fixed in pass 3: in frozen, the task queue showed ord-0142 as
  WORKING. The bridge blocks every working task with KILL_SWITCH
  on kill, so the queue now shows BLOCKED with the note "blocked
  KILL_SWITCH" in all five. Shared helper
  V2.tasksForState(state) in shared/v2-data.js. Terminal and
  Orderbook had their own overrides and got the same frozen rule.
- Fixed in pass 3: the mission mini state word was 58px, under the
  64px spec. Now 64px.
- Fixed in pass 3 and 4: roster tier duplicated the role for COORD
  ("coordinator / coordinator"). Fixed in terminal, mission, and
  orderbook; the tier now hides when it equals the role. HUD and
  heatmap never showed the tier.
- Fixed in pass 4: the event tape was one static list that showed
  approval events during idle. The tape is now state-aware via
  V2.tapeForState(state): idle shows only 2 boot events, thinking
  shows the run up to the risk check, approval shows the full
  run, approved and rejected and frozen append their own closing
  event, error shows the timeout. One defect caught during the
  fix: mission's tape panel fits 8 rows, so it shows the last 8
  (slice(-8)) and the closing event is always the last row.
- Fixed in pass 4: panel labels are now fully Chinese in zh mode
  in all 5 directions, via V2.label(key, lang) in
  shared/v2-data.js (17 keys). Data labels stay English: meter
  rows, column headers, risk facts, P&L strip items. There are
  no label keys for them, and they are abbreviations, proper
  nouns, or numbers.
- Fixed in pass 4: the approval buttons in orderbook and mission
  were hardcoded English and did not switch to Chinese. They now
  read 绿色 — 批准 / 红色 — 拒绝 in zh. Terminal, HUD, and
  heatmap buttons already switched.
- Fixed in pass 5: cash lied after the fill. The approved banner
  said cash after fill is $10,650.00, but every cash strip still
  showed $23,150.00. Cash is now state-aware via
  V2.cashForState(state): $10,650.00 in approved, $23,150.00
  everywhere else. Portfolio total stays $98,412.55 (cash plus
  positions). Orderbook's hero was already fully consistent
  ("CASH $10,650.00 + POSITIONS $87,762.55 = $98,412.55"). The
  heatmap XLE tag is now state-aware too: PROPOSAL only in
  approval, FILLED in approved, no tag in other states.
- Not fixed, by design of static mockups: the task queue still
  shows sig-0142 and risk-0142 DONE and ord-0142 WORKING during
  idle, while the tape now shows only boot events. The queue is
  a snapshot of the vault mid-run (week 2022-06-13); the real
  dashboard must drive the queue from bridge state, not from a
  fixture. The risk panel still shows the pending proposal in
  every state in terminal.
- Contrast: 21 text and background pairs computed with the WCAG
  luminance formula. All pass AA at 4.5 to 1 or better. Lowest
  is mission red #ff5a5a on #0d1117 at 6.18 to 1. Heatmap tile
  text is white on dark tile backgrounds (#14181d), with color
  carried by a 5px top bar and the colored change value, not by
  a full-bleed tile. Every gauge and heatmap has a numeric label,
  not just color.
- Chinese: approval in zh renders and fits on both screens in
  all five directions. The zh sentences are long, so they get a
  full-width line at 17 to 18px or bigger. Letter-spacing is 0
  on Chinese labels and CJK line-height is 1.6 or more, per the
  research in review/overnight-2026-11-25/docs/UI_RESEARCH_V2.md.
