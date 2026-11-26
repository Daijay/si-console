# SI Console Overview

Rev R3. Date 2026-11-23.
Model note: the router options below are the 2026-11-23 two-option decision. The ACCEPTED four-tier roster with Jev judge is in `docs/MODEL_TIERS.md` (2026-11-25).
Team: Jayden (overall, hardware, integration), Hasan (CAD, Fusion 360), Christopher (software architecture, model router).
Build deadline Dec 8, 2026. Booth at Maker Faire Shenzhen, Dec 12-13, 2026.

## 1. What SI Console is

SI Console is a physical console for dispatching and supervising a team of general-purpose AI agents. The user talks to it or presses buttons. The agents propose work. Nothing runs until the user presses the green button. The red button rejects. The kill switch freezes everything. The brain is the DeepSeek API, reached over the internet. Trading is one skill: price-only sector rotation with paper money, replaying 2020 and 2022. It is not the whole product. No real money is connected.

## 2. Connection diagram

![Connection diagram, Pi 5 in the middle, every part around it](../blueprints/2d/connection-diagram-R3.png)

Pi 5 sits in the middle. Each line is labelled with the connection type. GPIO map: COORD GPIO5, AGENT 1 GPIO6, AGENT 2 GPIO13, GUARD GPIO19, green button LED GPIO20, red button LED GPIO21. All 6 LEDs run through the ULN2003. Resistors: COORD green 150 ohm, AGENT 1 white 100 ohm, AGENT 2 blue 100 ohm, GUARD yellow 220 ohm. Button LEDs use their built-in resistors. Kill switch, push to talk and toggle grounds go to the GND bus on the perfboard, fed from Pi pins 6, 9 and 14. GPIO26 is free. ULN2003 IN7 is tied to GND. Full diagram: blueprints/2d/connection-diagram.svg.

## 3. Parts

| Part | What it does | Connects to | Price CAD | Status |
|---|---|---|---|---|
| Raspberry Pi 5, 8 GB | Computer. Runs bridge, coordinator, dashboard. | Everything, see diagram | 249.50 | Confirmed |
| Pi 5 power supply, 27W USB-C | Powers the Pi 5. 5.1V 5A. | Pi 5 USB-C, wall | 16.95 | Confirmed |
| Active cooler | Cools the Pi 5. | Pi 5 fan header | 9.29 | Unconfirmed |
| microSD 128GB | OS and vault storage. | Pi 5 microSD slot | 41.99 | Unconfirmed |
| Spare microSD 32GB | Spare card in case the main card fails at the booth. | Pi 5 microSD slot | 27.99 | Confirmed |
| Mini screen, Waveshare 5 inch HDMI (H) | Agent chain view. 800x480. Touch disabled. | Pi 5 micro HDMI1, own USB charger | 73.95 | Confirmed |
| USB microphone, FIFINE AM8 | Voice input. Push to talk only. | Pi 5 USB-A | 79.99 | Unconfirmed |
| USB speaker, soundbar | Voice output. Dual 3W. Not modelled in the R5 CAD yet. | Pi 5 USB-A | 25.99 | Unconfirmed |
| Arcade buttons, 30 mm, 5 pack | Green approves, red rejects. | Pi 5 GPIO17, GPIO27, GND | 24.99 | Estimated |
| Kill switch, APEM 22 mm latching | Freezes all agents. Normally closed. | Pi 5 GPIO22, GND | 57.37 | Confirmed |
| Push to talk button, 12 mm | Starts voice input while held. | Pi 5 GPIO23, GND | 14.99 | Estimated |
| LED kit, 5 mm, 50 pcs | 6 status LEDs. | ULN2003 outputs, 5V rail | 5.38 | Confirmed |
| Resistor kit, 64 values | LED resistors. 150, 220, 100 ohm. | LED anodes, 5V rail | 17.00 | Estimated |
| Wiring kit: perfboard, jumper wires, spade connectors, breadboard | Builds the LED and button circuits. | GPIO breakout to perfboard | 52.96 | Unconfirmed |
| Acrylic sheets, 3 mm, 6 pack | Laser-cut case. 360 x 240 x 140 mm. | Case panels, finger joints | 52.98 | Unconfirmed |
| Mounting hardware: standoff kits | Standoffs and screws. Pi holes are M2.5. | Pi 5 mounting holes | 32.66 | Unconfirmed |
| Printed wedge, library PLA | Mini screen wedge and Pi bracket. | Top panel, Pi 5 | 10.00 | Unconfirmed |
| Micro HDMI adapters, 2 pack | Pi micro HDMI to full-size HDMI cables. | Pi 5 HDMI0, HDMI1 | 19.98 | Unconfirmed |
| ULN2003 driver, 3 pcs | Drives 6 LEDs from 5V. Sink only. | Pi 5 GPIO5/6/13/19/20/21 | 5.37 | Confirmed |
| Toggle switch, 12 mm | Language toggle, EN and Chinese. | Pi 5 GPIO24, GND | 9.99 | Estimated |
| GPIO breakout, Cobbler Plus | Breaks out the 40-pin header. | Pi 5 header to breadboard | 11.80 | Confirmed |
| Case fan, 5V 40 mm | Rear wall exhaust. 140 mA. | Pi 5 5V and GND pins | 4.19 | Confirmed |
| API credits, DeepSeek and Bocha | Paid model and search APIs for the live demo. | Network, no wiring | 40.00 | Estimated |
| Main monitor, MSI PRO MP165 E6 | Main screen. 15.6 inch, 1920x1080 IPS. | Pi 5 micro HDMI0, own USB-C charger | 89.99 | Unconfirmed, self-funded, bought |

