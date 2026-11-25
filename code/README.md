# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console scratch code. Reference only. Not for Fallen submission.

## What this folder is
Draft skeletons for SI Console, built from the Autumn audit and the
architecture. The team must review and rewrite every file before it
is used. Nothing here is submission code. Nothing here is tested on
the Pi yet. (CODE_NOTES.md and autumn-clone/ from the original workspace are not in this repo.)

## Layout
- si_console/ : the rewired code. Start with config.py, then coordinator.py.
  - config.py : settings, provider keys, tier chains, arena panes, allow lists. No Gmail.
  - errors.py : shared error shapes, copied from Autumn.
  - deepseek_client.py : DeepSeek API layer, rewired from groq_client.py.
  - models.py : tier router for the accepted roster: T0-T3 chains, fallback, pane pins.
  - chat_client.py : one OpenAI-compatible client for DeepSeek, Hunyuan, GLM, Bailian/Qwen, MiMo.
  - router.py : rules-only routing (skill, keywords, length), Jev tie-break, dispatch.
  - judge.py : Jev 1.14 judge through the OpenRouter Decisions API.
  - telemetry.py : SQLite telemetry for routes and model calls.
  - vault.py : task notes, frontmatter, atomic writes. New code.
  - search.py : vault search, repointed from Autumn search.py.
  - context.py : prompt compression, repointed from Autumn context.py.
  - guard.py : GUARD checks. New code. No Autumn equivalent.
  - tools.py : tool registry, tags, schemas, role lists. New code.
  - coordinator.py : agent loop, fixed menu, 3 round limit. New code.
  - rules_engine.py : price only sector ranking. New code.
  - make_slides.py : slides with python-pptx. New code.
  - bocha.py : Bocha web search. New code.
  - voice_intents.py : voice intent matcher, from the handoff.js idea.
  - scheduler.py : replay clock and daily summary, from Autumn server.py.
  - state_store.py : state.json and claims, from Autumn chats.py.
  - bridge.py : vault watcher, buttons, LEDs, external agent API. New code.
  - gpio_test.py : GPIO test script for the Pi. Run on breadboard first.
- tests/ : tests that run without a Pi and without API keys.
- systemd/ : bridge and coordinator units. Pi uses systemd, not autostart.
- dashboard/ : strings.json (prewritten EN and ZH sentences) and theme.css
  (Autumn ember theme tokens). The full React dashboard is not copied.
  Reuse the layout and the palette from Autumn, rewrite the panels.
- requirements.txt : pinned versions. config.yaml.example and .env.example
  show the names only. No secrets in this folder.

## How to run the tests
From this folder (code/):
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   (gpiozero and python-pptx are only needed on the Pi / for slides)
.venv/bin/python3 -m pytest tests/ -v
Last run 2026-11-23 on Windows: 79 passed.

## What is NOT here
No API keys. No Gmail. No OAuth. No Windows autostart. No local LLM.
No DeepSeek model name hard coded. The model is pinned in .env at
build time. No voice models installed. STT and TTS are picked after
the bench test.
