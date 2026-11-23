# SI Console, morning summary
Date: 2026-11-23. Session ran 00:00 to about 02:00 MST, ahead of the plan clock.
Status: DRAFT REFERENCE. Not for Fallen submission.

## Read this first
The private GitHub repo was NOT created. The approval timed out while you slept, and no approval card is left. Tell me to retry and I will create Daijay/si-console as private and push the snapshot. Do not assume a repo link exists.

## What finished
- SI_Console_Overview.md: 2 page shareable doc, connection diagram, parts table, 3 decisions.
- SI_Console_Detailed.md: full compiled doc, 13 sections, fixed after a skeptic review.
- Blueprints R3: 4 redrawn 2D drawings as SVG and PNG, plus a connection diagram.
- 3D model: parametric CadQuery case and parts, 24 STEP files, 6 STL files, 5 renders.
- ONSHAPE_IMPORT.md: step by step Onshape and Fusion 360 import guide.
- Code: DeepSeek models pinned, router stub, GPIO Rev R2, 79 tests pass.
- Skeptic review: reviews/11-skeptic-r3.md. The doc contradictions it found are fixed.

## Shared workspace
- Local snapshot is ready in repo/: README, both docs, Onshape guide, BOM, GPIO map, 5 SVGs, 24 STEP files.
- No Onshape document exists. No Onshape login was available. Follow ONSHAPE_IMPORT.md to import the STEP files.
- PNG renders and STL files cannot go through the GitHub connector. They are binary. They live in blueprints-R3/ in the local workspace.

## Budget, Rev R2.1, VERIFIED by re-add
- Fundable: 845.31 CAD before tax, 946.75 CAD with tax.
- With both cuts (spare microSD 27.99, USB soundbar 25.99): 791.33 CAD before tax, 886.29 CAD with tax.
- Self-funded: 128.24 CAD before tax, 143.63 CAD with tax. Monitor, power brick, travel adapter.
- All-in with tax: 1090.38 CAD, before shipping and laser. With laser, shipping, tools: about 1240.38 to 1330.38 CAD.
- Core after all cuts, with both proposed cuts: 612.41 CAD before tax, 685.90 CAD with tax. Still 212.41 CAD over the 400 CAD target.
- Team limit is about 800 CAD, hard max 900 CAD. The 845.31 CAD fundable total is over the limit. With both cuts, 791.33 CAD is under the limit and under the hard max.

## The 3 decisions
1. Case: keep clear acrylic. Nylon costs about 125 to 145 CAD all in at JLCPCB, ASSUMED, needs 1 to 2 days redesign, and likely misses Dec 1. Acrylic is about 103 to 153 CAD with laser, files go today, arrives by Dec 2. Recommendation: acrylic now, nylon as a second case later.
2. Mini screen: keep the 5 inch HDMI screen. The brief's 5.5 inch DSI touchscreen does not exist. The real DSI option is the 5 inch DSI LCD, about the same price, 73.94 CAD, but it needs a cable, an overlay test, a Rev2.2 check, and a top panel redraw. Recommendation: HDMI.
3. Model router: DeepSeek only at the booth. Claude Fable 5.2 is real, claude-fable-5-2, 8 USD input and 40 USD output per 1M tokens, about 27x DeepSeek flash. Anthropic policy does not support use by persons physically in mainland China. The router stub falls back to DeepSeek only. Recommendation: DeepSeek only, premium tier maps to deepseek-v4-pro.

## Top risks
1. No laser cut file exists. The R3 drawing has no cut geometry. The files must go today. This is the most likely reason the build fails.
2. Fallen submission is due today and nothing has been sent. Grant cap is still unknown.
3. Recorded fallback format is still undefined. If the internet fails in Shenzhen, the demo is 4 minutes of dead air.
4. Voice is the weakest part. SenseVoice Small is untested on Pi 5 ARM64. Chinese STT is weakest. Text input fallback is not designed.
5. Green LED Vf is disputed, 2.2V vs 3.0V, both ASSUMED. Measure it on the bench before soldering.

## Code: what it can and cannot do
- Can: coordinator loop, tool registry, approval gate, kill handling, vault writer, router stub that fails closed to DeepSeek. 79 tests pass with mocked DeepSeek and mocked GPIO.
- Found and fixed: the coordinator passed role names where tool names were expected, so every tool call was blocked. Regression tests cover it.
- Cannot yet: no live DeepSeek call, thinking field wire shape is LIKELY. Approval pause is a skeleton, it logs and does not wait for the bridge. No message history, no STT or TTS, no Bocha test.

## Single next step
Today: get Hasan's laser cut file, send it to MakerLabs, and at the Fallen submission ask the grant cap in CAD and the approval time in business days. Ask MakerLabs if an 18 year old can use the drop-in LaserLab alone.