Case size 360 x 240 x 140 mm is estimated, not a CAD result. Confirm before cutting. Front panel holes: LEDs 5.2 mm, buttons 30.2 mm, kill 22.3 mm, PTT and toggle 12.2 mm. See blueprints/2d/case-drawings.svg. Note: the monitor row above is self-funded and not counted in the fundable total. Some rows in this table predate Rev R5; the only current BOM is `bom/BOM.csv`, fundable total 885.81 CAD.

## 4. Totals

Fundable (2026-11-24, from `bom/BOM.csv`): 885.81 CAD before tax, 992.11 CAD with 12 percent BC tax. This includes the USB soundbar (25.99), the spare microSD (27.99) and DeepSeek and Bocha API credits (40.00). Self-funded (monitor, brick, travel adapter): 128.24 CAD before tax, 143.63 CAD with tax. Team limit about 800 CAD, hard max 900 CAD. The fundable total is 51.13 CAD over the 800 limit before tax and under the 900 hard max before tax; with tax it is 92.11 CAD over the hard max. Totals exclude shipping, laser time, and tools.

## 5. Open decisions

1. Case. Option A: clear 3 mm laser-cut acrylic, sheets 52.98 CAD, laser time extra. Files must go Nov 23, MakerLabs takes 5 to 7 business days. Option B: black nylon factory print, about 125 to 145 CAD all in at JLCPCB, estimated, not a real quote. It arrives by Dec 1 only through JLCPCB, with no slack, and it needs a full redesign, 1 to 2 days of CAD, because finger joints do not print. Recommendation: keep acrylic for the Dec 8 build.
2. Mini screen. Option A: 5 inch Waveshare HDMI (H), 800x480, 73.95 CAD, confirmed, uses Pi HDMI1, powered by its own USB charger. Option B: no 5.5 inch Waveshare DSI touchscreen exists. Both 5.5 inch Waveshare displays are HDMI. The real DSI option is the 5 inch Waveshare DSI LCD, SKU 18396, 800x480, 66.99 CAD plus a 6.95 CAD cable, about 73.94 CAD total, unconfirmed, same price as HDMI. It needs a config.txt overlay, Rev2.2 only, and a top panel redraw. Recommendation: keep HDMI.
3. Model router. Option A: DeepSeek plus Claude Fable 5.2 tiers. Claude Fable 5.2 is real, API ID claude-fable-5-2, 8 USD input and 40 USD output per 1M tokens, confirmed on Anthropic docs. That is about 27 times DeepSeek flash input and 33 times its output. Anthropic policy does not support use by persons physically in mainland China, Hong Kong, or Macau, confirmed. Option B: DeepSeek only. Jayden's position: no Claude at the booth, because of cost and China access. Any router must fall back to DeepSeek only.
