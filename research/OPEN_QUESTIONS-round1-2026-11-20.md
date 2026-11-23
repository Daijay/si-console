# SI Console OPEN QUESTIONS
Date: 2026-11-20.
Ordered by importance. Most important first. Each question names who must decide it, what happens if it is not decided, and what the current evidence says.

## 1. Budget: raise it, cut to the core, or delay
Who decides: Jayden.
Why it is first: the full build is CAD 828.22 before tax, CAD 927.61 with 12 percent BC tax, before shipping, before the monitor, before the monitor power supply. The CAD 400 target is not met by any full build. The cheapest honest core is about CAD 570 before tax, about CAD 638 with tax, before shipping and before the monitor. The Pi 5 8GB alone is CAD 249.50, 62 percent of the CAD 400 budget.
If not decided: no order can be placed with confidence, because the Pi is the first order and it is CAD 249.50. Prices may rise again before Dec 8.
Evidence: Worker 9 primary CAD 661.58, fallback CAD 487.39, stripped CAD 393.45, all before tax and shipping. Reconciled total CAD 828.22, because Worker 9 left out the spade kit, the resistor kit, the second micro HDMI cable, the spare microSD, the monitor power supply, and used a cheaper sealed case. See LOG.md for the line by line difference.

## 2. Main monitor size and model
Who decides: Jayden.
Why it matters: the brief says 10 to 14 inch. The case footprint, the desk footprint, the luggage fit, and the power supply all change with size. Do not drill the case until this is decided.
Options: MSI Pro MP165 E6, 15.6 inch, CAD 133.00, DirectDial, VERIFIED, in stock, 1080p, 0.78 kg, needs its own 15W USB-C power supply, over the brief. Canada Computers CAD 89.99 is VERIFIED, sold out online, check BC store pickup first. Or Waveshare 10.1 inch, CAD 160.95, PiShop.ca, VERIFIED, in stock, 1280x800, fits the brief, heavier, more expensive, lower resolution. Or Arzopa A1S 14 inch, US price USD 69.99, LIKELY, CAD price UNVERIFIED, do not order it until a CAD listing is opened.
If not decided: the case layout, the vent plan, and the monitor power supply cannot be finalised.

## 3. STT model: SenseVoice Small or faster-whisper
Who decides: Jayden, after a Pi test.
Why it matters: Worker 3 picks SenseVoice Small, strong in Chinese, Pi 5 latency UNVERIFIED, ARM64 install UNVERIFIED. Worker 7 picks faster-whisper Tiny or Base, multilingual, verified install path, Chinese accuracy LIKELY poor, one benchmark gave Whisper a 15.99 percent character error rate in Chinese. They cannot both be primary.
Test: SenseVoice Small on ARM64 first, in English and Chinese, with a fan on and crowd noise from a phone speaker at 1 metre. If SenseVoice fails to install, fall back to faster-whisper Base multilingual, and use a fixed Chinese command vocabulary, not free speech. Pick the one that works on the Pi, not the one that looks best on paper. Test before Nov 30.

## 4. Local LLM in booth mode, or prewritten narration only
Who decides: Jayden.
Why it matters: Qwen 2.5 3B RAM is 2.35 GB pinned in one test, 5.4 GB in Ollama in another, 3025.9 MB RAM at 5.2 tokens per second in llama.cpp. With the 5.4 GB figure, OS plus Whisper Small plus Piper plus Qwen 3B plus bridge is 8.7 to 9.3 GB, over 8 GB. A 100 token answer at 5 to 10 tokens per second takes 10 to 20 seconds. That is too slow for a booth demo if the visitor waits for narration.
Recommendation in the blueprint: Qwen 2.5 1.5B for short narration only, or no LLM at all and prewritten bilingual sentences. Prewritten is faster, safer, and repeatable. Do not let a local LLM make a trade.

