# PROMPTS.md
SI Console research. Step 0. Date: 2026-11-20. Lead: Pingu, for Jayden, asleep.

## Step 0 summary: what I learned about multi-agent research

1. Split work by object, not by opinion. One agent owns one part. Parallel agents must not edit the same file.
2. Give each sub-agent a self-contained prompt. It has no other context. Put the goal, the files, the constraints, and the definition of done in the prompt.
3. The return is data, not chat. Ask for a fixed shape. Dense list, table, verdict plus evidence. The lead relays what matters.
4. Separate builder and verifier. A fresh agent reviews work it did not write. A model reviewing its own work is biased.
5. Give reviewers different jobs. One checks prices and links. One checks specs and compatibility. One tries to break the plan. Different roles find more mistakes.
6. Allow the agent to say I do not know. Add an explicit UNVERIFIED label. An honest gap beats a guessed number.
7. Ask for a source for every claim. A link that is not opened is not a source. Open the page. Check the price, the spec, and the date on the page.
8. Do not let the model grade its own homework. Verify prices and links against raw page text, not against a summary. If a page is blocked, mark it unreadable.
9. Use a parallel barrier, then a pipeline. Spawn all workers at once. Wait for all. Then run reviewers. Then run compatibility and skeptic checks. Then assemble.
10. Record disagreements. When two agents disagree, keep both views, keep the evidence, then decide. Log what changed and why.

Sources for Step 0:
- https://github.com/dirtybits/agent-skills/blob/HEAD/skills/subagent-orchestration/SKILL.md
- https://medium.com/google-cloud/5-agent-orchestration-patterns-backed-by-research-54be9f79171d
- https://www.opencastle.dev/docs/agentic-development/
- https://github.com/alp82/aistack/blob/HEAD/research/ai-coding-quality-systems-2026-03.md
- https://thetweaks.com/reduce-ai-hallucinations/
- https://ki-uebungsplatz.de/guides/research-with-ai-and-check-sources?lang=en
- https://www.murphmaxxing.com/vault/omega-agent-orchestration
- https://cwyz.com/tutorials/agent-team-sop-claude-agent-sdk-en

## Assumptions

- User is Jayden, in New Westminster, BC, Canada. Time zone America/Vancouver.
- Build deadline is Dec 8, 2026. Parts must arrive by about Nov 30, 2026.
- Budget target is parts under about CAD 400, excluding the portable monitor.
- No custom PCB. Perfboard, wires, terminal blocks only.
- The user will design and write his own submission. This job is research, plan, and specify only. Do not write his README, journal entries, CAD files, or firmware for submission.
- Plain text, no em dashes, short sentences.
- Mark every claim VERIFIED, LIKELY, or UNVERIFIED. Never present an UNVERIFIED price or spec as fact. No fabricated links.
- Prices are CAD, as found on Nov 20, 2026, from Canadian retailers. Prices change. Check the date on each page.

## Master prompt

You are the lead research agent for SI Console, a physical console for controlling a team of AI agents, built for Hack Club Fallen.
The console uses a Raspberry Pi 5 8GB as the engine.
It has a main portable monitor, 10 to 14 inch, HDMI or USB-C.
It has a mini screen, 3.5 to 5 inch HDMI, showing a live chain of which agent is doing what.
It has a USB mic with push-to-talk, a small speaker, a big green arcade button for approve, a big red arcade button for reject, and a red kill switch that freezes all agents.
It has one LED per agent. Four agents: signal, risk, execution, coordinator.
Agents hand work to each other through a shared Obsidian vault. Task notes are markdown with a status field: queued, working, blocked, done.
A bridge program watches the vault and updates the screens and LEDs.
Two-key rule: voice or text can only propose. Only the green button executes.
Home mode is live paper trading, price-only sector rotation, paper money only.
Booth mode is offline replay of 2020 or 2022 market history with scripted agent decisions. AI APIs may not work from Maker Faire Shenzhen. That is unverified.
Voice and screens must work in English and Chinese.
The build must finish by Dec 8, 2026. Parts must arrive by about Nov 30, 2026.
Budget target is parts under about CAD 400, excluding the portable monitor.
No custom PCB. No lithium batteries for travel to China.
Deliver BLUEPRINT.md, PARTS.csv, PROMPTS.md, OPEN_QUESTIONS.md, and LOG.md in ~/workspace/si-console/.
Split the work into 9 worker agents, one per workstream. Each worker saves its own report file. Then run reviewers, a compatibility agent, and a skeptic agent. Then assemble the final blueprint. Do not stop early. If a detail is unclear, pick the most reasonable reading, write it under Assumptions, and keep going.

