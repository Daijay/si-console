SI Console is a physical control console for a team of AI agents. The software is the product; the case exists to make the agents visible and keep a human hand on the brake. Tagline: "Talk to dispatch, press to approve."

## Content fundamentals

- Write short, literal labels in English and Chinese together. Hardware labels stack English above Chinese: APPROVE / 批准, REJECT / 拒绝, KILL / 冻结, TALK / 说话, toggle EN / 中文.
- Every screen string exists in both languages. Never mix languages inside one sentence on screen; the language toggle switches the whole UI.
- Say what the agent will do, not what it feels: "Run shell command", "python build_slides.py". Show the exact command on the approval card.
- Name agents in capitals in English: COORD, AGENT 1, AGENT 2, GUARD. In Chinese: 协调员, 智能体 1, 智能体 2, 守卫.
- Status words are fixed: queued, working, blocked, done, frozen (排队中, 工作中, 已阻塞, 完成, 已冻结). Never invent a sixth.
- No emoji, no exclamation marks, no marketing words on the product.

## Visual foundations

- Honest materials. Show the Raspberry Pi 5, fan, perfboard, wiring, screws and finger-joint edges. The look is industrial maker, never sleek consumer gadget. No brand logos or real company names on the hardware.
- Case: clear 3 mm acrylic (`acrylic` edges at 10 to 35 percent fill) with an optional warm 3 mm plywood front panel (`plywood`, labels in `ply-ink`).
- Screens are dark: `ground` for the page, `surface` for panels, `surface-raised` for cards. Text is `ink`, secondary text `ink-muted`. Accent is `ember`, working is `amber`.
- Color has jobs. `approve` is only safe, done and APPROVE. `reject` is only REJECT. `kill` is only the kill switch and the KILL ACTIVE banner. Never use red or green as decoration.
- Meaning never rests on color alone: every status carries a word, and the done chip carries a check mark.
- Borders that carry meaning use `line-strong`; dividers use `line`. Cards use `radius-md`, panels `radius-lg`, chips `radius-pill`.
- Mono type (`dash-mono`) for ids, commands and tool calls. Sans for sentences. Chinese uses the sans stack (Noto Sans SC first) and is never letter-spaced.
- Motion exists only on hardware states: pulse (APPROVE), blink (GUARD), slow blink (queued agent). Respect reduced motion in previews.

## Light states

| State | Agent LEDs | Buttons | Screens |
| --- | --- | --- | --- |
| Idle | all off | dim | ready |
| Working | active solid, queued slow blink | dim | live chat |
| Approval needed | GUARD blinks | APPROVE pulses | green Needs approval card |
| Kill active | all off | dark, faint green APPROVE only | red KILL ACTIVE / 已冻结 banner on both screens |

## Screens

- Main monitor (15.6 in): top bar (mode HOME/BOOTH, language, agent count, kill status), status strip, task queue left, live chat center, Needs approval card plus task graph right, Ctrl+K command bar bottom. Build it from the `Dashboard` preview.
- Mini screen (5 in, 800x480): no interaction, one row per agent, `mini-name` and `mini-detail`, nothing smaller than 28px. Build it from the `MiniScreen` preview.
- The approval card is the only green card. It shows the exact action and the hint "Press APPROVE on the console".

## Previews in this system

Hero (whole setup), ConsoleViews (front, top, rear, dimensions), Exploded (see-through parts), Dashboard, MiniScreen, LightStates, BoothScene. Use them as the reference when building the case, the screens or the booth.