## 5. Button size: 30 mm or 60 mm
Who decides: Jayden.
Why it matters: Worker 4 recommends 60 mm Adafruit buttons, USD 5.95 each, VERIFIED, in stock at Adafruit US. Worker 5 lays out 30 mm buttons. Worker 9 buys 30 mm EG STARTS. The blueprint chooses 30 mm, because they fit the case layout, cost less, and are in Canada. Adafruit 60 mm shipping from the US is 7 to 14 days, LIKELY, plus customs, which risks the Nov 30 arrival date. No PiShop.ca CAD price was found for the exact 60 mm parts.
If 60 mm is chosen: redraw the front panel with at least 90 mm centre to centre spacing, measure the stem hole before drilling, do not drill a 60 mm hole, the face is 60 mm, the stem is smaller, LIKELY 24 mm.

## 6. Kill reset rule
Who decides: Jayden.
Why it matters: Worker 4 says do not auto resume on reset alone, press green to resume. Worker 7 says turn the kill switch off, then press green once, or hold green for 2 seconds. The blueprint chooses turn the kill switch off, then press green once to resume. On resume, coordinator creates a new signal task. It does not resume an old half finished order.
If not decided: the bridge code cannot be written with confidence, and a builder may wire the wrong reset behaviour.

## 7. Mic: FIFINE AM8, lavalier, or cheap fallback
Who decides: Jayden, after a noise test.
Why it matters: FIFINE AM8 is dynamic cardioid, best for a loud booth, CAD 82.99, LIKELY, no CAD link found, stock UNVERIFIED, desktop mic with a stand, not panel mount, needs case space. JOUNIVO JV-601 is gooseneck condenser, CAD 49.79, LIKELY, will pick up booth noise, Worker 9 admits it is a cost pick not a noise proof pick. A USB lavalier clipped near the mouth is the best noise rejection per dollar, but no Canadian price was verified.
Test: record with the chosen mic in a loud room, with a fan on, before travel. If accuracy is below usable, cut voice from the booth demo and run on buttons and text only.

## 8. Speaker: USB only, or 3.5 mm via the mini screen jack
Who decides: Jayden, after a test on real hardware.
Why it matters: PiShop Mini External USB Stereo Speaker is CAD 18.95, LIKELY, USB only, no 3.5 mm needed. Amazon Basics 3.5 mm speaker is CAD 26.99, LIKELY, but the Pi 5 has no 3.5 mm jack, VERIFIED by Reviewer 3. Worker 9 lists the 3.5 mm speaker as primary anyway, with an untested workaround via the mini screen 3.5 mm jack and HDMI audio. That path is not verified for the exact 5 inch screen.
Test: confirm the mini screen HDMI audio jack works with a 3.5 mm speaker before ordering, or buy the USB only speaker.

## 9. Storage: microSD or NVMe for the first build
Who decides: Jayden.
Why it matters: microSD route is CAD 317.73 for compute, recommended on budget. NVMe route is CAD 391.44 for compute alone, and the official 256GB SSD price of CAD 98.75 is UNVERIFIED, conflicts with a 145 USD US report in the same file, Reviewer 1 flagged it. NVMe peak is about 23.9W, about 4.8A at 5V, close to the 5A limit. M.2 HAT+ takes 2230 and 2242 drives only, not 2280.
Recommendation: microSD for the first build, add the M.2 HAT+ and NVMe later after the booth build is working, keep a cloned spare microSD.

## 10. Replay start and speed
Who decides: Jayden.
Questions: start the replay with 100 percent cash, or 100 percent SPY, pick one for both scenarios so scores compare. Replay speed: one day per button press, or auto advance every 5 seconds, button press is more interactive. Trading frequency: weekly rebalance only, or daily timing as well, weekly is simpler. Max sectors held: 3 or 4. Position size: equal weight or ranked weight, equal weight is simpler. Cash reserve: 5 or 10 percent, or allow 100 percent invested. Transaction cost: 0 in the demo and say so, or fixed 0.05 percent per trade. Slippage: 0 and say so.
If not decided: the rules engine cannot be written with confidence, and the 2020 and 2022 scores will not compare cleanly.

