# SI Console submission checklist

Written 2026-11-25 during the overnight UI v2 run. Method: file inventory
from the repo tree (640 files, listed 2026-11-25 01:02 MST), the 36 text
files that could be downloaded, the fetched README.md, AGENTS.md,
INDEX.json, CHANGELOG.md, and code/si_console/tools.py. The GitHub read
path rate limited (HTTP 429) after the first 36 files, so 604 files were
NOT content-checked. Lines marked UNVERIFIED need a re-check once the
rate limit clears. Nothing here rewrites history. Nothing here submits.

## README

- PASS: what it is. "SI Console stands for Super Intelligence Console.
  It is a physical console that allows agentic orchestration."
- PASS: how to use it. Push to talk, LEDs, 5 inch screen, green approve,
  red reject, kill switch, EN/中文 toggle.
- PASS: why. Software approve buttons can be pressed by the software
  that runs away. Approval is on a real button on its own wire.
- PASS: full 3D assembly screenshot. docs/images/render_hero_R5.png
  and docs/images/render_exploded_R5.png both exist in the tree.
- PASS: PCB screenshot. docs/images/pcb_3d.png exists. pcb_front.png
  and pcb_back.png also exist.
- PASS: schematic or wiring diagram. docs/images/schematic.png and
  blueprints/R5/wiring_diagram_R5.png both exist.
- PASS: every image and link in the README resolves in the tree:
  render_hero_R5.png, render_exploded_R5.png, wiring_diagram_R5.png,
  pcb_3d.png, schematic.png, docs/GPIO_PIN_MAP.md, pcb/,
  blueprints/R5/si_console_assembly_R5.step, blueprints/R5/step/,
  cad/si_console_R5.f3d, code/, bom/BOM.csv.
  Note: the images are Git LFS files. Existence was checked in the
  tree listing, not by downloading the image bytes.

## Files

- PASS: STEP file for each part. 100 files in blueprints/R5/step/
  plus blueprints/R5/si_console_assembly_R5.step.
- PASS: Fusion source. cad/si_console_R5.f3d exists.
- PASS: PCB source files. pcb/si_console_hat.kicad_pro,
  .kicad_sch, .kicad_pcb, .kicad_prl all exist.
- PASS: gerbers.zip. pcb/gerbers.zip exists. pcb/jlcpcb_bom.csv and
  pcb/jlcpcb_cpl.csv also exist.
- PASS: firmware and agent code. code/ exists with si_console/,
  tests/, dashboard/, systemd/ (bridge.service, coordinator.service).
- UNVERIFIED: BOM.csv has a link on every line, including owned
  items. bom/BOM.csv was not downloaded (HTTP 429). The fundable
  total is 885.81 CAD before tax per AGENTS.md and the brief, and the
  README now says 885.81 after this run fixed it from 851. The
  per-line links still need a human to open the file and click them.
- PASS: perfboard backup exists as a part. blueprints/R5/step/
  perfboard_R5.step and perf_standoffs_R5.step exist, matching the
  README claim of perfboard as a backup.

## No leftover draft text

- FAIL: AGENTS.md line 3 says "Status: DRAFT."
- FAIL: INDEX.json has 45 entries with "status": "DRAFT". These are
  the repo's own status labels, not accidental text, but a judge
  reading the repo sees 45 DRAFT entries. The team must decide
  whether the status system stays visible in the submission.
- FAIL: the new v2 UI docs are marked DRAFT by this run:
  review/overnight-2026-11-25/docs/UI_RESEARCH_V2.md and review/overnight-2026-11-25/docs/UI_V2_COMPARISON.md. They are new
  work from tonight and have not been reviewed by the team yet.
- PASS: CHANGELOG.md has no "not for submission" text. Its one
  DRAFT mention is a historical entry about a DRAFT implementation
  gap table in ARCHITECTURE.md.
- PASS: README.md has no draft or not-for-submission text.

## No secrets or personal data

- PASS on the 36 fetched text files: no API keys, tokens, or
  passwords found by pattern search. No .env file in the repo.
  Only code/.env.example exists, which per AGENTS.md holds names
  only. The commit author is Jayden Dai, Daijayden5@gmail.com,
  which the brief orders for commits.
- UNVERIFIED: the other 604 files were not content-checked (HTTP
  429). A full grep for secrets needs the rate limit to clear.

## AI co-author trailers in history

- PARTIAL: 8 of 30 commits on main were seen. All 8 are authored by
  Jayden Dai. None of the 8 subjects carries an AI co-author
  trailer. The full 30-commit scan needs the connector (HTTP 429).
  Do not rewrite history. Decide with Christopher.
- Seen, no trailers in the subject:
  bb8e5e26 Add SI Console HAT PCB, gerbers, images and BOM lines
  19aecf1a UI design for SI Console: research, spec, screen mockups
  and screenshots
  da1a68c5 Prepare repo for Fallen submission
  edfefd56 README: describe the kill switch accurately
  431f4806 Rewrite README
  fc600b54 Add Fusion archive of the R5 assembly
  14d6c32e BOM: restore USB soundbar and spare microSD, add DeepSeek
  and Bocha API credits, update to...
  a5dab109 Reconcile LED resistors, pin names and grounds across
  code, docs and the R5 wiring diagram

## README claims vs the repo

- PASS: BOM total now matches. README says about CAD 885.81 before
  tax. AGENTS.md says BOM.csv is Rev R5, 885.81 CAD fundable.
  Fixed this run from the stale 851.
- PASS: pin map link resolves. docs/GPIO_PIN_MAP.md exists.
- PASS: "Open frame on clear laser-cut acrylic, 2 sheets." The R5
  laser DXFs exist (5 files in blueprints/R5/dxf/).
- PASS: "custom PCB, with perfboard as a backup." PCB sources exist
  and perfboard_R5.step exists.
- NOTE, not a mismatch: "I want to wire it [the kill switch] in
  series with the green button" and "I plan to add approve on the
  touchscreen" are stated as plans, not as done work. Keep them as
  plans or the judge will look for the wiring.
- NOTE, not verifiable from the repo: "Christopher and I are each
  logging 5 to 6 hours a day while balancing IB." A team claim,
  not a repo claim.

## Checks that could not run this run

- Repo tests (AGENTS.md expects 163 passed in code/tests/): not run.
  code/tests/ and most of code/si_console/ were not downloaded
  (HTTP 429). The older Nov 23 scratch tests pass: 79 passed in a
  fresh venv, 0.36s. That is the Nov 23 code, not the repo code.
- cad/build.py CAD checks: not run. cad/build.py was not downloaded.
- PCB checks (ERC, DRC, pcb/check_nets.py): not run. The PCB files
  were not downloaded, and kicad-cli is not installed here.
- UI_SPEC.md and UI_RESEARCH.md could not be re-read, so the v2
  research went into review/overnight-2026-11-25/docs/UI_RESEARCH_V2.md instead of appending
  to docs/UI_RESEARCH.md. Merge them before submission.

## Jayden must do by hand

- Make the repo public.
- Decide on the trailer commits with Christopher. Do not rewrite
  history without agreeing it together.
- Submit on fallen.hackclub.com.
- Post in #fallen-help.
- Decide what happens to the DRAFT labels: AGENTS.md, the 45 DRAFT
  entries in INDEX.json, and the two new v2 docs.
- Open bom/BOM.csv and click every link, including owned items.
- Re-run the repo tests, cad/build.py checks, and PCB checks once
  the files are available, and re-run the full 30-commit trailer
  scan.
- Review the 5 new UI v2 directions in review/overnight-2026-11-25/docs/UI_V2_COMPARISON.md
  and pick one before the build.
