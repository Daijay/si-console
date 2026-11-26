# SI Console Detailed

Date: 2026-11-23.
Rev: R2.1 for BOM and power. Wiring and GPIO map follow GPIO_PIN_MAP.md (updated 2026-11-24). Rev R3 for the case drawings, power diagram, and 3D model. The R3 drawings supersede the R2 drawings. The R3 drawings and 3D files are in blueprints/; the current CAD source is in cad/.
Model note: the model-router sections below describe the 2026-11-23 two-option decision (DeepSeek plus Claude vs DeepSeek only). The ACCEPTED four-tier roster with Jev judge is in `docs/MODEL_TIERS.md` (2026-11-25) and supersedes those options for model selection.
Search note (2026-11-26): web search now runs on Zhipu's Web Search API with the GLM key (`code/si_console/websearch.py`); Bocha is only an optional fallback, because a Bocha account could not be created. The Bocha sections below are historical.
Rule: plain words, short sentences, no em dashes.
Status words: "confirmed" means the page or source was opened and checked. "Unconfirmed" means a search result or secondhand claim only. "Estimated" means a figure nobody has measured or checked. Never treat an estimate as fact.

## 1. Overview

| Item | Fact |
|---|---|
| What it is | A physical console for dispatching and supervising a team of AI agents. Confirmed from the brief. |
| Tagline | Talk to dispatch, press to approve. Confirmed from the brief. |
| Core rule | Voice proposes. A model proposes. Only a physical green button approves and executes. Confirmed from the brief. |
| Trading role | Trading is one skill, not the whole product. Price-only sector rotation, paper money only, 2020 and 2022 replay. Confirmed from the brief. |
| Real money | None connected. No real money moves. Confirmed from the brief. |
| Booth | Maker Faire Shenzhen, Dec 12 to 13, 2026. Confirmed from the brief. |
| Build deadline | Dec 8, 2026. Confirmed from the brief. |
| Design submission | Mon Nov 23, 2026. Confirmed from the brief. |
| Parts target | About Nov 30, 2026. Confirmed from the brief. |
| Team | Jayden, overall system, hardware, integration. Hasan, CAD in Fusion 360. Christopher, software architecture, model router. Confirmed from the brief. |
| Brain | DeepSeek API, OpenAI-compatible tool calling. Confirmed from the brief. |
| Search | Bocha API, works in China. Confirmed from the brief. |
| Computer | Raspberry Pi 5 8GB, official 27W PSU, active cooler. Confirmed from the brief. |
| Main screen | MSI PRO MP165 E6 15.6 inch portable monitor, bought, self-funded. Confirmed from the brief. |
| Mini screen | Waveshare 5 inch HDMI LCD (H), 800x480, touch disabled. Confirmed from the brief. |
| Case | Clear 3 mm laser-cut acrylic, finger joints. This is now one of the 3 open decisions. See section 13. |
| No lithium battery | Wall power only. Confirmed from the brief. |
| No custom PCB | Breadboard prototype first, solder later. Confirmed from the brief. |

What a visitor sees: a console on a desk, a main screen with a dashboard, a small screen with the agent chain, 4 status LEDs, a green approve button, a red reject button, a red mushroom kill switch, a push-to-talk button, and a language toggle. The visitor talks to dispatch, watches agents work, then presses green or red. Nothing runs without the press.

## 2. Full BOM with links and status

Totals updated 2026-11-24 from `bom/BOM.csv`. All prices in CAD. Tax is 12 percent BC tax. The part tables in sections 2.3 to 2.5 are the older R2.1 list; `bom/BOM.csv` is the only current BOM.

### 2.1 Totals

| Line | Amount CAD | Status |
|---|---|---|
| Fundable, before tax | 885.81 | Re-added from BOM.csv |
| Fundable, tax 12 percent | 106.30 | Tax on every line is estimated |
| Fundable, with tax | 992.11 | Computed |
| Self-funded, before tax | 128.24 | From the R2.1 summary |
| Self-funded, with tax | 143.63 | From the R2.1 summary |
| All-in, with tax, before shipping and laser | 1135.74 | Computed |
| All-in, with laser, shipping, tools | About 1246.90 to 1336.90 | Estimated |
| Core after voice cut (120.97) and mini screen cut (83.94), before tax | 646.22 | Computed |
| Same, with tax | 723.77 | Computed |
| Team limit | About 800 | Confirmed from the brief. Exceeded by 85.81 before tax |
| Hard max | 900 | Confirmed from the brief. Exceeded by 92.11 with tax |
| 400 CAD target, missed by | 246.22 before tax, even after both cuts | Computed |

Status mix of the fundable total: confirmed 508.98, unconfirmed 269.86, estimated 106.97. Do not treat the total as verified.

### 2.2 Spare card, soundbar and API credits

The earlier proposal to cut the spare 32GB microSD (27.99) and the USB soundbar (25.99) is withdrawn: both are in the BOM again as of 2026-11-24. API credits for DeepSeek and Bocha (40.00) were added. The soundbar is not modelled in the R5 CAD yet.

### 2.3 Fundable parts

| Part | Exact model | Qty | Unit CAD | Line CAD | Store | Status | Link |
|---|---|---|---|---|---|---|---|
| Raspberry Pi 5 8GB | Raspberry Pi 5 8GB SC1112 | 1 | 249.50 | 249.50 | PiShop.ca | Confirmed | https://www.pishop.ca/product/raspberry-pi-5-8gb/ |
| Pi 5 power supply | Raspberry Pi 27W USB-C PSU Black US SC1158 | 1 | 16.95 | 16.95 | PiShop.ca | Confirmed | https://www.pishop.ca/product/raspberry-pi-27w-usb-c-power-supply-black-us/ |
| Active cooler | Official Raspberry Pi 5 Active Cooler SC1148 | 1 | 9.29 | 9.29 | RobotShop Canada | Unconfirmed | https://ca.robotshop.com/products/official-raspberry-pi-5-active-cooler |
| microSD 128GB | SanDisk Extreme microSDXC 128GB SDSQXAA-128G-GN6MN | 1 | 41.99 | 41.99 | TopSelect.ca | Unconfirmed | https://www.topselect.ca/products/sandisk-extreme-microsdhc-uhs-i-memory-card-2 |
| Spare microSD 32GB | SanDisk Ultra microSDHC 32GB SDSQUA4-032G-GN6MA | 1 | 27.99 | 27.99 | TopSelect.ca | Confirmed | https://www.topselect.ca/products/sandisk-ultra-microsdxc-uhs-i-memory-card-2 |
| Mini screen 5 inch | Waveshare 5inch HDMI LCD (H) SKU 14300, 800x480 capacitive | 1 | 73.95 | 73.95 | PiShop.ca | Confirmed | https://www.pishop.ca/product/5inch-hdmi-lcd-h-display-800x480-capacitive/ |
| USB microphone | FIFINE AmpliGame AM8 black USB/XLR dynamic | 1 | 79.99 | 79.99 | Best Buy Canada | Unconfirmed | https://www.bestbuy.ca/en-ca/product/fifine-ampligame-am8-xlr-usb-dynamic-gaming-microphone-black/19513447 |
| USB speaker | USB Computer Speaker soundbar dolaerOPOCCACAE103, dual 3W | 1 | 25.99 | 25.99 | Best Buy Canada | Unconfirmed | https://www.bestbuy.ca/en-ca/product/usb-computer-speaker-laptop-speaker-with-stereo-sound-enhanced-bass-portable-mini-sound-bar-for-windows-pcs-desktop-computer-and-laptops/16485058 |
| Arcade buttons | EG STARTS 5x 30mm Arcade LED Push Buttons 5V B01N11BDX9 | 1 | 24.99 | 24.99 | Amazon.ca | Estimated | https://www.amazon.ca/dp/B01N11BDX9 |
| Kill switch | APEM IDEC YW1B-V4E02R 22mm latching DPST-NC | 1 | 57.37 | 57.37 | DigiKey.ca | Confirmed | https://www.digikey.ca/en/products/detail/apem-inc/YW1B-V4E02R/15216544 |
| Push to talk button | Gebildet 5pcs 12mm momentary prewired stainless steel B08L49F7DV | 1 | 14.99 | 14.99 | Amazon.ca | Estimated | https://www.amazon.ca/dp/B08L49F7DV |
| LED kit | DFRobot LED Kit FIT0242 50pcs 5mm 5 colours | 1 | 5.38 | 5.38 | DigiKey.ca | Confirmed | https://www.digikey.ca/en/products/detail/dfrobot/FIT0242/25558500 |
| Resistor kit | Resistor Kit 1280 pieces 64 values 1/4W metal film B07L851T3V | 1 | 17.00 | 17.00 | Amazon.ca | Estimated | https://www.amazon.ca/dp/B07L851T3V |
| Perfboard | ELEGOO double sided prototype board kit 32 pieces B072Z7Y19F | 1 | 17.99 | 17.99 | Amazon.ca | Unconfirmed | https://www.amazon.ca/dp/B072Z7Y19F |
| Jumper wires | ELEGOO 120pcs Dupont Wire M-F M-M F-F 20cm B01EV70C78 | 1 | 12.99 | 12.99 | Amazon.ca | Unconfirmed | https://www.amazon.ca/Elegoo-120pcs-Multicolored-Breadboard-arduino/dp/B01EV70C78 |
| Spade connectors | Feggizuli 280pcs Crimp Connectors 2.8mm 4.8mm 6.3mm | 1 | 13.99 | 13.99 | Amazon.ca | Unconfirmed | https://www.amazon.ca/dp/B07T6XJF1T |
| Acrylic sheets | Fovorica 4-pack plus Langaelex 2-pack, 12x16 inch clear cast acrylic 3mm | 1 | 52.98 | 52.98 | Amazon.ca | Unconfirmed | https://www.amazon.ca/dp/B0C5TP7FWT |
| Hardware kit | Hilitchi 360pcs M2 M3 M4 standoff screw nut kit | 1 | 22.99 | 22.99 | Amazon.ca | Unconfirmed | https://www.amazon.ca/dp/B013ZWM1F6 |
| Printed wedge | Mini screen wedge 15 degrees and Pi bracket, library PLA | 1 | 10.00 | 10.00 | Library StoryLab | Unconfirmed | No direct link. Library service. |
| Micro HDMI adapters | axGear HDMI-F to Micro HDMI-M converter cable, 2 pack | 2 | 9.99 | 19.98 | Best Buy Canada | Unconfirmed | https://www.bestbuy.ca/en-CA/product/axgear-hdmi-female-to-micro-hdmi-male-converter-cable-f-m-adapter-hdmi-type-a-to-microhdmi-d/12317193 |
| ULN2003 driver | TI ULN2003AN DIP16 7-channel Darlington array | 3 | 1.79 | 5.37 | DigiKey.ca | Confirmed | https://www.digikey.ca/en/products/detail/texas-instruments/ULN2003AN/277624 |
| Toggle switch | Joinfworld SPST ON-OFF toggle 12mm 4-pack | 1 | 9.99 | 9.99 | Amazon.ca | Estimated | https://www.amazon.ca/dp/B0C22K75FZ |
| GPIO breakout | Adafruit Assembled Pi Cobbler Plus, 40-pin breakout cable to breadboard | 1 | 11.80 | 11.80 | Solarbotics | Confirmed | https://www.solarbotics.com/product/assembled-pi-cobbler-plus-breakout-cable-for-pi-b-a-pi-2-pi-3-pi-4/ |
| Breadboard | MB-102 830-point solderless breadboard | 1 | 7.99 | 7.99 | North Spark Lab via Amazon.ca | Unconfirmed | https://www.northsparklab.com/products/mb-102-solderless-breadboard |
| 5V case fan | 5VDC 40mm fan 40x40x10mm 5V 140mA 6000RPM 6.8CFM | 1 | 4.19 | 4.19 | Solarbotics | Confirmed | https://www.solarbotics.com/product/14060/ |
| M2.5 standoff kit | XLX M2.5 male female standoff kit | 1 | 9.67 | 9.67 | Amazon.ca | Unconfirmed | https://www.amazon.ca/dp/B07FMV5RMG |

### 2.4 Notes on key rows

