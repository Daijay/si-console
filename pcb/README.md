# SI Console HAT

A 2-layer, 1.6 mm Raspberry Pi 5 HAT-style carrier board (65 x 56.5 mm) that replaces the perfboard: ULN2003A LED driver, four LED resistors and a labelled screw terminal for every off-board wire. Pins follow `docs/GPIO_PIN_MAP.md`; no GPIO changed. The perfboard is the fallback, so the R5 wiring diagram (same electrical nets) was not changed.

![Front](../docs/images/pcb_front.png)
![Back](../docs/images/pcb_back.png)

## Connectors

| Ref | Label | Pins |
| --- | --- | --- |
| J2 | COORD | + (5 V through 150 ohm), - (OUT1, GPIO5) |
| J3 | AGENT 1 | + (100 ohm), - (OUT2, GPIO6) |
| J4 | AGENT 2 | + (100 ohm), - (OUT3, GPIO13) |
| J5 | GUARD | + (220 ohm), - (OUT4, GPIO19) |
| J6 | GREEN | SW (GPIO17), GND, L+ (5 V), L- (OUT5, GPIO20) |
| J7 | RED | SW (GPIO27), GND, L+ (5 V), L- (OUT6, GPIO21) |
| J8 | KILL | SW (GPIO22), GND, IL, IL (second NC contact, optional) |
| J9 | PTT | SW (GPIO23), GND |
| J10 | LANG | SW (GPIO24), GND |

## Optional kill interlock (off as built)

JP1 is closed and JP2 is open. To make the kill switch physically block approval, wire its second NC contact to the two IL terminals, **cut JP1**, then **solder JP2**. The contact is then in series with the green button signal. Cutting JP1 alone leaves the green button dead.

## Checks (KiCad 9.0.8)

- ERC: 0 errors, 0 warnings.
- DRC with schematic parity: 0 violations, 0 unconnected, 0 footprint errors.
- JLCPCB 2-layer rules in the .kicad_pro: 0.127 mm minimum track and clearance, 0.3 mm via drill, 0.45 mm via, 0.5 mm hole to hole, 0.3 mm copper to edge.
- `python pcb/check_nets.py`: 25 nets match `gpio_map.py`.
- Routed with Freerouting 2.5.0.

## Order from JLCPCB

1. Upload `gerbers.zip` at https://cart.jlcpcb.com/quote
2. 2 layers, 65 x 56.5 mm, qty 5, 1.6 mm, 1 oz, HASL (with lead).
3. Shipping to Canada: Global Standard Direct Line.
4. Quoted 2026-11-25 by dimensions (no file uploaded): US$4.00 boards + US$6.84 shipping = US$10.84, CAD 15.50 at 1.4296. Lead-free HASL adds US$1.20. Taxes and duties not included.

## Assembly

Solder resistors, DIP socket, then terminals. J1 is an extra-tall 2x20 female header soldered on the **underside**; trim the long pins. Mount on 16 mm M2.5 standoffs. Insert the ULN2003AN with its notch matching the silkscreen.

Optional JLCPCB assembly: `jlcpcb_bom.csv` and `jlcpcb_cpl.csv`. J1 is left out (hand fit). The DIP socket has no LCSC number yet. Check part rotations in the JLCPCB preview.

## Not verified

No board has been made or tested. Gerbers were not uploaded to JLCPCB. Active Cooler clearance is from drawings only (cooler 13.7 mm overall, header gives about 16 mm). Check that the kill switch has two NC contacts. The HAT is not modelled in the CAD. There is no HAT ID EEPROM.
