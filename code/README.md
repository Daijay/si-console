# SI Console code

Python code for the SI Console. It is tested on a laptop with the model
APIs mocked. Nothing here has been run on the Raspberry Pi yet.

## What is built

- Coordinator (`si_console/coordinator.py`): picks up queued task notes, calls
  the model, validates tool calls against a fixed menu, runs GUARD, stops at
  3 rounds and writes an escalation note. It logs tool calls but does not run
  the tool bodies yet, and it does not yet wait for a button approval.
- Guard (`si_console/guard.py`): kill switch, role, approval and risk checks,
  plus the shell command allow list.
- Router (`si_console/router.py`, `models.py`, `chat_client.py`,
  `deepseek_client.py`): rules-only tier routing with a judge tie-break, and
  model tiers with fallback. The coordinator loop does not call the router's
  worker dispatch yet.
- Judge (`si_console/judge.py`): typed choice decisions from Jev, direct from
  TypeSafe (`api.typesafe.ai/v1/systemone`); OpenRouter is the alternate route.
- Smoke check (`si_console/smoke.py`): free key and model-id checks, and opt-in
  one-call-per-model live checks. `deploy/sync_env.py` updates an old `.env`.
- Telemetry (`si_console/telemetry.py`): SQLite log of routes, judge calls and
  model calls.
- Bridge (`si_console/bridge.py`): token-protected HTTP API for external
  agents, plus the logic for green, red, kill switch and approval requests.
  The GPIO buttons and LEDs are not connected to it yet, and its vault watcher
  is not started by the service.
- Voice intent matcher (`si_console/voice_intents.py`): maps text to a fixed
  English and Chinese vocabulary. It takes text as input and does not listen
  to audio.
- Tests (`tests/`): run without a Pi and without API keys.

Supporting files:

- `si_console/`: also has config, errors, task note storage (`vault.py`),
  search, context compression, tool registry, price-only rules engine, slide
  maker, Bocha web search, scheduler, state store, GPIO pin map and a GPIO test
  script for the Pi.
- `systemd/`: bridge and coordinator service units.
- `dashboard/`: `strings.json` (prewritten English and Chinese sentences) and
  `theme.css` (colour tokens). There is no dashboard app yet.
- `requirements.txt`, `config.yaml.example`, `.env.example`: pinned versions
  and setting names. No secrets belong in this folder.

## Planned for the build phase

- Speech-to-text. The model will be picked after a bench test.
- Status screen UI for the 5 inch mini screen.
- Monitor dashboard.

The gaps between the architecture spec and this code are listed under
"Implementation gaps" in `../docs/ARCHITECTURE.md`.

## How to run the tests

From this folder (`code/`):

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python3 -m pytest tests/ -v
```

On Windows use `.venv\Scripts\python`. `gpiozero` is only needed on the Pi and
`python-pptx` only for slides.

Last run 2026-11-25 on Windows: 179 passed.

## Deploy to the Pi
1. On the Pi: `git clone` the repo (then `git lfs pull` if you need the CAD files).
2. Copy your filled `.env` from the laptop (it is not in git):
   `scp code/.env <you>@<pi>:~/si-console/code/.env`
   (an `.env` made from an older template is updated by `deploy/sync_env.py`,
   which the installer runs; your values are kept, the old file is backed up)
3. `bash ~/si-console/code/deploy/install_pi.sh` installs packages and the venv,
   makes the vault folders, locks `.env` (chmod 600, LF endings), checks the
   clock, writes the systemd units for your user and path, then runs the free
   smoke check. It sends no paid API call.
4. `cd ~/si-console/code && .venv/bin/python -m si_console.smoke --live` sends one
   tiny call per model (cost shown first, asks before sending).
5. `bash ~/si-console/code/deploy/install_pi.sh --enable` starts the services
   (refuses if the smoke check fails).
Run the smoke check again in Shenzhen before the booth opens.