| Row | Note |
|---|---|
| Pi 5 8GB | Price 249.50 CAD, in stock at PiShop.ca. Confirmed 2026-11-20. |
| Active cooler | Price from previous blueprint. Not re-opened this pass. PiShop lists 7.15 CAD in search results. Use 7.15 if PiShop confirms at checkout. Unconfirmed. |
| Spare microSD 32GB | Replaces the spare 128GB at 41.99 CAD. Saves 14.00 CAD. Cheapest listing was Kingston 14.99 CAD, out of stock. A 10 CAD target is not achievable in Canada. Confirmed 2026-11-23. |
| Mini screen | Driver free per listing. PiShop FAQ says a config.txt change is needed per wiki. Test first. Power now comes from a separate USB charger Jayden owns, not from Pi USB. Confirmed. |
| USB mic | Sold and shipped by marketplace seller FIFINE CA. Online only. Price from search listings, not in fetched page text. Unconfirmed. |
| USB speaker | PiShop mini speaker confirmed out of stock 2026-11-23. This Best Buy soundbar replaces it. Price from search result only. Seller claims Windows, MacOS, ChromeOS only. Test on Pi before the booth. Bigger than the PiShop speaker. Check the front panel grille size first. Unconfirmed. |
| Arcade buttons | No CAD price found in this pass. CAD 24.99 is a conservative estimate. Recheck at checkout. Estimated. |
| Kill switch | In stock 188 at DigiKey.ca. 22.3 mm cutout. Pull or twist reset. Replaces a generic 19.99 CAD estimate, adds 37.38 CAD. Confirmed. |
| Resistor kit | Listing includes 150 ohm, 20 pieces, 1/4W metal film, plus 100 and 220 ohm. Unconfirmed. No separate 150 ohm pack is needed. |
| Acrylic sheets | 6 sheets total. 4-pack at 32.99 plus 2-pack at 19.99. Second link: https://www.amazon.ca/dp/B0C6KMSKSG. Prices from search results. Amazon.ca page opens failed with HTTP 403. Recheck at checkout. Unconfirmed. |
| Micro HDMI adapters | Short converter cable, not a rigid dongle. Use the cables that ship with both screens. Sale ends Nov 24, 2026. Unconfirmed. |
| ULN2003 | Price 1.79 CAD. Offer shows InStock. Page body also lists a 26 week manufacturer lead time. Confirm quantity at checkout. Order 3 for spares. Confirmed. |
| GPIO breakout | Breaks out to a solderless breadboard, not screw terminals. Listing says Pi B+, 2, 3, 4 only. The 40-pin header is the same. Adafruit lists the same T-Cobbler Plus for Pi 5. Replaces the Pi-EzConnect HAT at 29.95 CAD, saves 18.15 CAD. Confirmed. |
| 5V case fan | 2-wire red and black leads, 130 mm cable. Draws 140 mA, 0.7W. Mounts on the rear wall, exhaust high. Replaces the AC Infinity MULTIFAN S5 at 25.99 CAD, saves 21.80 CAD. Confirmed 2026-11-23. |
| M2.5 standoff kit | Needed because the Hilitchi kit has no M2.5. Pi mounting holes are M2.5. Unconfirmed. |

### 2.5 Self-funded and uncounted rows

| Part | Model | Qty | Unit CAD | Store | Status | Link |
|---|---|---|---|---|---|---|
| Portable monitor | MSI PRO MP165 E6 15.6 inch FHD IPS 60Hz | 0 in BOM, 1 bought | 89.99 | Canada Computers | Unconfirmed | https://www.canadacomputers.com/en/24-under-home-office-monitors/286526/msi-pro-mp165-e6-16-fhd-ips-60hz-4ms-gtg-business-monitor-pro-mp165-e6.html |
| Monitor power brick | Amazon Basics 20W One-Port USB-C Wall Charger PD 5V 3A | 0 | 15.26 | Amazon.ca | Unconfirmed | https://www.amazon.ca/dp/B08MVCMNDD |
| China travel adapter | DIWILI Universal Travel Plug Adapter 5 in 1 | 0 | 22.99 | Amazon.ca | Unconfirmed | https://www.amazon.ca/dp/B0CDP7PT2S |
| Fallback mic | SunFounder Mini USB 2.0 Microphone | 0 | 12.27 | RobotShop Canada | Unconfirmed | https://ca.robotshop.com/products/sunfounder-mini-usb-20-microphone-audio-adapter-plug-play-raspberry-pi-5-4 |
| Portable monitor alt | Waveshare 10.1 inch Capacitive Touch Display 24484 1280x800 | 0 | 160.95 | PiShop.ca | Unconfirmed | https://www.pishop.ca/product/10-1inch-capacitive-touch-display-wide-color-gamut-1280-800-optical-bonding-toughened-glass-panel-hdmi-type-c-display-interface/ |
| Spare Pi PSU | Raspberry Pi 27W USB-C Power Supply Black US SC1158 | 0 | 16.95 | PiShop.ca | Confirmed | https://www.pishop.ca/product/raspberry-pi-27w-usb-c-power-supply-black-us/ |

Monitor note: the BOM row lists the monitor as sold out online, in store pickup. The overnight brief of 2026-11-23 says the monitor is bought. The BOM stock field is stale. The monitor is self-funded and not in the fundable total.

Monitor spec, confirmed from MSI official spec: 356.5 x 13.85 x 210.35 mm, 0.78 kg, 1920x1080 IPS 60Hz, full-size HDMI 2.0b, USB-C DP Alt plus 15W PD, no power brick, ships with HDMI and USB-C cables, 2x 1W built-in speakers. Case is 360 mm wide, only 3.5 mm wider than the monitor.

## 3. Wiring and GPIO map

GPIO library: gpiozero only. RPi.GPIO does not work on Pi 5. Confirmed from the brief. Debounce 0.05 s for green, red, and push to talk. Kill switch bounce time 0.02 s. Kill poll every 100 ms. Confirmed from the brief.

### 3.1 Button and switch inputs

| Control | GPIO | Pin | Type | Notes |
|---|---|---|---|---|
| Green button, approve | GPIO17 | 11 | Momentary, active low, internal pull-up | One press approves one task only. On the start screen only, green picks the 2020 scenario. |
| Red button, reject | GPIO27 | 13 | Momentary, active low, internal pull-up | One press rejects one task. On the start screen only, red picks the 2022 scenario. |
| Kill switch | GPIO22 | 15 | Latching mushroom, normally closed | Closed reads LOW, normal. Open reads HIGH, frozen. Fail safe: a broken wire reads frozen. |
| Push to talk | GPIO23 | 16 | Momentary, active low | Hold to record. Release to transcribe. Mic is muted during TTS playback. |
| Language toggle | GPIO24 | 18 | SPST ON-OFF | Flips EN to ZH and back. Both screens follow. |

### 3.2 Status LED outputs, all through ULN2003

| LED | GPIO | Pin | ULN2003 input | ULN2003 output pin | Resistor | Colour |
|---|---|---|---|---|---|---|
| COORD | GPIO5 | 29 | IN1 | OUT1 pin 16 | 150 ohm | Green |
| AGENT 1 | GPIO6 | 31 | IN2 | OUT2 pin 15 | 100 ohm | White |
| AGENT 2 | GPIO13 | 33 | IN3 | OUT3 pin 14 | 100 ohm | Blue |
| GUARD | GPIO19 | 35 | IN4 | OUT4 pin 13 | 220 ohm | Yellow |
| Green button LED | GPIO20 | 38 | IN5 | OUT5 pin 12 | Built in, no extra resistor | Green |
| Red button LED | GPIO21 | 40 | IN6 | OUT6 pin 11 | Built in, no extra resistor | Red |
| Not wired | GPIO26 | 37 | IN7 tied to GND | OUT7 pin 10, unused | None | None |

Resistor values, decided by Jayden: COORD green 150 ohm, AGENT 1 white 100 ohm, AGENT 2 blue 100 ohm, GUARD yellow 220 ohm. LED forward voltages are estimates, not yet measured.

Bench check: measure each LED forward voltage and current with a multimeter. Pass if 5 to 20 mA per LED. The math is in GPIO_PIN_MAP.md.

Button LED note: the two button LEDs run from 5V through their built-in resistors, with no extra resistor. Confirm this on the delivered parts and measure the current with a multimeter. See open question Q12.

ULN2003 wiring: pin 8 GND to the common GND bus on the perfboard, which is fed from Pi GND pins 6, 9 and 14. Pin 9 COM to 5V. Do not tie COM to ground. Confirmed from the datasheet. The chip sinks only. LED path is 5V, resistor, LED anode, cathode to ULN2003 output, GND. GPIO HIGH means LED on.

ULN2003 facts: 7 channels, not 8. Inputs pins 1 to 7. GND pin 8. COM pin 9 to 5V. Outputs pins 16 to 10, reversed, OUT1 pin 16 to OUT7 pin 10. 500 mA per channel. Confirmed from the datasheet.

ULN2003 at 3.3V: test first, not guaranteed. Datasheet VIH min 2.4V, unconfirmed. Input at 3.3V gives about 0.7 to 1 mA, estimated. Most parts turn on, unconfirmed. The datasheet does not promise full saturation at 3.3V. Fallback if a channel is dim or warm: TBD62083A, probably 3.3V friendly, or a logic level MOSFET per LED. See open question Q11.

LED current, all 6 LEDs on: about 63 to 83 mA total, estimated. Heat about 0.07W, estimated. Pass if 5 to 20 mA per LED, measured. COORD green is 13.3 mA at Vf 2.2V or 8.0 mA at Vf 3.0V. Vce_sat about 0.8V, estimated. Vce_sat max is 1.6V per the DigiKey page, which would lower every current; see OPEN_QUESTIONS.md Q11.

### 3.3 LED behaviour

| State | Pattern |
|---|---|
| No task | Off |
| Working | Solid on |
| Queued | Slow blink |
| Blocked | Fast blink |
| Kill active | All 4 status LEDs off, red button LED solid on. If no red LED, KILL ACTIVE on screens only. |

Kill pattern picked 2026-11-20. Confirmed from the brief.

LED colours, decided: COORD green, AGENT 1 white, AGENT 2 blue, GUARD yellow. Red is for the reject button and the kill switch only.

### 3.4 Pin map in code

The code maps COORD to GPIO5 and GUARD to GPIO19 in code/si_console/gpio_map.py, which matches GPIO_PIN_MAP.md. The GPIO map tests check the pins and the resistor values.

### 3.5 Wire table

| From | To | Wire | Notes |
|---|---|---|---|
| GPIO5 pin 29 | ULN2003 IN1 | Jumper | COORD LED control |
| GPIO6 pin 31 | ULN2003 IN2 | Jumper | AGENT 1 LED control |
| GPIO13 pin 33 | ULN2003 IN3 | Jumper | AGENT 2 LED control |
| GPIO19 pin 35 | ULN2003 IN4 | Jumper | GUARD LED control |
| GPIO20 pin 38 | ULN2003 IN5 | Jumper | Green button LED control |
| GPIO21 pin 40 | ULN2003 IN6 | Jumper | Red button LED control |
| GND bus | ULN2003 IN7 | Jumper | IN7 tied to GND, GPIO26 not wired |
| 5V rail | ULN2003 COM pin 9 | Jumper | Never tie COM to ground |
| Pi GND pins 6, 9, 14 | GND bus on the perfboard | Jumper | Feeds the common GND bus |
| GND bus | ULN2003 GND pin 8 | Jumper | Common ground |
| GND bus | Kill switch, PTT button, toggle switch | Hookup wire | Second contact of each |
| Pi GND pin 14 | Green button contact | Hookup wire | Green button ground |
| Pi GND pin 20 | Red button contact | Hookup wire | Red button ground |
| 5V rail | Resistor, LED anode | Hookup wire | One resistor per status LED, on the anode side |
| 5V rail | Button LED | Hookup wire | Built-in resistor, no extra resistor |
| LED cathode | ULN2003 OUT pin | Hookup wire | OUT1 pin 16 to OUT6 pin 11 |
| GPIO17 pin 11 | Green button contact | Twisted pair with GND | Keep button wires under 30 cm |
| GPIO27 pin 13 | Red button contact | Twisted pair with GND | Keep button wires under 30 cm |
| GPIO22 pin 15 | Kill switch NC contact | Twisted pair with GND | Kill switch wired normally closed |
| GPIO23 pin 16 | PTT button contact | Twisted pair with GND | Keep button wires under 30 cm |
| GPIO24 pin 18 | Toggle switch contact | Twisted pair with GND | Language toggle |
| Pi micro HDMI 0 | MSI monitor HDMI | Adapter cable | Main screen, closest to USB-C power |
| Pi micro HDMI 1 | Mini screen HDMI | Adapter cable | Mini screen, HDMI (H) model |
| Pi USB | FIFINE AM8 mic | USB cable | Mic draws 0.10A, estimated |
| Pi USB | USB soundbar | USB cable | Soundbar draw estimated about 0.5A max, not measured |
| Pi 5V rail | 5V case fan | 2-wire lead | Fan draws 140 mA, confirmed |

