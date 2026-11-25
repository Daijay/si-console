# UI Research, v2 addendum

Status: DRAFT. Written 2026-11-25 during the overnight UI v2 run.
This file is an addendum. It belongs in docs/UI_RESEARCH.md, but that file
could not be read this run (GitHub read path rate limited, HTTP 429), so
the new sources and takeaways live here until the team merges them in.
Nothing here overwrites the v1 research. The v1 flight deck direction
is untouched. No skill was installed during this run. The candidate
skills below are candidates only.

## Rules from the 7 installed skills

Read in full this run from .claude/skills/: animation-performance,
baseline-ui, fixing-accessibility, fixing-motion-performance,
frontend-design, review-animations, web-design-guidelines.

Motion:
- Animate transform and opacity only. Never transition all, never
  animate width, height, top, left, margin, padding.
- UI motion under 300 ms. Button feedback 100 to 160 ms. Entrance
  ease-out, strong curve cubic-bezier(0.23, 1, 0.32, 1). Never ease-in.
- Never scale(0). Start from scale(0.9 to 0.97) plus opacity.
- No requestAnimationFrame loops without a stop condition. Pause
  looping motion off screen. Honor prefers-reduced-motion.
- Animated blur under 8 px, one shot only, never on large surfaces.
- Motion must be justified: state indication, feedback, or preventing
  a jarring change. High frequency actions get no animation.

Baseline UI:
- Never use gradients. Never use glow as a primary affordance. Glow is
  accent only. One accent color per view. This matches the brief: the
  brief asks for a touch of soft glow, so glow stays an accent, never
  the thing that carries meaning.
- tabular-nums for all data. truncate and line-clamp for dense UI.
- aria-label on icon-only buttons.

Accessibility:
- WCAG AA: 4.5 to 1 normal text, 3 to 1 large text and UI components.
- Never rely on color alone. Pair red and green with plus and minus
  signs or arrows. About 1 in 12 men has color vision deficiency.
- Native button for actions, visible focus-visible rings, status
  changes need aria-live polite.
- color-scheme dark on html, meta theme-color matching the background,
  touch-action manipulation. Never disable zoom.
- Numbers via Intl.NumberFormat, never hardcoded formats.

Design:
- Distinctive, not templated. Near-black plus one acid green accent
  is a flagged AI default. The brief mandates a dark trading desk, so
  each direction makes its accent a deliberate subject choice: amber
  terminal, cyan HUD, and so on, not the default.
- One memorable element per screen, rest quiet. No tracked-out
  ALL-CAPS eyebrow on everything. Sentence case copy, active voice,
  specific labels. No lorem ipsum, every number plausible.

CJK type:
- No letter-spacing on Chinese labels. Han characters sit on a fixed
  em grid. Tracking breaks the grid and wraps labels.
- CJK leading 1.5 to 1.8. CJK base size about 1.125 times Latin.
- A monospace face has no Han glyphs, so Chinese in a mono column
  falls back to a system font and column alignment dies anyway. Keep
  Chinese in the sans face.

## References

1. Bloomberg terminal design spec (third-party extraction). Amber text
   on black, mono for numbers and tickers, right-aligned numbers with
   fixed decimals, tabular figures, 4-panel tiled grid, persistent top
   command bar. Takeaway: density is a feature. Hierarchy comes from
   color, not size.
   https://github.com/chrisleekr/binance-trading-bot/blob/HEAD/docs/design/bloomberg-terminal-design-spec.md
2. Bloomberg Terminal Dense Data skill tokens. Pure #000000 panels,
   amber #ffa028 labels, blue #3b82f6 up, red #ff433d down, zero
   radius, shadow, or whitespace. Contrast: amber on black about 11
   to 1, blue about 5.7 to 1, red about 6.1 to 1. Takeaway: use the
   token set verbatim for a terminal direction. Pair blue and red
   with plus and minus for color-blind users.
   https://claude-design-skills.convoke.software/styles/bloomberg-terminal
3. Sci-fi interface skill (Vibehackers). Wireframe and outlines, not
   filled boxes. Concentric circles, radar sweeps, curved progress.
   Monochrome plus red for alerts only. Tiny chroming details like
   target brackets and pixel coordinates. Takeaway: HUD is thin
   strokes plus rings plus one hue.
   https://vibehackers.io/claude-code/skills/sci-fi-interface-sickn33
4. FUI Sci-Fi HUD (designbycurio). Void black, cyan wireframes, ring
   gauges, scan grids, micro-numerals. Takeaway: every screen needs
   one big read graspable in 2 seconds. Pack the edges, keep the
   center clear.
   https://designbycurio.com/learn/fui-sci-fi-hud
5. HUD and FUI design system (designmd). Transparency and layering,
   depth through opacity not shadows, animated idle states, one or
   two hues max, text uppercase mono and terse. Takeaway: a dormant
   HUD still breathes. Depth comes from opacity steps.
   https://designmd.app/library/hud-sci-fi-fui