## 11. Voice reject: voice alone, or red button confirms
Who decides: Jayden.
Recommendation: voice reject only proposes a reject, red button confirms it. Voice never executes, and voice alone must not mark a proposal blocked. Safer than allowing voice to block a trade by itself in a noisy hall.

## 12. Cloud LLM allowed in home mode, and which provider
Who decides: Jayden.
Why it matters: home mode can use a cloud LLM for narration and for drafting proposals, if Jayden wants it. That affects cost and privacy. Booth mode must not need it. No provider was chosen in this research.

## 13. Airline and route
Who decides: Jayden.
Why it matters: IATA and China Southern rules are used as the baseline, but the exact airline is not yet known. Rules change, and airlines must also follow local law. Power banks are strictly prohibited in checked baggage on China Southern, LIKELY, must go in carry-on only. Since June 28, 2025, CAAC has banned power banks without a 3C mark, with an unclear 3C mark, or recalled models, on domestic flights in China, VERIFIED. If you fly inside China, buy a 3C marked power bank after arrival. Do not use a non 3C power bank on a domestic flight.
Also: RTC coin cell, do not add an RTC battery unless the airline rule is confirmed, it is a lithium metal cell, rule UNVERIFIED. Hong Kong transit, if Hong Kong is on the route, add a Type G adapter, Hong Kong uses British three pin Type G at 220V, 50Hz, VERIFIED.

## 14. Spare official Pi PSU in the pack list
Who decides: Jayden.
Why it matters: a spare official Pi PSU is CAD 16.95, VERIFIED, and it is the single part whose failure kills the whole demo. Pack it if the budget allows. Pack a spare USB-C cable, short and thick, for the monitor.

## 15. Is the Iozzia-Lab agent-remote repo the intended prior art
Who decides: Jayden, only if the submission cites prior art by name.
Why it matters: at least 5 different projects are named agent-remote. They are not the same project. The Iozzia-Lab one is the ESP32 Core2 one. The smatt989 one is a Mac and phone one. Cite the full owner and repo, not just the name.

## 16. Should the bridge use the Claude Code hook pattern, or a vault watcher only
Who decides: Jayden, with the builder.
Why it matters: prior art uses hooks, PreToolUse hook, POST to a local device, poll for a decision, return allow or deny. SI Console uses a vault. The bridge must decide how a vault status change becomes a button press, and how a button press becomes a vault status change. The blueprint specifies a vault watcher only, with state.json as the dashboard source. A hook is not specified for v1.

## 17. Should voice approval ever be allowed as a backup if a button fails
Who decides: Jayden.
Recommendation: no, voice proposes only. A.I.R.A. allows verbal yes, but voice can be misheard, spoofed by a nearby speaker, or triggered by booth noise. Keep the rule, or write down an exception. Do not leave it undecided.

## 18. Mini screen chain: live view of vault status, or a separate state machine
Who decides: Jayden, with the builder.
Why it matters: prior art has no chain view. The blueprint specifies a live view of vault status, via state.json, updated by the bridge from task notes. The dashboard must refresh from state.json, not by polling the vault. If the bridge dies, LEDs must go to a safe state, all off, except kill LED on if kill was active.

## 19. Do you have access to a 3D printer, or only a library service
Who decides: Jayden.
Why it matters: library limit is 150 x 150 x 170 mm, up to 7 hours per model, PLA only, VERIFIED at NVDPL StoryLab. A full printed box will not fit in one piece, needs at least 3 parts, about 20 to 30 hours total, UNVERIFIED. Print only brackets and a wedge, not the whole box, if only a library service is available. Use PETG, not PLA, for a booth case if printing outside the library.

## 20. Box colour: black or grey
Who decides: Jayden.
Why it matters: black shows fingerprints less in photos, grey shows labels better. The Hammond 1554XAGY is grey. A black box would be a different model number. Low priority, decide at order time.