Wire labels: G, R, K, PTT, LANG, COORD, AGENT 1, AGENT 2, GUARD, GND. Label every wire.

## 4. Power budget

Rev R2.1 update, 2026-11-22. This section supersedes the old budget in TEST_PLAN.md T4 and OPEN_QUESTIONS.md Q29. Those files still show the old numbers. Do not use them.

### 4.1 What changed in Rev R2.1

| Change | Effect |
|---|---|
| Mini screen moved to Jayden's own USB phone charger | Frees about 0.4A Pi USB headroom. Estimated. |
| MSI monitor on its own USB-C charger | Never from Pi USB. Monitor draws 10W on, needs 15W USB-C PD, 1.4A typical, 2.0A peak at 5V. That alone exceeds the 1.6A Pi USB limit. Confirmed from the brief. |
| Powered USB hub removed | Minus 61.99 CAD. Mini screen no longer needs the hub. |
| 5V case fan added | Solarbotics 40 mm fan, 140 mA, from the Pi 5V rail, not from USB. Confirmed. |

### 4.2 Pi USB loads, Rev R2.1

| Load | Current | Source |
|---|---|---|
| USB mic, FIFINE AM8 | 0.10A | Estimated |
| USB soundbar | About 0.5A max | Estimated, not measured |
| Mini screen | 0A from Pi | Powered by Jayden's own USB phone charger. Confirmed from the brief. |
| Main monitor | 0A from Pi | Powered by its own USB-C charger. Confirmed from the brief. |
| Total Pi USB peak | About 0.6A | Estimated |
| Pi USB limit, official 27W PSU | 1.6A | Confirmed from the brief |
| Headroom | About 1.0A | Estimated |

Old budget, superseded: mini screen 0.40A, mic 0.10A, speaker up to 1.00A peak, total peak 1.50A vs 1.6A limit, headroom 0.10A. That budget is dead. Do not quote it.

### 4.3 Power rules

| Rule | Fact |
|---|---|
| Pi PSU | Official Raspberry Pi 27W USB-C, 5.1V 5A, input 100 to 240V. Confirmed. Use it for the Pi only. |
| Phone charger for Pi | Do not use one. Most 65W GaN chargers give 5V at 3A only, which limits Pi USB to 600 mA and risks brownout. Confirmed from the brief. |
| Monitor power | Own USB-C charger only. Never from Pi USB. Confirmed from the brief. |
| Mini screen power | Jayden's own USB phone charger. Never from Pi USB. Confirmed from the brief. |
| Speaker volume | Cap at 50 percent in booth mode. Confirmed from the brief. |
| Touch USB cables | Do not connect them. Touch is not needed. Saves ports and USB load. Confirmed from the brief. |
| Pi peak 19.4W | Ambiguous. Unclear if 3.9A includes USB. Estimated as a warning, not a measured value. |
| All USB currents | Estimated until measured with a USB meter on the real build. |
| Fan | 5V case fan draws 140 mA from the Pi 5V rail, not from USB. Mounts on the rear wall, exhaust high. Confirmed. |

### 4.4 Power test, summary

Run vcgencmd get_throttled. It must be 0x0 after 10 minutes with both screens on, after 30 minutes at full CPU load plus microSD write plus speaker at 50 percent, and after 5 minutes with the speaker at max volume. Plug and unplug the main monitor while the Pi runs. The Pi must not reboot. If it does, the monitor was drawing from the Pi. Fix the wiring. Power cycle 5 times. No microSD corruption. dmesg must show no undervoltage lines. Full test is T4 in TEST_PLAN.md. T4 now lists the Rev R2.1 budget, updated 2026-11-23.

## 5. Case design

### 5.1 Acrylic option, Rev R2

This is the current design. It is also one of the 3 open decisions. See section 13.1.

| Item | Fact |
|---|---|
| Material | Clear 3 mm laser-cut cast acrylic. Cast cuts clean on CO2 laser. Confirmed from the brief. |
| Joints | Finger joints, teeth 15 mm wide, 3 mm deep, all edges. Estimated. |
| Outer size | 360 W x 240 D x 140 H mm. Estimated proposal, not a CAD result. Confirm before cutting. |
| Front and back panels | 360 x 134 mm. Height is 140 minus 2x3 mm. Confirmed from the drawing. |
| Side panels | 234 x 134 mm. Depth is 240 minus 2x3 mm. Estimated. |
| Top and bottom panels | 360 x 240 mm. Estimated. |
| Kerf | 0.2 mm. Estimated. Test joints on scrap first. |
| Sheets | 4x 12x16 inch (305x406 mm) cast acrylic. The BOM buys 6 sheets, a 4-pack plus a 2-pack, 52.98 CAD, so 2 sheets are spare. Confirmed from BOM.csv. |
| Laser vendor | MakerLabs Vancouver, full service 5 to 7 business days, 2.50 CAD per min, 50 CAD minimum. Unconfirmed. Drop-in LaserLab 2 CAD per min, orientation class required first. Age rule for Jayden at 18 is unconfirmed. |
| Do not cut | PVC, vinyl, or ABS. They release toxic gas. Confirmed from the brief. |

### 5.2 Panels

| Panel | Size mm | Holes and cutouts |
|---|---|---|
| Front | 360 x 134 | See table 5.3. |
| Back | 360 x 134 | R3 fix: one shared micro HDMI slot X 61 to 90, Z centred 14, for both micro HDMI ports. USB-C power slot X 46 to 56, Z centred 14. Port height is Z 12 to 16, not Y 20 from the top. Exact X depends on the Pi mount position, confirm in CAD. Vent slots 6x 4x20 mm, low, X 40 to 200 Y 100. Pi USB and ETH access: do not cut a large window. |
| Top | 360 x 240 | Mini screen bezel cutout 122 x 90.5 mm estimated at X 119 Y 75. Screen module 121 x 89.48 mm confirmed size. Screw holes 3.2 mm estimated, corners offset 5 mm. Vent slots near rear, 6x 4x20 mm estimated. |
| Bottom | 360 x 240 | 4x Pi standoff holes M2.5. 4x rubber feet holes 5 mm estimated. No vent slots on the bottom. Dust and spills. |
| Left side | 234 x 134 | Vent slots 6x 4x20 mm, high, exhaust. No cable holes. Estimated. |
| Right side | 234 x 134 | Vent slots 6x 4x20 mm, high, exhaust. Cable gland hole 12 mm estimated, optional. |

### 5.3 Front panel holes, centres from top-left of panel

| Hole | Size mm | Centre X | Centre Y | Status |
|---|---|---|---|---|
| LED COORD | 5.2 | 70 | 22 | Estimated |
| LED AGENT 1 | 5.2 | 100 | 22 | Estimated |
| LED AGENT 2 | 5.2 | 130 | 22 | Estimated |
| LED GUARD | 5.2 | 160 | 22 | Estimated |
| Green button | 30.2 | 70 | 75 | Confirmed from the drawing |
| Red button | 30.2 | 150 | 75 | Confirmed from the drawing |
| Kill switch | 22.3 | 235 | 75 | Confirmed from the drawing |
| Push to talk | 12.2 | 295 | 75 | Confirmed from the drawing |
| Language toggle | 12.2 | 330 | 75 | Estimated |
| Speaker grille | 20 holes 3 mm, 40x40 mm | 300 | 100 | Estimated. Omit the grille if the soundbar cut is taken. |

Hole clearance: buttons 30.2 mm for 30 mm, kill 22.3 mm for 22 mm, PTT and toggle 12.2 mm for 12 mm, LEDs 5.2 mm for 5 mm. Snap-in buttons need 1 to 5 mm panel. 3 mm acrylic satisfies this. Confirmed from the drawing.

Front panel hole centres are estimated. Measure real buttons with calipers and test in cardboard first.

### 5.4 Inside layout

| Item | Fact |
|---|---|
| Pi | Rear left, on M2.5 standoffs, 10 mm high. Leave 25 mm clear above the Pi for the active cooler and for air. |
| Perfboard with ULN2003 | Centre, on M3 screws. |
| Speaker | Front right inside, behind the front face, at least 20 mm from the Pi. |
| Clearance | 50 mm clear behind buttons. 75 mm behind kill. |
| Kill switch depth | APEM depth 78.3 mm vs 75 mm clearance, 3.3 mm over. Check in the CAD redraw. See open question Q34. |
| Mic | Do not mount inside the box. External USB mic on a short cable, on the desk to the left of the box. |
| Vents | Intake low, exhaust high. Total vent area 1440 mm2, estimated. Case fan added in Rev R2.1, rear wall, exhaust high. |
| Photo | Take a photo of the inside before closing it for the last time. |

### 5.5 Case options, both sides

| Item | Option A: clear 3 mm laser-cut acrylic | Option B: black nylon factory print |
|---|---|---|
| Material | Clear cast acrylic, 3 mm, finger joints | Black nylon, likely a factory print |
| Cost | 52.98 CAD for 6 sheets, unconfirmed | About 125 to 145 CAD all in at JLCPCB, estimated, not a real quote. A real quote needs the STL files. |
| Laser or print time | MakerLabs full service 5 to 7 business days, unconfirmed. Drop-in same day if the age rule allows. | JLCPCB only: 72 hours production plus 3 to 5 business days DHL. Arrives by Dec 1 only with no slack. PCBWay and Xometry miss Dec 1. |
| Electronics visible | Yes, clear panels | No |
| Heat | Acrylic insulates. Vents plus case fan. Heat test T6 decides. | Nylon also insulates. Vents plus case fan. Same test. |
| CAD work | Hasan draws 6 flat panels in Fusion 360 | Full redesign, 1 to 2 days, estimated. No finger joints. Screw bosses or brackets. |
| Status | Current design, Rev R2 drawings exist | Recommendation: keep acrylic for the Dec 8 build. Nylon as a second case after Fallen. |

Optional variant in the drawings: plywood front panel, 3 mm, same laser, same holes, about 10 to 15 CAD per sheet estimated. Hides the electronics. Decide in the CAD phase.

## 6. Software architecture

### 6.1 Processes

| Process | Job | Notes |
|---|---|---|
| Bridge | Watches the vault, drives LEDs and both screens, routes button presses, serves the external agent API | Runs on the Pi. Watchdog or inotify primary, 1 s poll fallback, 200 ms debounce, hash map, state.json cache. Vault wins on conflict. |
| Coordinator | Picks actions from a fixed menu of 12, calls DeepSeek, runs tools, enforces the approval gate | Max 3 rounds per task, then escalates to human with reason ROUND_LIMIT. |
| Dashboard | Main screen, Chromium kiosk | Shows portfolio, sector ranking, current proposal, status, language, mode. |
| Mini screen view | Mini screen, agent chain only | 4 rows, one per agent, status and current task id, large text, no interaction. Separate process or one dashboard process is undecided. See open question Q5. |
| Voice | Push-to-talk STT, Piper TTS | Offline only. STT is SenseVoice Small first, faster-whisper Base fallback. TTS is Piper. |

Ports: dashboard 8000, API 8001. Both estimated.

### 6.2 Coordinator rules

| Rule | Value | Status |
|---|---|---|
| Action menu | Fixed menu of 12 actions | Confirmed from the brief |
| Max rounds per task | 3 | Confirmed from the brief |
| Round limit reason | ROUND_LIMIT, escalates to human | Confirmed from the brief |
| Approval timeout | 120 s | Estimated |
| DeepSeek timeout | 30 s per call, retry once | Estimated |
| Bocha timeout | 15 s, return error, do not block the task | Estimated |
| Tool timeout | 60 s max for shell_run and run_python, kill the process, log TOOL_TIMEOUT | Estimated |
| Stuck task | Working for more than 300 s becomes blocked with reason STUCK, watchdog runs every 30 s | Estimated |
| Claim TTL | 300 s | Estimated |
| Heartbeat | 60 s | Estimated |
| Rate limit | 10 per min | Estimated |
| Research max | 20000 chars | Estimated |
| Report max | 5000 chars | Estimated |
| Token revoke | After 3 bad tries, for 10 min | Estimated |

