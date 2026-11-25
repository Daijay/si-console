# BOM notes (Rev R5, on top of R2.1 with both cuts)

STATUS: DRAFT. Prices CAD, before tax and shipping. Source file: `BOM.csv` (the only current BOM).

Rev R5 changes (open-frame design, 2026-11-23), applied to `BOM.csv`:
- 5V case fan removed (4.19 CAD). R5 has no enclosure and no fan; the Pi keeps its Active Cooler.
- Acrylic sheets cut from the 6-sheet buy (52.98) to the Fovorica 4-pack (32.99): R5 needs 2 sheets, plus 2 spare. The 2-pack at 19.99 would save another 13.00 but leaves no spare.
- Fundable total is now **767.15 CAD** before tax (was 791.33), saving 24.18. The with-tax figures in the table below are the old R2.1 ones; at the same rate as before (about 12%) the new total would be about 859.21 with tax, not re-verified.
- Not changed, flag for the team: the "Printed wedge" line (10.00, mini screen wedge and Pi bracket library) is no longer needed because R5's screen stand and brackets are laser-cut acrylic. Cable ties for the tie slots, and rubber feet, are not in the BOM.

Cuts applied to the Rev R2.1 file:
- Spare microSD (32GB, 27.99) removed. Clone the main card before travel instead.
- USB soundbar (25.99) removed. Audio goes through the monitor speakers over HDMI.

| Item | CAD |
| --- | --- |
| Fundable total, Rev R5 (fan and 2 acrylic sheets removed), before tax | 767.15 |
| Fundable total, R2.1 with both cuts, before tax | 791.33 |
| Same, before the cuts (R2.1 as received) | 845.31 |
| Savings from the two cuts | 53.98 |
| Fundable total with both cuts, with tax (from morning summary) | 886.29 |
| Self-funded (monitor, power brick, travel adapter), before tax | 128.24 |
| Self-funded, with tax | 143.63 |
| All-in with tax, before shipping and laser | 1090.38 |

The 791.33 figure was re-added from `BOM.csv` (30 lines); the 767.15 figure was re-added from the 29 lines left after the R5 edits. Tax and self-funded figures are copied from `research/overnight-notes/MORNING_SUMMARY_2026-11-23.md`; the self-funded rows are `REF ONLY` (qty 0) in the CSV.

Team limit is about 800 CAD, hard max 900 CAD. 767.15 is under both.

Open items: several rows are LIKELY or ASSUMED prices (see the status column), re-check at checkout. LED resistors are decided: green 150 ohm, white 100 ohm, blue 100 ohm, yellow 220 ohm; button LEDs use their built-in resistors (see `docs/GPIO_PIN_MAP.md`). Measure each LED on the bench.

The soundbar cut stands: sound comes from the monitor over HDMI (see `docs/decisions.md`).