6. FUI style guide (Stylogeny). Instruments built from hairlines
   (rings, arcs, tick scales, brackets, radar), one luminous hue on
   black, red for alarms only. Takeaway: size micro-text to WCAG,
   not to a cinema screen. Keep flashing scans under 3 flashes
   per second.
   https://stylogeny.com/styles/fantasy-ui/
7. NASA Apollo Big Boards. 10 by 20 ft boards split into functional
   sections, each with one job (velocity, vitals, timeline),
   glanceable big picture. Takeaway: segment the monitor by job,
   not by widget count.
   https://apollo11space.com/how-mission-controls-big-displays-worked-a-look-at-nasas-big-boards/
8. Dark-mode dashboard contrast (Alexander Cillan). Build a surface
   scale (bg, card, raised) with depth from lightness, not shadows.
   Desaturate colors. Reserve green and red for up and down only.
   Check colored text contrast, not just white. Takeaway: surface
   steps like #0b0b0e, #121216, #1a1a20, not pure black vs pure white.
   https://www.alexandercillan.com/blog/dark-mode-ui-for-data-heavy-products
9. Data-viz accessibility reference (vikast908). Never let color be
   the only encoding. If a chart works in grayscale it passes.
   Okabe-Ito palette. Label data directly instead of legends.
   Publish the data table next to the chart. Takeaway: every gauge
   and heatmap needs a numeric label, not just color.
   https://github.com/vikast908/data-visualization-skill/blob/HEAD/skill/references/accessibility.md
10. Dashboard design principles brief (28 sources). Operational
    dashboards are for real-time monitoring and immediate action.
    Top-down hierarchy with the most important numbers top-left.
    8pt spacing grid. Curate, do not dump. Progressive disclosure
    for rare features. Takeaway: the monitor is operational, the
    mini screen is the glanceable subset.
    https://github.com/jacey1225/fellowscript/blob/HEAD/.claude/research/20260816-dashboard-design-principles/brief.md
11. Kiosk attract mode (Workinman). Idle screens on dim screensavers
    waste the booth. Attract mode should autoplay a slideshow or
    pose a question, one tap to engage. Takeaway: idle state is a
    poster with one question and one action, not a dimmed dashboard.
    https://workinman.com/trade-show-museum-kiosk-design-development/
12. CJK typography (Will Chan). Tracking breaks Chinese text. Han is
    already monospaced by design. Line-height 1.4 to 1.5 tuned for
    Latin leaves Chinese cramped. Takeaway: letter-spacing 0 and
    line-height 1.6 or more on every lang(zh) node. Test Chinese
    strings in the same boxes as English.
    https://www.willchan.me/blog/typography-for-cjk-and-latin

## Candidate skills, NOT installed

Only install from these after reading each SKILL.md fully first.
Never run an install script without reading it.

1. dashboard-design (abdiraimov-otabek). 1,182 stars, 246 installs,
   MIT. Distilled from 127 shipped dashboards. KPI tiles, charts,
   ranked lists, states, 8 layouts, 10 playbooks, screenshot QA pass.
   Best fit for the v2 build. Recommendation: install this one first
   if one more skill is installed.
   https://github.com/abdiraimov-otabek/dashboard-design-skill
2. kpi-dashboard-design (wshobson/agents). Repo about 43k stars,
   18.1k installs, Alyn score 86 of 99, MIT. Decides which metrics
   matter and their hierarchy before building. Limits a dashboard
   to 5 to 7 KPIs.
   https://github.com/wshobson/agents
3. data-visualization (vikast908). Bertin encoding grammar plus
   Tufte integrity (Lie Factor 0.95 to 1.05, data-ink ratio,
   chartjunk removal), with accessibility and storytelling.
   Star count not verified.
   https://github.com/vikast908/data-visualization-skill
4. sci-fi-interface (Vibehackers). HUD and FUI implementation
   guide, SVG dials, corner brackets, mono plus alert red.
   Star count not verified.
   https://vibehackers.io/claude-code/skills/sci-fi-interface-sickn33
5. bloomberg-terminal (claude-design-skills.convoke.software).
   Token set plus skill for the amber-on-black terminal aesthetic.
   https://claude-design-skills.convoke.software/styles/bloomberg-terminal
6. typography-system (Awesome Skills). Bilingual EN and Chinese type
   ramp. Hard rules: max 5 sizes, 3 weights, 2 families per screen.
   CJK leading at least Latin. Every typographic value a token.
   https://www.awesomeskills.dev/en/skill/typography-skill-typography-system
7. creating-dashboards and visualizing-data
   (ancoleman/ai-design-components). Repo 533 stars, MIT.
   creating-dashboards 393 installs, visualizing-data 110 installs.
   Note: ships an install.sh. Read it fully before any install is run.
   https://github.com/ancoleman/ai-design-components