### 6.3 Tools

14 tools with schemas, per-role permissions. Tools are tagged SAFE or NEEDS APPROVAL. The full list is in ARCHITECTURE.md. Key tools: rules engine, make_slides, web search, vault write, portfolio read. The rules engine computes the sector ranking from price only. The LLM writes the explanation. The code computes the numbers. Never let an LLM compute the ranking.

### 6.4 Approval gate

| Rule | Fact |
|---|---|
| Who approves | Only a physical green button press. Voice cannot approve. A model cannot approve. |
| One press | Approves one task only. Never approves all queued tasks. |
| Approval record | Bridge sets approved_by to human, sets approved_at, sets status to working for execution. |
| Reject | Red press marks the task blocked, risk_reason is HUMAN_REJECT. The portfolio does not change. |
| Risk block | If risk_check fails, a green press does nothing. The screen shows RISK BLOCKED plus the reason code. |
| Expiry | No press in 120 s means the approval expires. The task stays queued. The green LED turns off. The screen shows APPROVAL EXPIRED. Estimated. |
| Gap | The NEEDS APPROVAL pause in coordinator.py is a skeleton. It logs the pause, it does not yet wait for the bridge. The code worker must wire it to wait on the bridge approval state. See open question Q15. |

### 6.5 GUARD role

GUARD enforces hard rules and approval gates, as code, not as LLM. GUARD checks the tool, the kill state, the approval state, and the risk check. It cannot be talked out of a block. GUARD is one of the 4 agent roles. See section 7.

### 6.6 Kill switch, software side

| Rule | Fact |
|---|---|
| Freeze | Kill freezes all agents. All working tasks mark blocked, with a log line KILL_SWITCH. No new orders run. Voice output stops. |
| Reset | Turn the kill switch off, then press green once to resume. Never auto-resume. |
| Resume | The coordinator creates a new signal task. It does not resume an old half finished order. Old blocked tasks stay blocked. |
| Green while latched | Does nothing. |
| Freeze time | Agents freeze within 200 ms. Estimated. |
| State | Bridge sets kill active to true in state.json. |
| Gap | software_freeze has no state.json field in ARCHITECTURE.md. Add it. See open question Q16. |

### 6.7 Vault and task state

| Rule | Fact |
|---|---|
| Format | Obsidian-compatible vault of markdown task notes, strict YAML frontmatter, 20 fields. Status is queued, working, blocked, or done. |
| Links | depends_on uses wikilinks in the body. |
| Obsidian app | Does NOT run on Pi. Viewer on Jayden's laptop only. |
| Write rule | Temp file then rename. Write the full new file to task_id.md.tmp, flush, fsync, rename to task_id.md, fsync the folder if the OS allows it. |
| Bridge read rule | Ignore .tmp files. Ignore a file while it is being written. Check the file is stable for 200 ms before parsing. Keep a hash map of file path to last parsed hash. Skip the file if the hash did not change. |
| Conflict | Second writer must read the current file first, merge log lines, then write. Never overwrite a newer file with an older copy. On conflict, log VAULT_CONFLICT and keep the newer file. |
| State cache | state.json cache, vault wins on conflict. Bridge rebuilds state.json from the vault on restart. A task that was working at power loss is marked blocked on boot, with reason POWER_LOSS. The coordinator creates a new task. No order is executed twice, because execution checks approved_by and executed_at before filling. |
| Gap | Claim expiry leaves the task status as working. A second claim gets 409. Decide whether expiry resets the task to queued with CLAIM_EXPIRED. See open question Q14. |

### 6.8 Bridge external agent API

| Rule | Fact |
|---|---|
| Who can use it | External agents, Hermes first, home only. |
| Auth | Token-protected HTTP API. Token stored only in .env on the Pi and in Jayden's password manager. Never in a task note, never on screen. |
| Can do | Claim tasks, write reports, write research notes. Research and narration tasks only. |
| Can never do | Approve, execute, propose trades, edit code, touch GPIO, change a task status to done for a trade task. The bridge enforces this in code, not in a prompt. |
| Ports | 8000 dashboard, 8001 API. Estimated. |
| Claim TTL | 300 s. Heartbeat 60 s. Estimated. |

### 6.9 Voice

| Item | Fact |
|---|---|
| Input | Push-to-talk, GPIO23. Hold to record, release to transcribe. |
| STT first choice | SenseVoice Small. Size and RAM are unconfirmed on Pi 5 ARM64. Test first. |
| STT fallback | faster-whisper Base multilingual, fixed Chinese command vocabulary, not free speech. Whisper Base is 74M, about 142 MB, about 30 percent more accurate on clean speech than Tiny, unconfirmed. Whisper Tiny is 39M, about 75 MB, transcribes 10 s in about 2 to 3 s on Pi 5 8GB, confirmed from the previous blueprint. Whisper Small is 244M, about 466 MB, needs about 2 GB RAM, too slow for live commands, unconfirmed. Do not use Small for live commands. |
| TTS | Piper, en_US-lessac-medium.onnx and zh_CN-huayan-medium.onnx, each about 60 MB, more than 3x real time on Pi 5, confirmed from the previous blueprint. RAM about 150 to 180 MB during synthesis, unconfirmed. |
| Languages | English and Chinese. Prewritten bilingual sentences from strings.json. 15 sentence IDs, EN and ZH, drafted. Chinese translations are not verified by a native speaker. LLM picks a sentence id, never free text. |
| Voice rule | Voice proposes, never executes. Voice never approves. |
| Mic mute | Mic is muted during TTS playback. No echo transcript. |
| Gap | No text input field is designed. No keyboard is in the BOM. Text input is the stated fallback if voice fails. See open question Q32. |

### 6.10 RAM budget

| Item | RAM | Status |
|---|---|---|
| OS and desktop | 0.8 to 1.2 GB | Unconfirmed or estimated |
| Bridge | 0.2 to 0.4 GB | Unconfirmed or estimated |
| Coordinator | 0.2 to 0.4 GB | Unconfirmed or estimated |
| Dashboard Chromium kiosk | 0.5 to 1.0 GB | Unconfirmed or estimated |
| Mini screen view | 0.1 to 0.2 GB | Unconfirmed or estimated |
| Pandas and price CSV data | Under 0.1 GB | Unconfirmed or estimated |
| Whisper Tiny or Base, during a voice turn only | 0.2 to 0.7 GB | Unconfirmed or estimated |
| Piper TTS, during synthesis only | 0.15 to 0.18 GB | Unconfirmed or estimated |
| Local LLM | 0 GB in v1, dropped | Confirmed from the brief |
| Total normal run, no voice turn | About 1.9 to 3.3 GB | Estimated |
| Total during a voice turn | About 2.25 to 4.18 GB | Estimated |
| Rule | Free RAM stays above 1 GB at all times. If RAM use goes over 7 GB, the bridge logs RAM_HIGH and unloads voice models first. | Estimated |

### 6.11 Model router, both options

| Item | Option A: DeepSeek plus Claude Fable 5.2 tiers | Option B: DeepSeek only |
|---|---|---|
| Models | DeepSeek plus Claude Fable 5.2, in tiers | DeepSeek only |
| Owner | Christopher, software architecture, model router | Same |
| Cost | Fable 5.2 is 8 USD input and 40 USD output per 1M tokens, confirmed. That is about 27 times DeepSeek flash input and 33 times its output. | DeepSeek daily cost cap USD 5.0, estimated, in config |
| China access | Claude does not work from mainland China. Anthropic policy does not support use by persons physically in mainland China, Hong Kong, or Macau, confirmed. | DeepSeek works in China. Bocha works in China. |
| Fallback | Any router must fall back to DeepSeek only | N/A, DeepSeek only by design |
| Verdict on Claude Fable 5.2 | Fable 5.2 exists, but it is too expensive and it cannot be used at the Shenzhen booth. Router must fall back to DeepSeek only. | N/A |
| Status | Unresolved, team decides tomorrow | Jayden's stated position |

Model names, confirmed on DeepSeek official docs 2026-11-23: current models are deepseek-flash (V4.1-Flash-1017) and deepseek-v4-pro (V4-Pro-0813). Both have 1M context and 384K max output. deepseek-chat and deepseek-reasoner are retired. deepseek-v4-flash is retired and only routes to V4.1 Flash. Pin deepseek-flash in config.yaml at build time. Run a live tool call test with the pinned model. Code takes the model from .env and fails loudly if missing. Never hardcode deepseek-chat. Never use a reasoner model as coordinator. See open question Q1.

Bocha domains: api.bochaai.com and api.bocha.cn. The conflict is confirmed from search results. Put the base URL in config. Test both domains from Canada before travel, test again in Shenzhen, use the one that answers. If both fail, search is off and the agent says so on screen. See open question Q2.

## 7. Agent flow

### 7.1 Roles

| Role | LED | Job |
|---|---|---|
| COORD | GPIO5 | Coordinator. Picks actions from the fixed menu. Creates tasks. Routes work. |
| AGENT 1 | GPIO6 | Worker agent. Research, slides, analysis. |
| AGENT 2 | GPIO13 | Worker agent. Execution, portfolio updates. |
| GUARD | GPIO19 | Guard. Enforces hard rules and approval gates in code. Blocks bad tool calls, bad tickers, bad amounts, kill state, risk failures. |

The role names are COORD, AGENT 1, AGENT 2 and GUARD.

### 7.2 Task lifecycle

| Step | State | What happens |
|---|---|---|
| 1 | queued | Coordinator creates a task note in the vault. Frontmatter status is queued. |
| 2 | working | An agent claims the task. Claim TTL 300 s, heartbeat 60 s. Estimated. |
| 3 | working | Agent works. Max 3 rounds. One round is one DeepSeek call plus its tool executions. |
| 4 | working | If a tool needs approval, the task pauses. Green button glows. Screen shows APPROVE and REJECT. |
| 5a | working | Green press: approved_by is human, approved_at is set, status is working for execution. Execution fills at the replay close price, paper only. Portfolio updates. |
| 5b | blocked | Red press: status is blocked, risk_reason is HUMAN_REJECT. Portfolio does not change. Coordinator routes work back to signal for a new proposal. |
| 5c | blocked | No press in 120 s: approval expires. Task stays queued. Green LED turns off. Screen shows APPROVAL EXPIRED. Estimated. |
| 6 | done | Task completes. Status is done. Log lines record each step. |
| 6b | blocked | Task fails. Status is blocked, with a reason code. See table 7.3. |
| Kill | blocked | Kill switch latches. All working tasks mark blocked, log line KILL_SWITCH. No new orders run. |

### 7.3 Error codes

| Code | Meaning |
|---|---|
| BAD_JSON | Reply is not valid JSON. Counts a failed round. No tool runs. |
| BAD_ACTION | Action is not in the fixed menu. No tool runs. |
| BAD_SCHEMA | Tool arguments do not match the schema. No tool runs. |
| BAD_TICKER | Ticker is not in the allowed list. No tool runs. |
| BAD_AMOUNT | Amount is over the portfolio value. No tool runs. |
| BAD_DEPENDENCY | depends_on task is not done. |
| DUPLICATE_TASK | Task already exists. |
| GUARD_BLOCK | GUARD blocked the call in code. |
| ROUND_LIMIT | Task used 3 rounds. Escalates to human. |
| API_TIMEOUT | DeepSeek call timed out after 30 s, retry once, then blocked. |
| API_ERROR | DeepSeek call failed. |
| TOOL_TIMEOUT | Tool ran over 60 s. Process killed. Task blocked. |
| STUCK | Task in working for more than 300 s. Watchdog blocks it. Estimated. |
| ESCALATE | Task escalates to human. |
| HUMAN_REJECT | Red button pressed. |
| KILL_SWITCH | Kill switch latched. |
| VAULT_WRITE_FAIL | Vault write failed. Keep the old file. Set the task blocked. Retry once after 200 ms. |
| VAULT_CONFLICT | Two writers wrote the same note. Keep the newer file. |
| POWER_LOSS | Task was working at power loss. Marked blocked on boot. |
| CLAIM_EXPIRED | Proposed reason for claim expiry. Undecided. See open question Q14. |

