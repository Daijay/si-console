# UI research

Feeds [UI_SPEC.md](UI_SPEC.md).

**How to read the sources.** Web references below were read as search result summaries, not as full text. Treat their findings as unconfirmed and open the link before quoting a number. The guides in section 1 were read in full. Star counts come from the GitHub API on 2026-11-25.

## 1. Guides used

Only Markdown and license files were read. No install script or executable was run, and none of these needs credentials. Copies are not kept in this repo; follow the links.

| Guide | Source (pinned commit) | License | Used for | Where it was overruled |
|---|---|---|---|---|
| frontend-design | [anthropics/skills @ e4bb5d9](https://github.com/anthropics/skills/tree/e4bb5d960d87126ff3b3a8af1a104b7db67560ba/skills/frontend-design) (200k stars) | Apache 2.0 | Direction planning, avoiding template looks, plain screen copy | Capital state words and agent names stay because the brief and the panel labels ask for them |
| web-design-guidelines | [vercel-labs/agent-skills @ 5a37a63](https://github.com/vercel-labs/agent-skills/tree/5a37a6329fbad3666c3207392a6a7c0110e92efb/skills/web-design-guidelines) (35k) | MIT | Review checklist: reduced motion, `color-scheme`, `aria-live`, no `transition: all`, tabular numbers, `Intl` formats | Sentence case instead of Title Case; no pause control on kiosk loops. Rules file matched the SHA-256 stated in the guide |
| baseline-ui | [ibelick/ui-skills @ 7ef0076](https://github.com/ibelick/ui-skills/tree/7ef0076fce1dfa39dd2bc43b7dc13add6eda8a41/skills/baseline-ui) (11k) | MIT | Compositor-only motion, clear empty states, no decorative gradients | Tailwind and React rules ignored (plain CSS stack). The hatched fault band is a hard-edged repeating gradient used as a pattern |
| fixing-accessibility | [same repo](https://github.com/ibelick/ui-skills/tree/7ef0076fce1dfa39dd2bc43b7dc13add6eda8a41/skills/fixing-accessibility) | MIT | Names on icons and meters, native elements, contrast, states not carried by colour alone | None |
| fixing-motion-performance | [same repo](https://github.com/ibelick/ui-skills/tree/7ef0076fce1dfa39dd2bc43b7dc13add6eda8a41/skills/fixing-motion-performance) | MIT | Pi 5 motion budget | None |
| animation-performance | [emilkowalski/skills @ 64eb3de](https://github.com/emilkowalski/skills/tree/64eb3deb9a5fbfa041faf783e0bc3fd635872e9c/skills/animation-performance) (59k) | MIT | Choosing CSS over JavaScript loops, `transform` and `opacity` only | None |
| review-animations | [same repo](https://github.com/emilkowalski/skills/tree/64eb3deb9a5fbfa041faf783e0bc3fd635872e9c/skills/review-animations) | MIT | Review of the motion spec: ease-out entrances, short UI transitions | Its pointer to a `choreograph` guide is unused |

Two further guides were also consulted: an anti-template-design checklist and a data-visualisation guide (used for the cost and judge meters: one hue, direct labels).

## 2. Guides found and not used

| Guide or list | Why not |
|---|---|
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (116k) | Ships scripts and a command line tool that would all need reading first |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (154k) | Python search scripts and a generic style database |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) (121k) | Popularity checked only; not opened |
| [greensock/gsap-skills](https://github.com/greensock/gsap-skills) (19k) | No GSAP in this design |
| anthropics/skills: [theme-factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory), [webapp-testing](https://github.com/anthropics/skills/tree/main/skills/webapp-testing), [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design), [web-artifacts-builder](https://github.com/anthropics/skills/tree/main/skills/web-artifacts-builder), [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) | Slide themes, Python test helpers, static art, a React bundler and a vendor brand. A small Playwright script covered testing |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) React and deploy skills | No React, no deployment |
| [plugin87/ux-ui-agent-skills](https://github.com/plugin87/ux-ui-agent-skills) (3.2k) | Described as a large bundle, more than a two screen kiosk needs; not opened |
| [kylezantos/design-motion-principles](https://github.com/kylezantos/design-motion-principles) (1.6k) | Overlaps the two motion guides used |
| [chrisvoncsefalvay/claude-d3js-skill](https://github.com/chrisvoncsefalvay/claude-d3js-skill) (256) | No license reported, no D3 here |
| [abdiraimov-otabek/dashboard-design-skill](https://github.com/abdiraimov-otabek/dashboard-design-skill) (1.2k), [oil-oil/draw-ui](https://github.com/oil-oil/draw-ui) (572), [joepUI/motion-ref-skill](https://github.com/joepUI/motion-ref-skill) (9) | Less established sources; not opened |
| Indexes: [ComposioHQ](https://github.com/ComposioHQ/awesome-claude-skills), [BehiSecc](https://github.com/BehiSecc/awesome-claude-skills), [travisvn](https://github.com/travisvn/awesome-claude-skills), [VoltAgent](https://github.com/VoltAgent/awesome-agent-skills), [romanticamaj motion list](https://github.com/romanticamaj/awesome-ui-motion-skills), [zhuyansen design list](https://github.com/zhuyansen/awesome-claude-design-skills) | Lists used to find candidates; nothing to install |

## 3. Visual references and takeaways

| Reference | Finding | What we did with it |
|---|---|---|
| Quiet, dark cockpit: [NASA NTRS 19910001626](https://ntrs.nasa.gov/citations/19910001626), [Volpe flight deck human factors](https://www.volpe.dot.gov/sites/volpe.dot.gov/files/docs/Human_Factors_Considerations_in_the_Design_and_Evaluation_of_Flight_Deck_Displays_and_Controls_V2.pdf) | Lights stay off when all is well; only abnormal or action-needed items light up | Idle tiles are dark. A lit tile always means that agent is working. Only approval and kill take the whole screen |
| Alert colour convention: [EASA CS-25](https://www.easa.europa.eu/cs/downloads/1592/en), [NASA TM 20205010986](https://human-factors.arc.nasa.gov/publications/NASA_TM20205010986.pdf) | Red is warning, amber or yellow is caution | Red is kept for reject and kill. Yellow already means GUARD, so system faults use white on a hatched band instead |
| Air traffic control colour: [FAA study](https://rosap.ntl.bts.gov/view/dot/73240/dot_73240_DS1.pdf), [colour vision study](https://www.faa.gov/data_research/research/med_humanfacs/oamtechreports/2000s/2007/200705) | Colour needs a redundant cue, and brightness alone is a weak one | Every state has a word, plus fill, outline, dashed outline or icon |
| Character size: [FHWA](https://www.fhwa.dot.gov/publications/research/safety/98057/ch03.cfm), [NASA TM](https://human-factors.arc.nasa.gov/publications/NASA_TM20205010986.pdf) | About 16 arcminutes minimum, 20 to 22 for assured reading of critical items | Type sizes are computed from screen pitch and distance (section 4) |
| Cockpit type: [B612 repository](https://github.com/greebl3/b612), [ENAC record](https://hal-enac.archives-ouvertes.fr/hal-01022511) | B612 was designed for Airbus cockpit screens, OFL. Independent legibility proof not found | Chosen as the Latin face |
| Car displays: [NHTSA visual-manual guidelines](https://www.nhtsa.gov/document/visual-manual-nhtsa-driver-distraction-guidelines-vehicle-electronic-devices-0) | Short single glances, around 2 seconds | One big word per screen; detail lives on the monitor |
| Teenage Engineering: [OP-1 layout guide](https://teenage.engineering/guides/op-1/original/layout), [review](https://www.soundonsound.com/reviews/teenage-engineering-op1) | Screen colour maps one to one onto physical knobs | Tile colours equal the panel LEDs; on-screen green is left of red, as on the control strip |
| Bloomberg: [customer-centric design](https://www.bloomberg.com/company/stories/bloombergs-customer-centric-design-ethos), [concealing complexity](https://www.bloomberg.com/company/stories/how-bloomberg-terminal-ux-designers-conceal-complexity) | Consistency matters as much as density; the look is recognisable from far away | Fixed monitor columns that never move between states |
| Terminal and cyberdeck UIs: [eDEX-UI review](https://www.linux-magazine.com/index.php/Issues/2019/220/FOSSPicks/(offset)/18), [low contrast complaint](https://robertsspaceindustries.com/spectrum/community/SC/forum/3/thread/ui-readability-a-recurring-pain-point-that-deserve) | Looks good, often reads poorly | Borrowed only the monospace tool call lines |
| Agent observability: [Langfuse agent graphs](https://langfuse.com/docs/observability/features/agent-graphs), [LangSmith tracing](https://docs.langchain.com/langsmith/trace-with-langgraph), [OpenSearch agent graph](https://observability.opensearch.org/docs/ai-observability/agent-tracing/graph/) | Graph, trace and timeline shown together and kept in step | Monitor shows transcript, handoff graph and event log at once. The graph is a fixed pipeline so visitors can learn it |
| Public displays: [LMU display blindness paper](https://www.medien.ifi.lmu.de/pubdb/publications/pub/memarovic2015perdis/memarovic2015perdis.pdf), [Huang et al. 2008](https://almeida.informatik.rwth-aachen.de/publications/huang2008b.pdf) | Passers-by glance for one to two seconds, if at all | Attract screen carries one sentence, one example and four large moving lamps |
| Kiosk attract screens: [Digital Signage Today](https://www.digitalsignagetoday.com/articles/can-attract-screens-lure-in-customers/) | Invite action; do not explain everything. No sound source for a "10 second" figure was found | Attract screen names the one physical action |
| Chinese layout: [W3C clreq resources](https://www.w3.org/International/clreq/resources/) | Reference for line breaking and spacing | `line-break: strict`, no letter spacing, more line height |
| Contrast and flashing: [WCAG 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html) | 4.5:1 text, 3:1 large text; no more than 3 flashes per second | Fastest blink is 2 Hz |

## 4. Principles

1. **One second, two metres.** Screen pitch is about 0.135 mm per pixel on the 5 inch panel (108 mm active width, estimated from the 800x480 module) and 0.18 mm on the monitor. B612 Bold capitals are 0.76 of the font size. A 146 px word is therefore about 15 mm tall, 26 arcminutes at 2 m. A 30 px label is about 3 mm, readable only up close. So only the state word, colour fields and position are designed for 2 m.
2. **Colour is state, and it matches the hardware.** Agent hue = panel LED. Solid = working, slow blink = queued, dashed with fast blink = blocked, dark = idle, grey = frozen. Red = reject or kill. White hatching = something is broken.
3. **Motion means change.** A loop runs only where something is alive or waiting. The kill screen appears instantly and does not move.
4. **Hierarchy.** State word, then the action, then who asked and how risky, then evidence.
5. **Never show stale as live.** If the screen loses the console it says so and drops the live view. A recorded run is labelled on every frame.
6. **Bilingual type.** B612 for Latin and digits; Noto Sans SC for Chinese (OFL, also packaged for Raspberry Pi OS as `fonts-noto-cjk`); IBM Plex Mono for tool calls because B612 Mono parentheses looked like brackets. Fonts are bundled as subsets so the booth needs no network. Chinese words are shorter, so they may be set larger.
7. **Camera.** Dark ground, no thin hairlines carrying meaning, no pure red text on dark, large flat fields for the two buttons.
