# CHECKS, SI Console Rev R5

Run 2026-11-23 by `cad/build.py`. Overall: **ALL CHECKS PASSED**.

Laser sheets used: **2** (305 x 406 mm).

| Result | Check |
| --- | --- |
| PASS | No part collides with another |
| PASS | Every hole fully inside its part, at least 5 mm from any edge or other hole |
| PASS | Every part fits on a 305 x 406 mm sheet |
| PASS | Tabs and slots mate (every slot is filled by exactly one tab) |
| PASS | Clear space behind the buttons (50 mm) and the kill switch (75 mm), checked against the base and everything else |
| PASS | Cables and wires reach between the Pi, breakout, perfboard and controls |
| PASS | Everything on the base is at least 15 mm from the base edge |

## PASS: No part collides with another

- 26 solid parts, 325 pairs tested, tolerance 0.5 mm3. Touching faces (standoff on plate, tab bottoming in a slot) count as clear. Wires and cables are not solids for this test; they end on their terminals by construction.

## PASS: Every hole fully inside its part, at least 5 mm from any edge or other hole

- control_strip: 13 holes, closest to an edge 8.0 mm, closest pair 12.3 mm
- strip_bracket: no holes (tabs only)
- screen_plate: 8 holes, closest to an edge 5.5 mm, closest pair 8.1 mm
- screen_prop: no holes (tabs only)
- base_plate: 26 holes, closest to an edge 17.4 mm, closest pair 7.0 mm

## PASS: Every part fits on a 305 x 406 mm sheet

- control_strip (x1): 300.2 x 70.2 mm with kerf, usable sheet 297 x 398
- strip_bracket (x2): 62.5 x 86.3 mm with kerf, usable sheet 297 x 398
- screen_plate (x1): 150.2 x 114.2 mm with kerf, usable sheet 297 x 398
- screen_prop (x2): 29.4 x 111.8 mm with kerf, usable sheet 297 x 398
- base_plate (x1): 330.2 x 220.2 mm with kerf, usable sheet 297 x 398

## PASS: Tabs and slots mate (every slot is filled by exactly one tab)

- 14 slots checked, each completely filled by a tab of the bracket or prop that belongs there

## PASS: Clear space behind the buttons (50 mm) and the kill switch (75 mm), checked against the base and everything else

- btn_green: zone 40 x 40 mm, 50 mm deep along the button axis, own body 30 mm; lowest point of the zone is 10.4 mm above the base plate
- btn_red: zone 40 x 40 mm, 50 mm deep along the button axis, own body 30 mm; lowest point of the zone is 10.4 mm above the base plate
- kill_switch: zone 32 x 32 mm, 75 mm deep along the button axis, own body 55 mm; lowest point of the zone is 5.6 mm above the base plate
- btn_ptt: zone 22 x 22 mm, 30 mm deep along the button axis, own body 20 mm; lowest point of the zone is 25.7 mm above the base plate
- toggle_lang: zone 22 x 22 mm, 30 mm deep along the button axis, own body 20 mm; lowest point of the zone is 25.7 mm above the base plate

## PASS: Cables and wires reach between the Pi, breakout, perfboard and controls

- GPIO ribbon (Pi header to breakout): GPIO ribbon 68 mm of 150 mm
- button wires (breakout to controls): G 207 mm of 300 mm
- button wires (breakout to controls): R 150 mm of 300 mm
- button wires (breakout to controls): K 165 mm of 300 mm
- button wires (breakout to controls): PTT 227 mm of 300 mm
- button wires (breakout to controls): LANG 269 mm of 300 mm
- button wires (breakout to controls): GND 174 mm of 300 mm
- LED wires (breakout to ULN2003 inputs): COORD 164 mm of 200 mm
- LED wires (breakout to ULN2003 inputs): AGENT 1 157 mm of 200 mm
- LED wires (breakout to ULN2003 inputs): AGENT 2 151 mm of 200 mm
- LED wires (breakout to ULN2003 inputs): GUARD 144 mm of 200 mm
- LED wires (breakout to ULN2003 inputs): GRN LED 138 mm of 200 mm
- LED wires (breakout to ULN2003 inputs): RED LED 131 mm of 200 mm
- LED wires (ULN2003 outputs to LEDs): COORD LED 216 mm of 300 mm
- LED wires (ULN2003 outputs to LEDs): AGENT1 LED 195 mm of 300 mm
- LED wires (ULN2003 outputs to LEDs): AGENT2 LED 181 mm of 300 mm
- LED wires (ULN2003 outputs to LEDs): GUARD LED 179 mm of 300 mm
- power (Pi header to perfboard): 5V 187 mm of 300 mm
- power (Pi header to perfboard): GND PWR 176 mm of 300 mm
- ULN2003 IN7 tied to GND: IN7 28 mm of 50 mm
- cables out of the Pi: HDMI MAIN 111 mm of 1000 mm
- cables out of the Pi: USB-C POWER 104 mm of 1200 mm
- cables out of the Pi: USB MIC 121 mm of 1000 mm
- cables out of the Pi: HDMI MINI 234 mm of 500 mm

## PASS: Everything on the base is at least 15 mm from the base edge

- min margins (mm): left 15.0, front 15.4, right 15.0, back 15.0

## Nested layout

- Sheet 1: base_plate (rotated), control_strip (rotated), strip_bracket_1, strip_bracket_2 (rotated), screen_prop_1 (rotated)
- Sheet 2: screen_plate, screen_prop_2