Gap: INTEGRATION.md invents 12 codes with no ARCH source, for example CLAIM_CONFLICT, CLAIM_TOKEN_BAD, CLAIM_TYPE_DENY, RATE_LIMIT. Write one error code table in ARCHITECTURE.md and make INTEGRATION.md match it. See open question Q17.

Gap: a slide task is not a trade, so risk_check should be blank, but the worked example keeps risk_check pass for the slide task. Pick one rule for non-trade tasks, blank or pass. See open question Q18.

### 7.4 Worked example, 2022 bear market

From INTEGRATION.md. 5 DeepSeek calls. Replay date 2022-12-30, a Friday trading day, estimated. Portfolio start 100000 paper dollars, 100 percent cash, estimated.

| Step | What happens |
|---|---|
| 1 | Visitor holds push to talk, says: Research the 2022 bear market and make 3 slides. |
| 2 | Coordinator creates a task note. Mini screen shows COORD working, then AGENT 1 working. |
| 3 | Worker calls Bocha for research, if the network works. |
| 4 | Rules engine computes the sector ranking from price only, up to the replay date. No future data. |
| 5 | Worker makes 3 slides with python-pptx. Slides go to the vault, then to the main screen. |
| 6 | Proposal appears. Green button glows. Screen says APPROVE and REJECT. |
| 7 | Visitor presses green once. Execution fills at the replay close price, paper only. Portfolio updates. |
| 8 | Main screen shows the final score vs SPY, price only. Total return, SPY total return, excess return, max drawdown, number of trades. |

Scoring is price only for both the portfolio and SPY. Dividends are ignored. That understates SPY total return by about 1 to 2 percent per year, unconfirmed. Label it price only on screen.

How slides are shown on screen is undefined. make_slides writes a .pptx to the vault. Neither ARCHITECTURE.md nor INTEGRATION.md says how that file is shown on the main screen. Pick one method, for example convert to images and show in the dashboard, or open in LibreOffice, and test it on the Pi. See open question Q4.

## 8. Autumn reuse plan

Autumn is Jayden's FastAPI plus React dashboard, local-first.

### 8.1 Audit findings

| Finding | Fact |
|---|---|
| Backend | Portable, runs on Linux with no changes. Server smoke test passed. |
| Vault write-back | Passes 27 of 27 checks in test_vault_write.py. Atomic temp plus os.replace. |
| Brief claim check | The brief claim that Autumn Obsidian writes failed repeatedly could NOT be confirmed. |
| Test-first flag still stands | SI Console rewrites YAML frontmatter status. Autumn only flips a checkbox. The SI writer is new code. Test it first. |
| Chat lifecycle tests | 38 of 38 pass. |
| Briefing test | Pass. |
| Search test | Pass, after a realistic fixture. |
| Dashboard tests | 9 of 9 pass. |
| Vite build | Passes, 503 ms, 296 kB JS. |
| Not run | test_categorise, needs real mail. test_overview, live only, no API key. Palette browser test, needs Playwright. |
| Windows-only code | Confined to autostart, PowerShell, VBS, Edge UI Automation. All DROP. No win32 imports in Python. |
| Gaps | No tool calling anywhere. No approval gate, kill, GPIO, voice, or DeepSeek code. No YAML frontmatter parser. No vault watcher. |
| Groq models | Groq Llama models are dead. Light tier is now openai/gpt-oss-120b. |
| requirements.txt | Was fully unpinned. Versions were pinned during the salvage. |

### 8.2 What to salvage

| Autumn part | Use in SI Console |
|---|---|
| Model tiering | Rewire to DeepSeek. See section 6.11. |
| Chat orchestrator | Base for the coordinator loop. |
| TF-IDF search with citations | Base for research notes and slide sources. |
| APScheduler | Base for the coordinator watchdog and claim expiry. |
| Ctrl+K palette | Dashboard shortcut pattern. |
| React dashboard | Base for the main screen dashboard. |
| Atomic vault writer pattern | Base for the SI vault writer, plus YAML frontmatter rewrite. |

### 8.3 What to skip

| Autumn part | Why skip |
|---|---|
| Gmail and OAuth | Not needed on the Pi. |
| Windows autostart | Pi uses systemd. |

### 8.4 Code salvage gaps, from CODE_NOTES.md

| Gap | Fact |
|---|---|
| NEEDS APPROVAL pause | Skeleton only. Logs the pause, does not wait for the bridge. See open question Q15. |
| Claim expiry | Leaves the task status as working. A second claim gets 409. See open question Q14. |
| Message history | Skeleton. Results are logged, not re-sent. |
| search.py | No dedicated test. |
| STT and TTS | Not installed. |
| Bridge /docs | Left on by default. Disable in the booth build. |
| DeepSeek cost cap | Daily cap USD 5.0, estimated, added in config. Closes part of the cost gap. Bocha cost cap still open. See open question Q13. |
| DeepSeek model | Taken from .env, fails loudly if missing. Never hardcodes deepseek-chat. |
| GPIO map | The code maps COORD to GPIO5 in gpio_map.py. The GPIO map tests pass. See section 3.4. |
| Early tests | 37 passed on 2026-11-20, Python 3.12.3, fresh venv. Bridge smoke test passed: health 200, no token 401, bad token 401, 10 API routes. make_slides wrote a 2-slide deck. Rules engine with no price files returned Hold cash. |

## 9. Build plan

Build deadline Tue Dec 8, 2026. Booth Sat Dec 12 to Sun Dec 13, 2026. All dates are 2026, America/Vancouver time.

Order of work: design and CAD, submit, approval, order, build. Fallen funds parts only after design approval. Confirmed from the brief.

### 9.1 Staged build

| Stage | Work | Pass test |
|---|---|---|
| Stage 0, measure and mockup | Measure every real part with calipers when it arrives. Before that, measure from datasheets only. Make a cardboard mockup at full size. Put the buttons in it. Press them. Test button spacing. Test mini screen readability at 800x480. Draw the lid on paper at 100 percent scale. Lay it on the real lid or the mockup. Check holes line up. | A hand can press green and red without hitting the other button. Mini screen text is readable from a seated position. The cardboard box closes without parts poking through. No hole is drilled yet. |
| Stage 1, Pi and screens | Flash Raspberry Pi OS Trixie on the 128GB microSD. Use a venv for Python. Pin versions in requirements.txt. Boot the Pi 5 with the official 27W PSU and the active cooler. Plug in both screens before power on. Main screen to HDMI0, closest to USB-C power. Mini screen to HDMI1. Set the layout in Screen Configuration. Test Chinese font rendering. Install the bridge skeleton, the dashboard, and the vault watcher. Do not wire buttons yet. | Pi boots cleanly 5 times in a row. Both screens show at the right resolution. Main screen shows the dashboard. Mini screen shows the agent chain, 4 rows, large text. Chinese text renders, not boxes. vcgencmd get_throttled returns 0x0 after 10 minutes with both screens on. |
| Stage 2, breadboard buttons and LEDs | Build on a solderless breadboard, MB-102 830-point. Wire green GPIO17, red GPIO27, push to talk GPIO23, toggle GPIO24, all active low with internal pull-up. Wire the 4 status LEDs direct from GPIO first, for testing only, with the same resistors as the final build (green 150 ohm, white 100 ohm, blue 100 ohm, yellow 220 ohm) at 3.3V. That direct wiring is dimmer. It is a test only, not the final wiring. Run a gpiozero test script. Press each button 100 times. | Each button press prints once. No double press in 100 presses. Each LED turns on and off on command. Toggle flips EN to ZH and back, and the screen language changes. Debounce is 0.05 s. If one press creates two executions, raise debounce to 0.1 s and retest. |
| Stage 3, kill switch and ULN2003 | Highest risk stage. Do it before soldering anything else. Bench test the ULN2003 at 3.3V before soldering. Test every channel. Measure LED current with a multimeter. Bench measure the green Vf first. Pass if 5 to 20 mA per LED. If a channel is dim or the chip is warm, stop. Use the fallback: TBD62083A, probably 3.3V friendly, or a logic level MOSFET per LED. Wire the kill switch next. Kill is GPIO22 pin 15, NC. Closed reads LOW, normal. Open reads HIGH, frozen. Test with a multimeter before trusting code. Poll GPIO22 every 100 ms. Wire the ULN2003 per section 3. Pin 8 to GND. Pin 9 COM to 5V. | All 6 LEDs light at 5 to 20 mA, measured, with the green Vf recorded. Kill pressed and latched reads HIGH and freezes all agents within 200 ms, estimated. Kill released still stays frozen until green is pressed once. Green press while kill is still latched does nothing. All 4 agent LEDs go off on kill, plus the kill pattern on screen. No channel is warm to the touch after 10 minutes on. |
| Stage 4, solder | Move the breadboard circuit to perfboard. Solder the 4 status LED resistors in a row. Solder LED anode wires to resistors, cathode wires to the ground rail. Solder the ULN2003 socket, not the chip directly, so a dead chip can be swapped. Keep button wires under 30 cm. Twist GPIO and ground together per button. Keep LED wires under 20 cm. Label every wire. | Continuity test with a multimeter on every wire before first power on. No short between 5V and GND. No short between any GPIO pin and 5V. Each LED lights on command after soldering. Each button still prints once in 100 presses. |
| Stage 5, case, laser cutting | Finish CAD first. Every acrylic panel flat with dimensions in mm, finger joints, hole sizes with clearance. Send clean DXF or SVG files to MakerLabs fabrication service. Or use MakerLabs drop-in LaserLab at 2 CAD per min, if the age rule allows. Do not use FabLab Vancouver for a single case. Minimum commitment is 320 CAD plus tax for two months. Do not use Vancouver Hack Space. It requires age 19 plus. Jayden is 18. That is unconfirmed. | All 6 panels fit together with finger joints, no force needed, no gap over 0.5 mm. Every button, switch, and LED fits its hole. The mini screen fits its bezel cutout. The Pi, perfboard, and speaker fit inside with clearance. No panel is cracked. |
| Stage 6, mount and heat test | Mount the Pi on M2.5 standoffs, 10 mm high. Mount the perfboard on M3 screws. Mount the speaker front right inside, behind the front face, at least 20 mm from the Pi. Do not mount the mic inside the box. Route the USB-C power cable through a cable gland or a panel mount socket on the rear wall. Route two micro HDMI cables out the rear wall. Keep the Pi USB and Ethernet edge facing the rear wall. Leave 25 mm clear above the Pi for the active cooler and for air. Take a photo of the inside before closing it for the last time. | Close the box, run for 2 hours lid closed, with both screens on, speaker at 50 percent, fan on. Log temperature with vcgencmd measure_temp. If temperature stays above 75C for 5 minutes, fail, add vents or a case fan. Check vcgencmd get_throttled. It must be 0x0. Run the full 2020 replay and the full 2022 replay end to end, with no crash. Run 100 button presses, green and red, with no double execution. Run 100 vault writes, with no lost status change. |

Stage 3 gate: do not go to Stage 4 until Stage 3 passes, or until the fallback is formally chosen and recorded in LOG.md.

ULN2003 stock note, corrected: the old claim that DigiKey is out of stock with a 12 week lead is wrong. DigiKey TI ULN2003AN shows InStock at 1.79 CAD, confirmed. The page body also lists a 26 week manufacturer lead time. Confirm quantity at checkout. Order 3 for spares.

Safety: safety glasses on. Soldering iron 60W adjustable. Borrow first. Do not solder with the Pi powered on.

### 9.2 Timeline

