# SI Console

SI Console stands for Super Intelligence Console. It is a physical console that allows agentic orchestration. There is a push to talk mic, an English/Chinese toggle, LEDs, a 5 inch status screen and a monitor dashboard. This hardware project showcases the physical process of agentic orchestration, not just something that lives in your computer.

![Hero render](docs/images/render_hero_R5.png)

## How to use it
Press and hold the push to talk button and speak. The agents work, the LEDs show which agent is active, and the 5 inch screen shows status. Risky actions wait for you to press the green button. The red button rejects. The kill switch freezes everything. The toggle switches between English and Chinese.

## Why I made it
I wanted agents that can't just run wild. Most AI agents live in a window on your computer, and if something goes wrong, the same software that's running away has to be the thing that stops it. A software approve button has that problem. If the agent or a prompt injection controls the software, it can press the button itself. So I put approval on a real button on its own wire. Nothing in the software can press it, and the kill switch cuts the signal no matter what the software does. It also makes the demo physical, because a visitor can press the big green button themselves. For low-risk actions like read-only searches, I plan to add approve on the touchscreen, so risky things need the real button and safe things stay fast. This is my first hardware project.

## Design
![Exploded view](docs/images/render_exploded_R5.png)
![Wiring diagram](blueprints/R5/wiring_diagram_R5.png)

- Raspberry Pi 5 8GB, ULN2003 driver for the LEDs, GPIO buttons, 5 inch HDMI status screen, MSI portable monitor
- Open frame on clear laser-cut acrylic, 2 sheets. No PCB, the circuit is on perfboard.
- Pin map: docs/GPIO_PIN_MAP.md

## Files
- CAD assembly (STEP): blueprints/R5/si_console_assembly_R5.step
- Per-part STEP files: blueprints/R5/step/
- Fusion source: [Fusion archive (R5)](cad/si_console_R5.f3d)
- Firmware and agent code: code/
- BOM with links: bom/BOM.csv (about CAD 851 before tax, the main monitor was bought by me and is not in the fundable total)

## Team
- Jayden: system, hardware, CAD, integration
- Christopher: software architecture and agent orchestration

## How I used AI
I came up with the idea and made the main decisions: the hardware, the open-frame design, and what to cut or add to stay on budget. I used AI for brainstorming, looking up part specs and prices, and Claude Code to generate first versions of the CAD scripts, wiring diagram, code and tests. I then reviewed what came out and decided what to change, keep or throw away. For example, I scrapped the boxed case because it hid the electronics.

## What's next
Christopher and I are each logging 5 to 6 hours a day while balancing IB. The plan is to get the design approved, order the parts, and finish the build by December 8, then take it to Maker Faire Shenzhen on December 11 to 14. We both want to travel there, show the project, and see Shenzhen. My biggest worry is running out of time to submit, especially waiting on design approval and parts shipping before the build.
