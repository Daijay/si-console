"""Writes the R5 wiring diagram (SVG) to ../blueprints/R5/. Pins follow docs/GPIO_PIN_MAP.md.

    python wiring_diagram.py

The PNG next to it is a browser screenshot of the SVG at 1x (1760 x 1360).
"""
import os
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blueprints", "R5", "wiring_diagram_R5.svg")
W, H = 1760, 1360
C = {"green": "#12a037", "red": "#d71920", "yellow": "#f2c500", "white": "#ffffff", "orange": "#f57c00", "blue": "#1f55d6",
     "grey": "#9a9da3", "black": "#141414"}
S = []


def text(x, y, t, size=14, weight="normal", anchor="start", fill="#111"):
    S.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{escape(t)}</text>')


def box(x, y, w, h, fill="#f4f6f8", stroke="#222", dash=False, rx=8):
    d = ' stroke-dasharray="7 5"' if dash else ""
    S.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>')


def wire(pts, colour, width=4):
    p = " ".join(f"{x},{y}" for x, y in pts)
    for stroke, wd in (("#222", width + 1.8), (C[colour], width)):
        S.append(f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{wd}" stroke-linejoin="round"/>')


def dot(x, y, r=4.5):
    S.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#111"/>')


def label(x, y, t, size=13, anchor="start", weight="normal"):
    """Text on a white backing so it stays readable over wires."""
    w = len(t) * size * 0.58 + 8
    x0 = x - 4 if anchor == "start" else x - w / 2 if anchor == "middle" else x - w + 4
    S.append(f'<rect x="{x0}" y="{y - size}" width="{w}" height="{size + 5}" fill="#fff" opacity="0.92"/>')
    text(x, y, t, size, weight, anchor)


def gnd(x, y):
    wire([(x, y), (x, y + 14)], "black", 3)
    for i, half in enumerate((13, 8, 3)):
        S.append(f'<line x1="{x - half}" y1="{y + 15 + 5 * i}" x2="{x + half}" y2="{y + 15 + 5 * i}" stroke="#111" stroke-width="2.4"/>')


def led(x, y, colour):
    """LED symbol on a horizontal run: anode on the right, cathode on the left (current flows right to left)."""
    S.append(f'<circle cx="{x}" cy="{y}" r="17" fill="{C[colour]}" stroke="#111" stroke-width="1.8"/>')
    S.append(f'<path d="M {x + 8} {y - 9} L {x + 8} {y + 9} L {x - 7} {y} Z" fill="#fff" stroke="#111" stroke-width="1.4"/>')
    S.append(f'<line x1="{x - 8}" y1="{y - 9}" x2="{x - 8}" y2="{y + 9}" stroke="#111" stroke-width="2.4"/>')


# ------------------------------------------------------------------ title
text(1460, 52, "SI CONSOLE", 30, "bold")
text(1460, 80, "Wiring diagram, Rev R5 (open frame)", 15)
text(1460, 102, "Pins: docs/GPIO_PIN_MAP.md (BCM / physical)", 13)

# ------------------------------------------------------------------ top row: power and displays
box(30, 140, 220, 72, "#fff3e0")
text(140, 166, "Pi 27 W USB-C supply", 15, "bold", "middle")
text(140, 188, "5.1 V 5 A, powers the Pi only", 12, "normal", "middle")
box(390, 24, 240, 62, "#fff3e0")
text(510, 49, "Monitor charger", 15, "bold", "middle")
text(510, 70, "20 W USB-C (5 V 3 A)", 12, "normal", "middle")
box(790, 24, 240, 62, "#fff3e0")
text(910, 49, "Mini screen charger", 15, "bold", "middle")
text(910, 70, "separate USB charger", 12, "normal", "middle")
box(360, 140, 300, 70, "#e8eaf6")
text(510, 168, "Main monitor", 16, "bold", "middle")
text(510, 191, "MSI PRO MP165 E6, behind the base", 12, "normal", "middle")
box(760, 140, 300, 70, "#e8eaf6")
text(910, 168, "Mini screen, on its angled stand", 16, "bold", "middle")
text(910, 191, "Waveshare 5inch HDMI LCD (H)", 12, "normal", "middle")
box(1180, 140, 240, 70, "#e8f5e9")
text(1300, 168, "USB microphone", 16, "bold", "middle")
text(1300, 191, "FIFINE AmpliGame AM8", 12, "normal", "middle")
wire([(510, 86), (510, 140)], "black", 5)
label(520, 118, "USB-C power")
wire([(910, 86), (910, 140)], "black", 5)
label(920, 118, "USB power (USB-A to micro-B)")
wire([(60, 212), (60, 300)], "black", 5)
label(14, 232, "USB-C power", 12)
wire([(100, 300), (100, 240), (500, 240), (500, 210)], "black", 5)
label(290, 234, "HDMI: micro-HDMI 0 + adapter", 12, "middle")
wire([(150, 300), (150, 258), (870, 258), (870, 210)], "black", 5)
label(690, 252, "HDMI: micro-HDMI 1 + adapter", 12, "middle")
wire([(200, 300), (200, 277), (1300, 277), (1300, 210)], "black", 5)
label(1110, 271, "USB-A to the Pi", 12, "middle")

# ------------------------------------------------------------------ Pi and breakout
box(30, 300, 220, 745, "#e8f5e9")
for x, t in ((60, "PWR"), (100, "HD0"), (150, "HD1"), (200, "USB")):
    text(x, 318, t, 11, "bold", "middle")
text(140, 420, "Raspberry Pi 5 8GB", 17, "bold", "middle")
text(140, 444, "with Active Cooler", 14, "normal", "middle")
text(140, 466, "back left of the base", 12, "normal", "middle")
text(140, 650, "40-pin GPIO header", 13, "bold", "middle")
text(140, 670, "3.3 V logic only", 12, "normal", "middle")
box(330, 318, 220, 727, "#e3f2fd")
text(440, 1068, "GPIO ribbon breakout", 15, "bold", "middle")
wire([(250, 655), (330, 655)], "grey", 22)
label(290, 628, "ribbon", 12, "middle")


def pad(y, t, colour):
    S.append(f'<circle cx="550" cy="{y}" r="6" fill="{C[colour]}" stroke="#111" stroke-width="1.5"/>')
    text(538, y + 5, t, 13, "bold", "end")


# 5 V rail
pad(340, "5V  pins 2, 4", "red")
wire([(550, 340), (1690, 340), (1690, 750)], "red")
label(1220, 333, "5 V rail (from the Pi, never from a GPIO pin)", 13, "middle")

# ------------------------------------------------------------------ ULN2003 and LEDs
box(820, 358, 450, 424, "#fbf3df", "#8a6d1d", True)
text(836, 802, "Perfboard, right side of the base", 13, "bold")
box(900, 370, 260, 402, "#263238")
text(1030, 392, "ULN2003AN (DIP-16)", 15, "bold", "middle", "#fff")
channels = [
    (400, "COORD", "GPIO5  pin 29", 1, 16, "green", "200 Ω", "COORD status LED (green)"),
    (450, "AGENT 1", "GPIO6  pin 31", 2, 15, "white", "100 Ω", "AGENT 1 status LED (white)"),
    (500, "AGENT 2", "GPIO13  pin 33", 3, 14, "blue", "100 Ω", "AGENT 2 status LED (blue)"),
    (550, "GUARD", "GPIO19  pin 35", 4, 13, "yellow", "220 Ω", "GUARD status LED (yellow)"),
    (600, "GRN BTN LED", "GPIO20  pin 38", 5, 12, "green", "see note A", "LED inside the green button"),
    (650, "RED BTN LED", "GPIO21  pin 40", 6, 11, "red", "see note A", "LED inside the red button"),
]
box(1340, 362, 330, 318, "none", "#37474f", True)
text(1350, 702, "LEDs on the control strip", 13, "bold")
for y, name, gp, inp, outp, col, res, desc in channels:
    pad(y, gp, col)
    wire([(550, y), (900, y)], col)
    label(600, y - 8, f"{name} to IN{inp}", 13)
    text(910, y + 5, f"{inp}  IN{inp}", 13, "bold", "start", "#fff")
    text(1150, y + 5, f"OUT{inp}  {outp}", 13, "bold", "end", "#fff")
    wire([(1160, y), (1425, y)], col)
    led(1425, y, col)
    wire([(1442, y), (1545, y)], col)
    dashed = res.startswith("see")
    box(1545, y - 13, 100, 26, "#fff", "#111", dashed, 3)
    text(1595, y + 5, res, 13, "bold", "middle")
    wire([(1645, y), (1690, y)], "red")
    dot(1690, y)
    text(1352, y - 22 if False else y - 20, desc, 11)
text(910, 705, "7  IN7", 13, "bold", "start", "#fff")
text(1150, 705, "OUT7  10 (unused)", 12, "normal", "end", "#cfd8dc")
wire([(900, 700), (860, 700), (860, 716)], "grey")
gnd(860, 716)
label(760, 694, "IN7 tied to GND", 13)
text(910, 755, "8  GND", 13, "bold", "start", "#fff")
text(1150, 755, "COM  9", 13, "bold", "end", "#fff")
wire([(900, 750), (800, 750), (800, 756)], "black")
gnd(800, 756)
wire([(1160, 750), (1690, 750)], "red")
label(1420, 743, "COM (pin 9) to 5 V", 13, "middle")

# ------------------------------------------------------------------ buttons and switches
box(610, 1075, 1100, 180, "none", "#37474f", True)
text(1696, 1244, "Control strip, front of the base: buttons and switches", 13, "bold", "end")
buttons = [  # rows run right to left so no signal wire crosses another
    (830, "LANG", "GPIO24  pin 18", "orange", 1540, "EN/ZH toggle", "ON-OFF, 12 mm", "GND bus"),
    (870, "PTT", "GPIO23  pin 16", "white", 1330, "Push to talk", "momentary, 12 mm", "GND bus"),
    (910, "K", "GPIO22  pin 15", "yellow", 1120, "Kill switch (NC)", "latching, 22 mm", "GND pin 25"),
    (950, "R", "GPIO27  pin 13", "red", 910, "Red button", "reject, 30 mm", "GND pin 20"),
    (990, "G", "GPIO17  pin 11", "green", 700, "Green button", "approve, 30 mm", "GND pin 14"),
]
for y, tag, gp, col, x, name, sub, ground in buttons:
    pad(y, gp, col)
    wire([(550, y), (x - 40, y), (x - 40, 1110)], col)
    label(600, y - 8, f"{tag}: {name}", 13)
    box(x - 70, 1110, 140, 92, "#fff")
    dot(x - 40, 1110)
    text(x, 1142, name, 14, "bold", "middle")
    text(x, 1161, sub, 11, "normal", "middle")
    if tag == "K":
        text(x, 1186, "closed = LOW = run", 11, "bold", "middle")
    dot(x + 40, 1110)
    wire([(x + 40, 1110), (x + 40, 1090), (x + 82, 1090), (x + 82, 1225)], "black")
    dot(x + 82, 1225)
    label(x + 40, 1219, ground, 12, "middle", "bold")
pad(1025, "GND  6, 14, 20, 25, 30", "black")
wire([(550, 1025), (580, 1025), (580, 1225), (1622, 1225)], "black")
label(592, 1244, "GND bus", 12)

# ------------------------------------------------------------------ notes
text(30, 1292, "Inputs use the Pi internal pull-ups, active LOW. Kill switch: NC contacts between GPIO22 and GND; open (HIGH) means frozen. Never wire a button or switch to 5 V.", 13)
text(30, 1314, "LED path: 5 V rail, resistor, LED anode, LED cathode, ULN2003 output. A GPIO HIGH turns its LED on. Measure each LED's forward voltage before soldering (green especially).", 13)
text(30, 1336, "Note A: button LEDs with a built-in resistor get no external resistor. A plain LED needs 200 Ω (green) or 220 Ω (red). COORD green: 220 Ω if no 200 Ω is available.", 13)

svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="Segoe UI, Arial, sans-serif">\n<rect width="{W}" height="{H}" fill="#fff"/>\n' + "\n".join(S) + "\n</svg>\n")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf8", newline="\n").write(svg)
print(os.path.normpath(OUT))