## Shared rules for every worker and reviewer

- Work only from live web sources. Use browser.search and browser.open. Open each product page you cite.
- Use Canadian retailers first: DigiKey.ca, Amazon.ca, Canada Computers, Adafruit via Canadian resellers, Buyapi.ca, PiShop.ca, Creatron, and similar. Note the retailer, the exact model, the price in CAD, stock status, and shipping estimate to BC.
- Mark every claim VERIFIED, LIKELY, or UNVERIFIED. VERIFIED means you opened the page and saw the price or spec on that page. LIKELY means a second source agrees but you did not open the primary page. UNVERIFIED means you could not check it. Never present UNVERIFIED as fact.
- Never invent a link. If you do not have a real URL from a tool result, write no link and mark the claim UNVERIFIED.
- Plain text, no em dashes, short sentences.
- Save your report as a markdown file in ~/workspace/si-console/workstreams/. Return a short summary in your final message: top 3 findings, total cost for your parts, and what is UNVERIFIED.
- Do not write Jayden's README, journal entries, CAD files, or firmware for submission. Research and specify only.

## Worker 1: Compute

Research the Raspberry Pi 5 8GB as the engine for SI Console.
Cover: Pi 5 8GB board, official 27W USB-C power supply, active cooler, case fan, microSD card vs NVMe HAT, storage size and speed, thermal load in a closed case with two displays, and whether 8GB RAM is enough for two displays, a dashboard, Python agents, a vault watcher, and offline speech-to-text and text-to-speech in English and Chinese.
Give exact models, Canadian retailer links, CAD prices, stock, and shipping to BC.
Give a cheaper fallback for each part.
Save to ~/workspace/si-console/workstreams/01-compute.md

## Worker 2: Displays

Research the main portable monitor and the mini screen.
Main monitor: 10 to 14 inch, HDMI or USB-C, portable, buyable in Canada. Compare at least 3 options. Note price, resolution, power draw, cable type, and whether it needs its own power brick.
Mini screen: 3.5 to 5 inch HDMI, for the Pi 5. Compare at least 3 options. Note resolution, touch or no touch, power draw, and driver needs.
Explain how the Pi 5 drives two displays at once. Note the two micro-HDMI ports, resolution limits, and power budget.
Cover cables, adapters, mounting, and total power draw for both screens.
Save to ~/workspace/si-console/workstreams/02-displays.md

## Worker 3: Audio

Research USB mic, speaker, push-to-talk, and offline speech on a Pi 5.
Cover: USB mic options for a loud booth, small speaker options, push-to-talk button wiring to GPIO, echo and noise problems, and how to reduce them without a custom PCB.
Cover offline speech-to-text and text-to-speech in English and Chinese on a Pi 5 8GB. Compare Whisper, Vosk, Piper, and other offline options. Give model sizes, RAM use, latency, and accuracy notes.
Give exact models, Canadian retailer links, CAD prices, stock, and shipping to BC.
Save to ~/workspace/si-console/workstreams/03-audio.md

## Worker 4: Controls

Research arcade buttons, kill switch, LEDs, and GPIO wiring.
Cover: big green arcade button, big red arcade button, red kill switch, 4 LEDs for signal, risk, execution, and coordinator, resistors, perfboard, wires, and terminal blocks.
Give a wiring table in text form. List every GPIO pin, what it connects to, voltage, and resistor value.
Cover debouncing in software, pull-up and pull-down, and why 3.3V logic matters.
Give exact models, Canadian retailer links, CAD prices, stock, and shipping to BC.
Save to ~/workspace/si-console/workstreams/04-controls.md

## Worker 5: Case and mechanical

