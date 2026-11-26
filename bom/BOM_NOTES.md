# BOM notes (Rev R5, updated 2026-11-26)

Prices in USD, to match the Fallen submission. Shipping is not included, except on the Custom PCB line. Source file: `BOM.csv` (the only current BOM).

## Current totals

| Item | USD |
| --- | --- |
| Fundable parts and API credits, before tax | 641.67 |
| BC tax, 12% GST+PST (its own row in the CSV) | 77.00 |
| **Fundable total, with tax** | **718.67** |
| Self-funded (monitor, power brick, travel adapter), before tax | 89.70 |
| Self-funded, with tax | 100.46 |
| All-in with tax, before shipping and laser | 819.13 |

Converted from the earlier CAD prices at 1.4296 CAD per USD, rounding each unit price to 2 decimals; the Custom PCB is the quoted US$10.84. The conversion does not re-check any store price, and the Canadian store pages show CAD. 33 fundable lines (two of them qty 0) plus the tax row. Status mix before tax, from the status column of the CSV: confirmed 356.05, unconfirmed 188.77, estimated 96.85. Notes on the self-funded `REF ONLY` rows still quote CAD.

**Limits:** the team limit (about 800) and hard max (900) were set in CAD. At 1.4296 the total is about 917.33 CAD before tax and 1027.41 CAD with tax: over both the team limit and the hard max, even before tax.

Amounts in the sections below are in CAD, as recorded at the time.

## Changes on 2026-11-26

The API credits line is now DeepSeek, Zhipu and Qwen at USD 50.00 (was USD 27.98). Tax is 77.00 and the fundable total is USD 718.67 including tax (was 694.01).

## Changes on 2026-11-25

Custom PCB and its parts added (34.68 CAD), total 851.13 to 885.81. The perfboard line stays as the fallback.

## Changes on 2026-11-24 (decided by Jayden, see `docs/decisions.md`)

| Line | CAD | Status |
| --- | --- | --- |
| USB soundbar, restored | 25.99 | Confirmed price. Not modelled in the R5 CAD yet |
| Spare microSD 32GB, restored | 27.99 | Confirmed price and page |
| API credits, new | 40.00 | Estimated budget amount. Top-up pages are behind sign-in |
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

Open items: several rows are unconfirmed or estimated prices (see the status column), re-check at checkout. LED resistors are decided: green 150 ohm, white 100 ohm, blue 100 ohm, yellow 220 ohm; button LEDs use their built-in resistors (see `docs/GPIO_PIN_MAP.md`). Measure each LED on the bench.