| Dates | Work | Gate |
|---|---|---|
| Fri Nov 20 | Design day 1. Research, blueprints, ARCHITECTURE.md, INTEGRATION.md, BOM.csv, LASER_AND_TOOLS.md, BUILD_PLAN.md, TEST_PLAN.md, DEMO_SCRIPT.md, OPEN_QUESTIONS.md, MORNING_SUMMARY.md. | Research done. |
| Sat Nov 21 to Sun Nov 22 | Design days 2 to 3. Budget and monitor decisions. Start CAD. Draw all 6 acrylic panels. Cardboard mockup. Test button spacing. Start the starter firmware skeleton. | Cardboard mockup passes Stage 0. CAD draft is complete enough to send for a quote. |
| Mon Nov 23 to Tue Nov 24 | Submit the Fallen design package. Ask Fallen the grant cap, approval time, self-funded parts, AI-assisted code with disclosure, team size. See section 13.4. Send the CAD files to MakerLabs for a quote in parallel. Do not wait for Fallen approval to get a laser quote. | Submission sent. MakerLabs quote in hand. Laser cost known, 50 to 90 CAD estimated. |
| Wed Nov 25 to Fri Nov 27 | Approval window, estimated 2 to 4 business days. If approval comes early, move the order up. If approval is late, do not order the Pi on a guess. Wait for approval. Use the wait to finish the firmware skeleton and the voice test plan. If approval has not come by Fri Nov 27, email Fallen once to ask for a status update. | Fallen approval received, or a clear no-go date is set. |
| Mon Nov 30 | Parts arrival target. Order the PiShop.ca parts in one order on approval: Pi 5 8GB, PSU, cooler, microSD, mini screen. Order buttons, kill switch, LEDs, perfboard, wires, breakout, acrylic, cables, mic, speaker, travel adapter. Recheck every estimated price at checkout before paying. If the spare card cut is not taken, clone the microSD as soon as the first card is flashed and keep the spare card in carry-on. If the cut is taken, back up the image to a laptop instead. | All parts are in hand, or a missing part has a named fallback and a new arrival date. |
| Tue Dec 1 to Wed Dec 2 | Stages 1 to 3. Tue Dec 1: Stage 1, Pi and screens. Stage 2, breadboard buttons and LEDs. Wed Dec 2: Stage 3, kill switch and ULN2003. Run the GPIO test script. Run the vault write test. Run the STT test in English and Chinese, with a fan on and crowd noise. | Stages 1 to 3 pass. If the ULN2003 has not arrived, use the Stage 3 fallback and record it in LOG.md. |
| Wed Dec 2 | Laser cut case arrives. Mon Nov 30 to Wed Dec 2 window for a Mon Nov 23 submission. If the files slip, use MakerLabs drop-in. | Case panels are in hand. |
| Thu Dec 3 to Fri Dec 4 | Stages 4 to 5. Thu Dec 3: Stage 4, solder. Fri Dec 4: Stage 5, assemble the panels. Test fit every part. | Case fits, all holes fit, no panel cracked. |
| Sat Dec 5 to Sun Dec 6 | Stage 6 and stress test. Sat Dec 5: Stage 6, mount. Run the 100-round stress test. Run the Wi-Fi off booth test. The 2 hour lid closed heat test runs early, in Stage 2, not Dec 5. Sun Dec 6: fix failures. | Heat test passed in Stage 2, throttled is 0x0, stress test passes, Wi-Fi off booth test passes. |
| Mon Dec 7 to Tue Dec 8 | Fix, label, pack. Mon Dec 7: fix, label every wire and every button, take a photo of the inside before closing it for the last time. Run the demo script twice, once in English, once in Chinese. Run the recorded fallback path once, with Wi-Fi off and DeepSeek blocked. Tue Dec 8: build deadline. Pack for travel. Pack spare microSD, cables, LEDs, resistors, buttons, and two travel adapters in carry-on. Test on 220V in Shenzhen at least one day before the booth, with the Type I adapter. The Pi PSU takes 100 to 240V, so no voltage converter is needed, only a plug adapter. | Demo runs end to end twice, fallback runs once, pack list is checked. |

Laser timing warning: MakerLabs full service is 5 to 7 business days. Files sent Fri Nov 27 finish Dec 7 to 9, too late for Dec 8. Files must go Mon Nov 23, before Fallen approval, or use drop-in if the age rule allows. A Mon Nov 23 submission at 5 to 7 business days finishes Mon Nov 30 to Wed Dec 2. That fits.

Fri Dec 4 is also the Hack Club Harvest deadline, 11:59pm EST, for RAINBOUND PROTOCOL. That is a separate project. Do not let it eat the SI Console build day. Plan around it.

### 9.3 Cut order if the grant cap is low

| Cut first | Saves CAD | Never cut |
|---|---|---|
| Voice | 120.97 | Buttons, LEDs, kill switch, agents |
| Mini screen | 83.94 | Buttons, LEDs, kill switch, agents |

Core after the voice and mini screen cuts: 646.22 CAD before tax, 723.77 CAD with tax. The voice cut of 120.97 CAD includes the soundbar at 25.99 CAD. The lit-button cut no longer exists. The ULN2003 stays in the design. That still misses the 400 CAD target by 246.22 CAD before tax.

If a stage fails twice, cut the feature in the cut order above. If the core still fails, stop and ask Jayden. He is the decision maker for a scope cut.

## 10. Test plan

Run tests in order: T1 to T4 first, then T5 to T8, then T9 to T11, then T12 stress test, then T13 Wi-Fi off test. Each test has a pass test and a fail test. A fail means stop and fix the cause. Do not lower the pass test to make it pass. Fix the bridge, not the test. Log every result with date, test id, result, and numbers. Keep the log in the vault log folder, one file per day, named YYYY-MM-DD.md. Full test text is in TEST_PLAN.md.

| Test | Purpose | Pass test |
|---|---|---|
| T1 RAM | Prove the full stack fits in 8GB, with at least 1GB free at all times | Free RAM stays above 1GB at all times. Total used stays under 7GB at all times. No process grows without bound over 30 minutes. |
| T2 STT accuracy, EN and ZH, with noise | Prove voice works in a loud booth, in both languages, or prove it does not and cut it | Clean English: word error rate under 10 percent, intent matched on at least 9 of 10 turns. Noisy English: word error rate under 20 percent, intent matched on at least 8 of 10 turns. Clean Chinese: character error rate under 20 percent, intent matched on at least 9 of 10 turns. Noisy Chinese: character error rate under 30 percent, intent matched on at least 8 of 10 turns. Latency: a 5 second clip transcribes in under 5 seconds on average. All targets are estimates. |
| T3 Vault write reliability | Prove task notes never lose a status change | 100 of 100 writes read back correctly, no lost status change, no half written file, no .tmp file left behind, no lost log line. Bridge restart rebuilds state.json correctly 5 of 5 times. Concurrent writes produce VAULT_CONFLICT or a clean merge, never a lost update. |
| T4 Power | Prove the Pi never brownouts, with both screens, mic, and speaker on | get_throttled is 0x0 in every step. No reboot on monitor plug or unplug. No microSD corruption in 5 power cycles. No undervoltage lines in dmesg. T4 in TEST_PLAN.md now lists the Rev R2.1 budget, updated 2026-11-23. |
| T5 GPIO, buttons, LEDs, kill, toggle | Prove every physical control works, 100 times, with no double execution | 100 presses, no double execution. Kill freezes 20 of 20 times. Resume needs green once, 20 of 20 times. Green press while kill is latched does nothing, 20 of 20 times. LED currents are 5 to 20 mA, Vf measured first. Toggle flips language 20 of 20 times. |
| T6 Heat, 2 hours lid closed | Prove the closed acrylic case does not throttle the Pi | Temperature stays under 75C for the full 2 hours, except for brief spikes under 5 minutes. get_throttled stays 0x0. |
| T7 Coordinator loop | Prove the fixed action menu, the 3 round limit, and the approval gate work in code | All 10 checks pass. No tool runs on a rejected reply. No task is approved without a green press. No task runs a fourth round. Approval expires at 120 seconds. |
| T8 DeepSeek and Bocha, home and booth | Prove the brain and the search work, and prove the fallback works when they do not | DeepSeek tool call works in Canada. At least one Bocha domain answers in Canada. Wi-Fi off switches to recorded runs with no crash. DeepSeek blocked switches to recorded runs with no crash. |
| T9 Replay data | Prove the 2020 and 2022 replays use only data up to the replay date, never future data | Max date used is never after the replay date. Both replays finish with no crash. Two runs with the same inputs give identical results. |
| T10 External agent API | Prove Hermes can claim tasks and write reports, but can never approve, execute, propose trades, or edit code | Claim plus research note succeeds with a valid token. Approve, execute, propose trade, and edit code all fail with a valid token. Every call fails with an invalid token or no token. Double claim fails. |
| T11 Screens and language | Prove both screens show the right thing, in English and Chinese, with no boxes for Chinese characters | Both screens show the right content. Toggle flips language 20 of 20 times. Voice switch works. No Chinese character shows as a box. No English string is hard coded in dashboard code. |
| T12 100-round stress | Prove the console survives a full booth day of use, lid closed, both screens on, speaker at 50 percent, fan on | 100 rounds finish with no crash. No double execution in 100 presses. No lost status change in 100 vault writes. No order after kill in 20 kill cycles. 10 reboots rebuild state correctly, 10 of 10. get_throttled stays 0x0. Temperature stays under 75C, except for brief spikes under 5 minutes. |
| T13 Wi-Fi off booth | Prove the booth demo works with no internet, in Canada, before travel to Shenzhen | Full booth demo runs with Wi-Fi off, in both scenarios, with no crash, no hang over 30 seconds, and no step that needs the network. Voice works offline. Recorded fallback starts automatically. |

Test order and sign-off: run T1 to T4 on Dec 1. Run T5 to T8 on Dec 2. Run T9 to T11 on Dec 3. Run T12 and T13 on Dec 5 to Dec 6. Fix failures on Dec 6 to Dec 7. Do not sign off until T12 and T13 pass.

Sign-off checklist, all must be yes: T1 RAM passes. T2 STT passes, or voice is cut and text input works. T3 vault writes pass, 100 of 100. T4 power passes, get_throttled is 0x0. T5 GPIO passes, 100 presses, no double execution. T6 heat passes, 2 hours lid closed. T7 coordinator passes, 3 round limit, approval gate. T8 DeepSeek and Bocha pass, or fallback is proven. T9 replay passes, no lookahead. T10 external API passes, forbidden calls fail. T11 screens pass, Chinese renders. T12 stress passes, 100 rounds. T13 Wi-Fi off passes, booth demo runs. If any item is no, the build is not ready for Shenzhen. Record the no in LOG.md, with the test id, the numbers, and the fix.

## 11. Demo plan

Demo length 3 to 5 minutes. Target 4 minutes. Do not run long. A booth visitor gives you 4 minutes, not 10. Full script is in DEMO_SCRIPT.md.

### 11.1 Before the demo starts

Checklist, run every morning before the booth opens: Pi boots cleanly. Both screens show. Main screen shows the dashboard. Mini screen shows the agent chain, 4 rows, large text. vcgencmd get_throttled returns 0x0. If it is not 0x0, stop and fix power. Speaker volume is capped at 50 percent. Mic is plugged in. Push to talk works. Kill switch is off. Green button LED is off. No proposal is pending. Replay data is on the microSD card. Recorded agent runs are on the card, for the fallback path. Language is set to English to start. Toggle GPIO24 flips to Chinese on request. Portfolio starts at 100000 paper dollars, 100 percent cash, for both scenarios. That is estimated. Spare microSD if the cut is not taken, cables, LEDs, resistors, buttons, and two travel adapters are in carry-on. The console has no lithium battery inside. If any check fails, fix it before the first visitor. Do not demo a broken console.

### 11.2 Demo in English, 4 minutes, live path

