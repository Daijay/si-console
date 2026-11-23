# CHECKS, SI Console Rev R4.1

Run 2026-11-23 by `cad/build.py`. Overall: **ALL CHECKS PASSED**.

Screen mode: `window_under`. Laser sheets used: **4** (305 x 406 mm).

| Result | Check |
| --- | --- |
| PASS | No part collides with another in the assembly |
| PASS | Every hole fully inside its panel, at least 5 mm from any edge or other hole |
| PASS | Every panel fits on a 305 x 406 mm sheet |
| PASS | Finger joints mate between neighbouring panels |
| PASS | Clear space behind the arcade buttons (50 mm) and the kill switch (75 mm) |
| PASS | The Pi cables reach their back panel cutouts |
| PASS | Parameter sanity (screen window, fan opening, finger counts) |

## PASS: No part collides with another in the assembly

- 26 parts, 325 pairs tested, overlap tolerance 0.5 mm3. Parts that only touch (a standoff on a panel, a button flange on a face) count as clear.

## PASS: Every hole fully inside its panel, at least 5 mm from any edge or other hole

- top: 5 holes, closest to an edge 54.4 mm, closest pair 7.3 mm
- bottom: 12 holes, closest to an edge 24.9 mm, closest pair 26.7 mm
- front: 9 holes, closest to an edge 34.4 mm, closest pair 21.9 mm
- back: 21 holes, closest to an edge 9.3 mm, closest pair 5.5 mm
- left: 8 holes, closest to an edge 12.0 mm, closest pair 8.0 mm
- right: 8 holes, closest to an edge 12.0 mm, closest pair 8.0 mm

## PASS: Every panel fits on a 305 x 406 mm sheet

- top: 360.2 x 240.2 mm (with kerf), usable sheet 295 x 396
- bottom: 360.2 x 240.2 mm (with kerf), usable sheet 295 x 396
- front: 360.2 x 140.2 mm (with kerf), usable sheet 295 x 396
- back: 360.2 x 140.2 mm (with kerf), usable sheet 295 x 396
- left: 240.2 x 140.2 mm (with kerf), usable sheet 295 x 396
- right: 240.2 x 140.2 mm (with kerf), usable sheet 295 x 396

## PASS: Finger joints mate between neighbouring panels

- edge top-front: 23 fingers of 15.39 mm, top owns the ends
- edge top-back: 23 fingers of 15.39 mm, top owns the ends
- edge top-left: 15 fingers of 15.60 mm, top owns the ends
- edge top-right: 15 fingers of 15.60 mm, top owns the ends
- edge bottom-front: 23 fingers of 15.39 mm, bottom owns the ends
- edge bottom-back: 23 fingers of 15.39 mm, bottom owns the ends
- edge bottom-left: 15 fingers of 15.60 mm, bottom owns the ends
- edge bottom-right: 15 fingers of 15.60 mm, bottom owns the ends
- edge front-left: 9 fingers of 14.89 mm, front owns the ends
- edge front-right: 9 fingers of 14.89 mm, front owns the ends
- edge back-left: 9 fingers of 14.89 mm, back owns the ends
- edge back-right: 9 fingers of 14.89 mm, back owns the ends
- corner-top cube filled
- corner-top cube filled
- corner-top cube filled
- corner-top cube filled
- corner-bottom cube filled
- corner-bottom cube filled
- corner-bottom cube filled
- corner-bottom cube filled
- fit gap per finger side after laser kerf compensation: 0.00 mm (cut paths offset by 0.1 mm so parts finish at nominal size)

## PASS: Clear space behind the arcade buttons (50 mm) and the kill switch (75 mm)

- btn_green: zone 40 x 40 mm, 50 mm deep, own body uses 30 mm, nothing behind it
- btn_red: zone 40 x 40 mm, 50 mm deep, own body uses 30 mm, nothing behind it
- kill_switch: zone 32 x 32 mm, 75 mm deep, own body uses 55 mm, nothing behind it
- btn_ptt: zone 22 x 22 mm, 30 mm deep, own body uses 20 mm, nothing behind it
- toggle_lang: zone 22 x 22 mm, 30 mm deep, own body uses 20 mm, nothing behind it

## PASS: The Pi cables reach their back panel cutouts

- micro-HDMI 0: port x=97.2, cutout x=98, sideways 0.8 mm, straight run after plug 38.4 mm, S-bend needs 8.0 mm (bend radius 20), margin 30.4 mm
- USB-C power: port x=111.8, cutout x=127, sideways 15.2 mm, straight run after plug 41.4 mm, S-bend needs 31.8 mm (bend radius 20), margin 9.6 mm
- mic USB: plug needs 30 mm left of the Pi, 32.0 mm available; cable path about 181 mm of 500 mm
- mini screen USB power: hole to the screen edge about 336 mm of cable inside the case, 450 mm available (the screen HDMI cable stays inside)
- GPIO ribbon: header to breakout about 34 mm of 150 mm

## PASS: Parameter sanity (screen window, fan opening, finger counts)

- window 109 x 66 is smaller than module 121 x 89.48: module cannot fall through
- mini screen top face 134.0 mm, panel underside 137 mm, gap 3 mm

## Nested layout

- Sheet 1: top (rotated) 240.2 x 360.2
- Sheet 2: bottom (rotated) 240.2 x 360.2
- Sheet 3: front (rotated) 140.2 x 360.2, back (rotated) 140.2 x 360.2
- Sheet 4: left (rotated) 140.2 x 240.2, right (rotated) 140.2 x 240.2