Research case layout, dimensions, and mounting.
Cover: 3D printed case vs drilled project box, pros and cons, cost, and time.
Give a layout for every part: Pi 5, main monitor, mini screen, mic, speaker, 2 arcade buttons, kill switch, 4 LEDs, power supply, and cables.
Give outside dimensions in mm. Give mounting hole notes.
Cover where to download STEP models for the Pi 5, screens, and buttons. Cover CAD tips for a first-time builder.
Save to ~/workspace/si-console/workstreams/05-case.md

## Worker 6: Power and travel

Research total power budget and travel to China.
Cover: power draw for Pi 5, both screens, mic, speaker, LEDs, and buttons. Give a table in watts and amps.
Cover one power supply vs several. Cover USB-C PD, and what happens if the Pi browns out.
Cover China plug type, voltage, and adapter needed. Cover airline rules for luggage, and why no lithium batteries matters.
Cover what to pack, and what to buy in China as a fallback if a part fails.
Save to ~/workspace/si-console/workstreams/06-power-travel.md

## Worker 7: Software architecture

Research the software plan for SI Console.
Cover: agent roles for signal, risk, execution, and coordinator. Vault note format for task notes, with status queued, working, blocked, done. Bridge program that watches the vault and updates screens and LEDs.
Cover voice proposes and green button approves. Cover kill switch behavior. Cover home mode vs booth mode.
Cover the paper-trading replay game. Compare 2020 vs 2022 market history. Cover scoring vs SPY. Cover data sources for history that work offline. Note what data is free, what needs a download before travel, and file size.
Cover English and Chinese UI and voice. Cover what runs on the Pi and what needs internet.
Save to ~/workspace/si-console/workstreams/07-software.md

## Worker 8: Prior art

Research existing agent approval hardware and Pi voice assistants.
Cover: Claude Desktop Buddy, Iozzia-Lab/agent-remote, XiaoZhi, and at least 3 others. For each, note what it does, what hardware it uses, what is open source, and what is already done.
Cover what makes SI Console different: two-key approval, vault handoff, 4 LEDs, booth offline replay, and English plus Chinese.
Note what Jayden can copy, what he must not copy, and what is a dead end.
Save to ~/workspace/si-console/workstreams/08-prior-art.md

## Worker 9: Sourcing and cost

Research sourcing and cost for every part in workstreams 1 to 6.
For every part, give exact model name, exact retailer product page link, price in CAD, stock status, and shipping estimate to BC.
Give a primary source and a backup source for each part.
Flag any part with long shipping, or with a ship date after Nov 30, 2026.
Give a total for the primary list, and a total for a cheaper fallback list, excluding the portable monitor.
Save to ~/workspace/si-console/workstreams/09-sourcing-cost.md
Also save a draft CSV to ~/workspace/si-console/workstreams/09-parts-draft.csv with columns: part, exact model, qty, unit price CAD, retailer, link, backup link, stock, shipping note, verified status.

## Reviewer prompt

You are a reviewer. You did not write the worker report you are checking.
Read the worker report file in ~/workspace/si-console/workstreams/.
Independently re-verify: every price, every link, every spec, and every compatibility claim.
Open each link with browser.open. If a link does not open, or does not show the price or spec claimed, mark it failed.
Check Pi 5 compatibility: voltage, GPIO 3.3V logic, power, HDMI micro ports, USB bandwidth.
Check that no claim is invented. If a claim has no source, mark it UNVERIFIED.
Save your review to ~/workspace/si-console/reviews/. List each correction, with the old claim, the corrected claim, and the source link.
Return a short summary: how many claims passed, how many failed, and the 3 biggest corrections.

## Compatibility agent prompt

You are the compatibility agent. Read all 9 worker reports in ~/workspace/si-console/workstreams/ and all reviews in ~/workspace/si-console/reviews/.
Check the whole parts list together: total power, ports, USB bandwidth, physical fit in the case, GPIO pin conflicts, cable count, and thermal load.
List every conflict, with the two parts that conflict, and a fix.
Save to ~/workspace/si-console/reviews/compatibility.md

## Skeptic agent prompt

You are the skeptic. Try to break the plan.
Test: noisy booth, no internet, hot closed case, part out of stock, Pi brownout, mic fails, button bounces, LED wiring wrong, China power adapter missing, and data file too large for the Pi.
For each failure, say what happens, how likely it is, and what fallback saves the demo.
Save to ~/workspace/si-console/reviews/skeptic.md