| Time | What happens |
|---|---|
| 0:00 to 0:30, hook and start screen | Say: Hi, this is SI Console. Talk to dispatch, press to approve. I talk to a team of AI agents. I press a button to approve. Nothing runs without my press. Point to the start screen. It says CHOOSE SCENARIO, with 2020 and 2022. Say: Pick a crash. Green picks 2020. Red picks 2022. Ask the visitor which one they want to see. Press green for 2020, or red for 2022, as the visitor chooses. This is the only time red does not mean reject. The screen must label the buttons in large text. The screen shows the scenario start date, the start cash 100000 paper dollars, and the start holdings, 100 percent cash. Mini screen shows the agent chain: COORD, AGENT 1, AGENT 2, GUARD. All queued to start. |
| 0:30 to 1:30, voice propose | Hold the push to talk button. Say: Research the 2022 bear market and make 3 slides. Release the button. The screen shows RECORDING, then the transcript. The system speaks a short confirmation with Piper TTS, in English. The mic is muted during playback. Voice proposes only. Voice never executes. The coordinator creates a task note. The mini screen shows COORD working, then AGENT 1 working. The main screen shows the proposal forming. The worker agent calls Bocha for research, if the network works. The rules engine computes the sector ranking from price only, up to the replay date. It never uses future data. The LLM writes the explanation. The code computes the numbers. The worker makes 3 slides with python-pptx. The slides go to the vault, then to the main screen. Say, while it runs: The agents are researching. The numbers come from code, not from the model. The model writes the words. |
| 1:30 to 2:30, approval pause | The proposal appears on the main screen. The green button glows. The screen says APPROVE with green, REJECT with red, in English and Chinese. Say: Now it waits for me. The agents proposed, but nothing runs until I press green. This is the hand on the brake. Point to the green button LED. Point to the GUARD LED. Say: GUARD is code, not a model. It checks the tool, the kill state, the approval state, and the risk check. It cannot be talked out of a block. Ask the visitor: Approve or reject. If the visitor says approve, press green once. One press approves one task only. The bridge sets approved_by to human, sets approved_at, sets status to working for execution. The green LED turns off. The execution agent fills at the replay close price, in paper only. The portfolio updates. The mini screen shows EXEC working, then done. If the visitor says reject, press red once. The task marks blocked, risk_reason is HUMAN_REJECT. The portfolio does not change. The coordinator routes work back to signal for a new proposal. Say, after the press: That press was the only execution path. Voice cannot do it. The model cannot do it. Only this button can. Show the slides on the main screen. Flip through the 3 slides. Each slide has a source line. |
| 2:30 to 3:30, kill switch demo | Say: Now the safety test. This red mushroom is the kill switch. It freezes all agents. Press the kill switch and latch it. The bridge sets kill active to true in state.json. All working tasks mark blocked, with a log line KILL_SWITCH. No new orders run. Voice output stops. All 4 agent LEDs go off, plus the kill pattern. Both screens show KILL ACTIVE, in English and Chinese. Say: It is wired normally closed. A broken wire also reads frozen. That is fail safe. Release the kill switch. Twist or pull to release it. The console stays frozen. The screens say KILL ACTIVE, plus PRESS GREEN TO RESUME. Say: It does not auto resume. I have to press green once. Press green once. The console resumes. The coordinator creates a new signal task. It does not resume an old half finished order. Old blocked tasks stay blocked. Show the final score vs SPY on the main screen, price only, in large text. Show total return, SPY total return, excess return, max drawdown, number of trades. Say: Price only, no dividends, so SPY is understated by about 1 to 2 percent per year, unconfirmed. That is stated on screen. |
| 3:30 to 4:00, close | Say: That is SI Console. Talk to dispatch, press to approve. Trading is one skill, not the whole product. The same console can research, write slides, and run any agent team, with the same green button as the gate. Ask: Do you want to try it. Let the visitor press green or red on the next proposal. Do not let a visitor press kill without warning them first. Reset to the start screen for the next visitor. The start screen shows CHOOSE SCENARIO again. |

### 11.3 Demo in Chinese, 4 minutes, live path

Same demo, in Chinese. Same time marks. Flip the GPIO24 toggle to ZH, or say the voice command to switch language. The screens, the TTS, and the proposal all switch to Chinese. Full Chinese script is in DEMO_SCRIPT.md section 2. The Chinese sentences are translations of the English script, not verified by a native speaker. Have a Chinese speaker check the cue card before the booth. Say the Chinese sentences in characters, not in pinyin, at the booth. The pinyin in the script is only a reading aid.

### 11.4 Hard questions

| Question | Answer |
|---|---|
| Does the AI make the trade. | No. The rules engine computes the ranking from price only. The model writes the explanation. The green button approves. No button, no trade. |
| What if the model is wrong. | GUARD blocks it in code. Risk blocks it with a reason code. I block it with the red button. Kill freezes it all. |
| What if the internet fails in Shenzhen. | The console switches to recorded agent runs automatically. The demo continues on replay data. No live price feed is needed. |
| Can voice approve. | No. Voice proposes only. Voice never executes. Voice never approves. That is a hard rule. |
| Is this real money. | No. Paper money only. 100000 paper dollars. No real money is connected. |
| How much did it cost. | Fundable parts and API credits 885.81 CAD before tax, 992.11 CAD with tax. Self-funded monitor, power brick, and travel adapter 128.24 CAD before tax, 143.63 CAD with tax. All-in with tax 1135.74 CAD, before shipping and laser cutting. Laser cutting is 50 to 90 CAD extra. Shipping is estimated 40 to 60 CAD extra. |
| What is the hardest part. | Voice in a loud hall, and heat in a closed case. Both are tested. See TEST_PLAN.md T2 and T6. If voice fails, buttons and text still work. |

### 11.5 Recorded fallback path, when internet or DeepSeek fails

Booth mode uses live DeepSeek by default, with recorded agent runs as the automatic offline fallback when internet or the API fails.

| Item | Fact |
|---|---|
| Trigger | DeepSeek API timeout is 30 seconds per call, estimated. On timeout, retry once, then mark the task blocked with reason API_TIMEOUT, and switch to recorded fallback in booth mode. Do not retry forever. Bocha timeout is 15 seconds, estimated. On timeout, return an error, do not block the task, and continue without search results. |
| What the visitor sees | The screen says LIVE MODE OFF, RECORDED RUN, in English and Chinese. The mini screen keeps showing the agent chain. The demo continues. No crash. No hang over 30 seconds. |
| What changes | 0:00 to 0:30, same. 0:30 to 1:30, voice propose, same. Say: The network is off, so this run uses a recorded agent run. The numbers are the same as a live run for this replay date. The slides are pre-made from the recorded run. 1:30 to 2:30, approval pause, same. The proposal is from the recorded run, not from a live DeepSeek call. The green button still approves. The red button still rejects. The approval pause is real, even in fallback mode. Do not skip it. 2:30 to 3:30, kill switch demo, same. Kill works offline. It is hardware and bridge code, not a cloud call. 3:30 to 4:00, close, same. Say: This was the recorded path. With the network on, the same console runs live DeepSeek. The buttons and the kill switch work the same in both paths. |
| Practice | Turn off Wi-Fi on the Pi. Turn off the phone hotspot. Unplug Ethernet. Run the full demo, start to finish, in 2020 mode, then in 2022 mode. See TEST_PLAN.md T13. Practice it at least twice before Shenzhen. If the fallback does not start automatically, do not go to Shenzhen with that build. Fix it first. |
| What must be on the card | Replay CSV files for SPY and the 11 sector ETFs, 2019 to 2023. Recorded agent runs for both scenarios, with task notes, research notes, and 3 slides each. Piper TTS voices, en_US-lessac-medium.onnx and zh_CN-huayan-medium.onnx. STT model, SenseVoice Small or faster-whisper Base, whichever passed T2. All models downloaded at home, before travel. No download at the booth. |
| Gap | The recorded fallback format is undefined. No format is defined, no file exists, no code exists. See open question Q3. |

### 11.6 Timing and reset between visitors

Target 4 minutes per visitor. If a visitor stays longer, let them try one more proposal, then reset. Do not run a 10 minute demo for one visitor while a queue forms.

Reset steps, 30 seconds: press red to reject any pending proposal, or let it expire after 120 seconds, estimated. The task stays queued, the green LED turns off. Press kill, then release it, then press green once to resume, to prove the console is clean. Or restart the coordinator task only, not the whole Pi. Return to the start screen. CHOOSE SCENARIO, 2020 or 2022. Language back to English, unless the next visitor asks for Chinese. Check get_throttled is 0x0. Check temperature is under 75C. If it is over 75C for 5 minutes, open a vent or add a case fan.

Do: let the visitor press green or red. Show the approval pause clearly. Demo the kill switch every time. Show the final score vs SPY, price only, in large text. Speak in short sentences. Reset to the start screen between visitors.

Do not: let a visitor press kill without warning them first. Run the demo with the lid open as a fix for heat, unless it is recorded as a booth fallback and the electronics are protected from touch. Let voice approve, even if a visitor asks for it. Show a score that mixes price only portfolio returns with total return SPY returns. Use price only for both and label it price only. Claim the demo uses live prices in booth mode. Booth mode uses replay data. Run the demo if get_throttled is not 0x0. Fix power first.

## 12. Risks

| Risk | Impact | Fix or mitigation | Status |
|---|---|---|---|
| Laser timing | Files sent Fri Nov 27 finish Dec 7 to 9, too late for Dec 8 | Send files Mon Nov 23, before Fallen approval, or use drop-in if the age rule allows | Open. See Q21. |
| Grant cap unknown | Fundable total 885.81 CAD before tax is over the 400 CAD target by 485.81 CAD, and over the 800 CAD team limit by 85.81 CAD | Ask Fallen the cap at submission. Apply the cut order: voice first, then mini screen, which gives 646.22 CAD before tax. | Open. See Q22. |
| Shenzhen offline demo | No internet kills the live demo. Recorded fallback format is undefined. No file exists, no code exists. | Define the recorded run format, record at least one full run at home with live DeepSeek, store it on the microSD, test the automatic switch with Wi-Fi off. | Open. See Q3. |
| Voice in a loud booth | Chinese STT is weakest. SenseVoice Small is unconfirmed on Pi 5 ARM64. Whisper Base Chinese CER 15.99 percent is clean speech only, unconfirmed. | Test STT on Dec 2, with noise. If it fails, cut voice from the booth demo and run on buttons and text only. Text input must exist in v1. | Open. See Q10, Q32. |
| Power, heat, ULN2003 together | Old USB headroom was 0.10A. Acrylic insulates. ULN2003 at 3.3V is test first, not guaranteed. | Rev R2.1 fixes the power headroom: about 1.0A, estimated, with the mini screen and monitor on their own chargers. Case fan added. Bench test the ULN2003 at 3.3V before soldering. Heat test T6 decides. | Partly fixed. USB currents still estimates until measured. |
| Fallen approval time unknown | Estimated 2 to 4 business days, never verified. If it is 7 days or more, the order slips past Nov 30, and the build slips past Dec 8. | Submit on Mon Nov 23. Ask for the approval time in the submission. Use the wait to finish CAD and firmware. | Open. See Q21. |
| ULN2003 stock | Old claim said DigiKey out of stock, 12 week lead. That claim was wrong. | DigiKey shows InStock at 1.79 CAD, confirmed. Page body also lists a 26 week manufacturer lead time. Confirm quantity at checkout. Order 3 for spares. | Mostly fixed. Confirm at checkout. |
| Pi 5 price and stock | 249.50 CAD confirmed on Nov 20. Prices surged in late 2026 due to a RAM shortage, per the previous blueprint. | Order the Pi first on approval, in one PiShop.ca order with the PSU, cooler, microSD, and mini screen. | Open. |
| Dec 4 collision | Harvest deadline for RAINBOUND PROTOCOL is Dec 4, 11:59pm EST. It collides with the solder and case days Dec 3 to 4. | Finish the Harvest submission before Dec 3, or move the SI Console solder day to Dec 2 if Harvest runs long. | Open. |
| Shipping not in budget | Estimated 40 to 60 CAD across retailers. | Order from as few retailers as possible. Use BC store pickup for the monitor. | Open. |
| Kill switch depth | APEM depth 78.3 mm vs 75 mm clearance, 3.3 mm over. | Check in the CAD redraw. See Q34. | Open. |
| Heat in a closed acrylic case | Acrylic insulates more than a vented ABS box. Vents are 1440 mm2, estimated. | Vents low and high, case fan added in Rev R2.1. Run the 2 hour lid closed heat test early, in Stage 2, not Dec 5. See Q30. | Open. |
| DeepSeek and Bocha in Shenzhen | Neither tested from China. DeepSeek model is unpinned. Bocha has two domains, neither tested. | Test both from Shenzhen on arrival day. Have the recorded fallback ready before the booth opens. See Q33. | Open. |
| Acrylic price | 32.99 CAD confirmed only by a 210-day-old crawl. | Re-check the price at order time. Confirm the sheet size covers the 360 by 240 mm panels. See Q24. | Open. |

## 13. Open questions

### 13.1 Three team decisions, team decides tomorrow

