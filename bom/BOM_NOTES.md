# BOM notes (Rev R5, updated 2026-11-24)

STATUS: DRAFT. Prices CAD, before tax and shipping. Source file: `BOM.csv` (the only current BOM).

## Current totals

| Item | CAD |
| --- | --- |
| **Fundable total, before tax** | **851.13** |
| Tax at 12 percent, ASSUMED to apply to every line | 102.14 |
| Fundable total, with tax | 953.27 |
| Self-funded (monitor, power brick, travel adapter), before tax | 128.24 |
| Self-funded, with tax | 143.63 |
| All-in with tax, before shipping and laser | 1096.90 |

Re-added from the 27 fundable lines of `BOM.csv`. Status mix of the fundable total: VERIFIED 474.30, LIKELY 269.86, ASSUMED 106.97. Do not treat the total as verified. Self-funded figures are copied from `research/overnight-notes/MORNING_SUMMARY_2026-11-23.md`; those rows are `REF ONLY` (qty 0) in the CSV.

**Limits:** team limit about 800 CAD, hard max 900 CAD. 851.13 before tax is **51.13 over the team limit** and 48.87 under the hard max. With tax (953.27) it is 53.27 over the hard max, if the limit counts tax.

## Changes on 2026-11-24 (decided by Jayden, see `docs/decisions.md`)

| Line | CAD | Status |
| --- | --- | --- |
| USB soundbar, restored | 25.99 | VERIFIED price. Not modelled in the R5 CAD yet |
| Spare microSD 32GB, restored | 27.99 | VERIFIED price and page |
| API credits, DeepSeek and Bocha, new | 40.00 | ASSUMED budget amount. Top-up pages are behind sign-in |
| Added | 93.98 | Total went from 757.15 to 851.13 |

The two restored lines were not in the git history of `BOM.csv` (the repo starts after they were cut). Model, price, store and link come from `docs/SI_Console_Detailed.md` section 2.3.

## History

| Revision | Fundable, before tax |
| --- | --- |
| R2.1 as received | 845.31 |
| R2.1 with the soundbar and spare card cut | 791.33 |
| R5: fan removed (4.19), acrylic cut from 52.98 to the 32.99 4-pack | 767.15 |
| Printed wedge line removed (10.00), R5 has no printed parts | 757.15 |
| 2026-11-24: soundbar, spare card and API credits | 851.13 |

R5 acrylic: 2 sheets needed plus 2 spare. The 2-pack at 19.99 would save 13.00 but leaves no spare. Cable ties for the tie slots, and rubber feet, are not in the BOM.

Open items: several rows are LIKELY or ASSUMED prices (see the status column), re-check at checkout. LED resistors are decided: green 150 ohm, white 100 ohm, blue 100 ohm, yellow 220 ohm; button LEDs use their built-in resistors (see `docs/GPIO_PIN_MAP.md`). Measure each LED on the bench.
