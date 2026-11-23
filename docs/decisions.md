# Decisions

STATUS: DRAFT. Figures come from `research/overnight-notes/MORNING_SUMMARY_2026-11-23.md`. "Final choice" stays blank until the team decides.

## A. From the overnight run (recommendations, awaiting confirmation)

### 1. Case material
- Options: clear laser-cut acrylic, or nylon print at JLCPCB.
- Cost: acrylic about 103 to 153 CAD with laser, files go today, arrives by Dec 2. Nylon about 125 to 145 CAD all in (ASSUMED), 1 to 2 days of redesign, likely misses Dec 1.
- Recommendation: acrylic now, nylon as a second case later.
- Final choice: _pending_

### 2. Mini screen
- Options: 5 inch HDMI (Waveshare, 73.95 CAD) or 5 inch DSI LCD (about 73.94 CAD, needs a cable, overlay test, Rev2.2 check and a top panel redraw). The brief's 5.5 inch DSI touchscreen does not exist.
- Recommendation: HDMI.
- Final choice: _pending_

### 3. Model router
- Options: DeepSeek only at the booth, or add Claude (claude-fable-5-2, 8 USD input / 40 USD output per 1M tokens, about 27x DeepSeek flash). Anthropic policy does not support use by persons physically in mainland China. The router stub falls back to DeepSeek only.
- Recommendation: DeepSeek only, premium tier maps to deepseek-v4-pro.
- Final choice: _pending_

## B. R3 review notes, OPEN for the team

### OPEN 1. Mini screen cutout (owner: Hasan, in CAD)
The 122 x 90.5 mm cutout is the full module size, so the screen would fall through. Options:
1. Cut to the visible display area and screw the module underneath.
2. Keep the full cutout and add a printed bezel on top.

### OPEN 2. Soundbar cut (owner: Hasan, drawings)
If the soundbar cut is applied (use monitor speakers over HDMI), remove the speaker grille holes and the soundbar from the drawings. The BOM already has the cut applied.

### OPEN 3. Pi 5 port side (owner: Hasan, CAD)
Pi 5 HDMI and USB-C power are on its long side, not the USB/Ethernet end. Check back panel cable routing in CAD.

### OPEN 4. LED colours (owner: Jayden)
AGENT 1 changes from red to white. Red stays for reject and kill only. Update drawings and the resistor table (white LED Vf is not in the current resistor math in `GPIO_PIN_MAP.md`).

### OPEN 5. Laser cut file source (owner: Hasan)
R3 drawings are reference only. The laser cut file must come from Hasan's Fusion model as DXF or SVG cut lines.