| Decision | Option A | Option B | Jayden's position |
|---|---|---|---|
| Case | Clear 3 mm laser-cut acrylic. Cost 52.98 CAD, unconfirmed. Laser 5 to 7 business days, unconfirmed. Electronics visible. | Black nylon factory print. About 125 to 145 CAD all in at JLCPCB, estimated. Arrives by Dec 1 only through JLCPCB with no slack. Needs a full redesign, 1 to 2 days. Electronics hidden. | Recommendation: keep acrylic. |
| Mini screen | 5 inch Waveshare HDMI (H), 800x480, 73.95 CAD, confirmed. Driver free per listing, but PiShop FAQ says a config.txt change is needed per wiki. Touch disabled. Uses an HDMI port. | No 5.5 inch Waveshare DSI exists. Real DSI option is the 5 inch Waveshare DSI LCD, SKU 18396, 800x480, about 73.94 CAD total with cable, unconfirmed. Ribbon, powered by the cable, no audio, frees HDMI1. Needs a config overlay, Rev2.2 only, and a top panel redraw. | Recommendation: keep HDMI. |
| Model router | DeepSeek plus Claude Fable 5.2 tiers. Fable 5.2 is real, 8 USD input and 40 USD output per 1M tokens, confirmed. Too expensive, and Anthropic policy does not support use from mainland China, confirmed. | DeepSeek only. Daily cost cap USD 5.0, estimated. | No Claude at the booth, because of cost and China access. Any router must fall back to DeepSeek only. |

Hardware research is done. The Claude Fable verdict is in, see the router row above.

### 13.2 Open questions Q1 to Q35

| ID | Question | What decides it |
|---|---|---|
| Q1 | DeepSeek model name at build time. Confirmed 2026-11-23 on DeepSeek official docs: current models are deepseek-flash and deepseek-v4-pro. deepseek-v4-flash is retired. | Pin deepseek-flash in config.yaml, run a live tool call test. |
| Q2 | Bocha base URL. api.bochaai.com vs api.bocha.cn. Conflict confirmed from search results. | Test both domains from Canada before travel, test again in Shenzhen, put the working one in config. |
| Q3 | Recorded fallback format. No format defined, no file exists, no code exists. | Decide the file format, record at least one full run at home with live DeepSeek, store it on the microSD, test the automatic switch with Wi-Fi off. |
| Q4 | How slides are shown on screen. make_slides writes a .pptx to the vault. No file says how it is shown. | Pick one method, for example convert to images and show in the dashboard, or open in LibreOffice, and test it on the Pi. |
| Q5 | Mini screen: separate process or one dashboard process. | Decide at build time, measure RAM both ways. |
| Q6 | STT confidence threshold. INTEGRATION.md used 0.6, estimated. No test supports it. | Test SenseVoice Small and faster-whisper Base on the Pi with clean and noisy speech, pick the threshold that gives 9 of 10 intent matches clean and 8 of 10 noisy. |
| Q7 | rules_engine and make_slides argument schemas are incomplete. | The code worker writes the full arg schema in tools.py and tests it against the rules engine. |
| Q8 | Scenario start date and holdings. Worked example uses replay_date 2022-12-30, estimated, and portfolio start 100000. The 2020 start date and start holdings for both scenarios are unset. | Jayden picks the start date and start holdings for 2020 and 2022. The code worker writes them in config.yaml. |
| Q9 | Market CSV names, tickers, and dates. No file names, ticker list, or date range is fixed. | Jayden picks the sector ETF list. The code worker downloads the CSV files before travel and records their names and date ranges in the vault. |
| Q10 | SenseVoice Small on Pi 5 ARM64. Size and RAM are unconfirmed. No install or test was done. | Install SenseVoice Small on the Pi, test EN and ZH, measure RAM and latency. If it fails, fall back to faster-whisper Base. |
| Q11 | ULN2003 at 3.3V on the bench. Vce_sat max is 1.6V per the DigiKey page, not 1.0V assumed. Resistor values are decided (see section 3.2). | Bench test every ULN2003 channel at 3.3V and measure each LED current with a multimeter. Fallback is TBD62083A, unconfirmed, or a logic level MOSFET per LED. |
| Q12 | Button LEDs run from 5V through built-in resistors. The exact EG STARTS part is unconfirmed. | Read the part datasheet before wiring and measure the current with a multimeter on the bench. |
| Q13 | Bocha cost cap and DeepSeek cost cap confirmation. DeepSeek daily cap USD 5.0, estimated. No Bocha cap exists. | Jayden confirms the daily cap in dollars. The code worker adds a Bocha cap the same way. The bridge logs cost per call. |
| Q14 | Claim expiry and task status. Expiry leaves the task status as working. A second claim gets 409. | The bridge must decide whether expiry resets the task to queued with reason CLAIM_EXPIRED. The code worker implements it. |
| Q15 | NEEDS APPROVAL pause in coordinator.py is a skeleton. It logs the pause, it does not wait for the bridge. | The code worker wires the coordinator to wait on the bridge approval state, with the 120 s timeout, and tests it with a real button press. |
| Q16 | Software freeze flag has no state.json field. | Add software_freeze to the state.json field list in ARCHITECTURE.md. Make the bridge enforce it. |
| Q17 | API error code table. INTEGRATION.md invents 12 codes with no ARCH source. | Write one error code table in ARCHITECTURE.md and make INTEGRATION.md match it. |
| Q18 | Slide task risk_check: blank or pass. A slide task is not a trade, so risk_check should be blank, but the worked example keeps risk_check pass. | The lead picks one rule for non-trade tasks, blank or pass, and the fix is applied to both files. |
| Q19 | SHELL_DENY and shell allow list. ARCH logs SHELL_DENY when a shell command is rejected, but the allow list and the deny code are not in one table. | List the allowed shell commands and the deny code together in ARCHITECTURE.md section 5.2. |
| Q20 | MakerLabs age rule for Jayden at 18. Drop-in LaserLab needs an orientation class first. Age rule is unverified. Vancouver Hack Space is blocked, age 19 plus, confirmed. FabLab is 320 CAD minimum for 2 months, too expensive. | Call or email MakerLabs and ask if an 18 year old can take the orientation class and use the drop-in lab alone. |
| Q21 | Laser timing vs Fallen approval. Files sent Fri Nov 27 finish Dec 7 to 9, too late for Dec 8. Fallen approval time is estimated 2 to 4 business days, never verified. | Ask Fallen the approval time at submission. Send laser files Mon Nov 23 if the drop-in path is not available. |
| Q22 | Grant cap unknown. Do not guess. | Ask Fallen the cap at submission, then apply the cut order: voice first, then mini screen. Buttons, LEDs, kill switch, agents never cut. The lit-button cut no longer exists. |
| Q23 | MSI monitor BC store pickup stock. Sold out online, confirmed. In-store BC pickup stock was not re-checked. | Check Canada Computers BC store stock before ordering, or order online if it comes back. Note: the brief of 2026-11-23 says the monitor is bought. |
| Q24 | Acrylic price. 32.99 CAD confirmed only by a 210-day-old crawl. | Re-check the price at order time. Confirm the sheet size covers the 360 by 240 mm panels. |
| Q25 | Mic product page. FIFINE AM8 is 79.99 CAD, unconfirmed. The BOM link is now a direct product page, fixed in Rev R2. Price was not in the fetched text. | Check price and delivery at checkout. |
| Q26 | Breakout Canadian seller. The Pi-EzConnect HAT is Adafruit 2711, 19.95 USD, about 27.93 CAD at 1.40, US store, shipping and customs extra. | Resolved in part: Rev R2 replaced the HAT with the Adafruit Pi Cobbler Plus from Solarbotics, 11.80 CAD, confirmed. The HAT question is closed unless the Cobbler fails. |
| Q27 | Pi-EzConnect HAT clearance vs Active Cooler. Unverified. | Closed by the Rev R2 change to the Pi Cobbler Plus. The HAT is not used. |
| Q28 | Mini screen config.txt change. Waveshare claims driver-free, but the PiShop FAQ says config.txt must be changed per the wiki. | Test the mini screen on the Pi first, apply the config.txt change if needed, record the exact lines. |
| Q29 | USB power headroom. Old budget: 0.90A typical, 1.50A peak vs 1.6A limit, headroom 0.10A only. | Superseded by Rev R2.1. New headroom is about 1.0A, estimated. Still unmeasured. Measure real USB current on the bench with all devices plugged in. Test whether the monitor built-in 1W speakers can replace the external USB speaker. |
| Q30 | Heat in a closed acrylic case. Vents are only 1440 mm2, estimated. Old note said no case fan is in the BOM. | Rev R2.1 added a 5V case fan, 4.19 CAD, confirmed. Run the 2 hour lid-closed heat test early, in Stage 2, not Dec 5. Fail if over 75C for 5 min or throttled is not 0x0. |
| Q31 | Chinese demo sentences are translations, not verified by a native speaker. | Have a native speaker check the cue card before Shenzhen. |
| Q32 | Text input fallback has no designed field. No keyboard is in the BOM. No strings.json IDs cover it. | Design a text field on the main screen, add a keyboard to the BOM or use an on-screen keyboard, test it with voice off. |
| Q33 | DeepSeek and Bocha in Shenzhen. Neither tested from China. | Test both from Shenzhen on arrival day. Have the recorded fallback ready before the booth opens. |
| Q34 | Kill switch depth. APEM depth 78.3 mm vs 75 mm clearance, 3.3 mm over. | Measure the APEM kill switch cutout, 22.3 mm, and the depth in the CAD redraw. Fix the drawing before cutting. |
| Q35 | Closed. LED names and colours are decided: COORD green, AGENT 1 white, AGENT 2 blue, GUARD yellow. | None. |

### 13.3 Resolved in session, kept here so the fix is visible

| ID | Fix |
|---|---|
| G2 | Button LED GPIO pins. Green GPIO20 pin 38, red GPIO21 pin 40. |
| G3 | Kill LED pattern. All 4 agent LEDs off, plus red button LED solid on. If the red button has no LED, KILL ACTIVE on both screens only. |
| G4 | strings.json sentence IDs. code/dashboard/strings.json was written with 15 sentence IDs, EN and ZH. Chinese translations are draft, not verified by a native speaker. |
| G6 | External API. Specified in INTEGRATION.md. Ports 8000 and 8001, claim TTL 300 s, heartbeat 60 s, rate limit 10 per min, research max 20000 chars, report max 5000 chars, token revoked after 3 bad tries for 10 min. All estimated. |
| G8 | VAULT_CONFLICT missing from the risk_reason list. Added to ARCHITECTURE.md section 8.2. |
| G11 | Dashboard and bridge ports. 8000 and 8001, estimated. |
| G13, part | DeepSeek cost cap. A daily cost cap was added: USD 5.0, estimated, in config. Bocha cost cap is still open, see Q13. |
| G15 | External task types narrowed to research and narration only, per INTEGRATION.md section 8.2. Needs ARCHITECTURE.md to confirm the narrowing. |
| G17 | Voice intent mapping. code/si_console/voice_intents.py was written with a fixed EN and ZH vocabulary, negatives win, no API call. |

### 13.4 Questions to ask Fallen at submission

1. What is the grant cap in CAD, and does it cover shipping, tax, and laser cutting?
2. How long does design approval take in business days?
3. Can self-funded parts, the MSI monitor and power brick, be bought before approval?
4. Is AI-assisted code allowed with disclosure, and what disclosure is needed?
5. What is the team size limit, and does Brent count as a team member for the prize?
6. Can laser files be sent before approval, or must the design be approved first?
7. Is there a parts order deadline, or only the Dec 8 build deadline?

### 13.5 Questions to ask MakerLabs

1. Can an 18 year old take the orientation class and use the drop-in LaserLab alone?
2. What is the current full service lead time for 3 mm acrylic, and what is the rush lead time?
3. What file types do you accept, and what is the file setup fee?

### 13.6 Questions to ask Jayden

1. Scenario start date and start holdings for 2020 and 2022.
2. Sector ETF list for the rules engine.
3. Daily cost cap in dollars for DeepSeek and Bocha.
4. Final LED colour for each agent.
5. Kill pattern is set, see G3. Confirm the red button has an LED, or the pattern is screens only.
6. Pursue or park Fallen, given Summit Nov 21, Harvest Dec 4, and the Dec 8 build deadline.

### 13.7 Single next step

Ask Fallen the grant cap and the approval time at submission, and ask MakerLabs if an 18 year old can use the drop-in LaserLab alone. Those two answers decide the budget and the laser path, and both are needed before Mon Nov 23.
