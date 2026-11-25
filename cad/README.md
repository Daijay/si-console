# SI Console CAD, Rev R5 (open frame)

Parametric CadQuery model of the whole console as an open-frame "cyberdeck": no enclosure, no side walls, no lid, no back panel, no fan. The electronics and the wiring are the visual feature. Change one number in `params.py`, run `build.py`, and every part, laser file, drawing, render and check is regenerated.

The geometry is complete and every automated check passes (`output/CHECKS.md`), but some dimensions are estimates. See [Measure with calipers before cutting](#measure-with-calipers-before-cutting) at the bottom before sending anything to a laser.

The earlier boxed design (Rev R4.2: finger-jointed clear acrylic case, 40 mm fan) is kept as an alternative in `../research/R4.2-boxed/` and at git tag `r4.2-boxed`.

## The design

| Part | What it is |
| --- | --- |
| `base_plate` | One 330 x 220 mm clear 3 mm acrylic plate with rounded corners and 4 rubber feet. Everything screws onto it. The Pi, perfboard and breakout are fully exposed |
| `control_strip` | 300 x 70 mm panel, tilted 20 degrees from vertical (leaning back, face looks up at the user), standing at the front on two brackets. Green and red 30 mm buttons, 22 mm kill switch, 12 mm push-to-talk and EN/ZH toggle, 4 status LEDs (COORD green, AGENT 1 white, AGENT 2 blue, GUARD yellow) |
| `strip_bracket_1`, `strip_bracket_2` | Two identical laser-cut triangular brackets. Tabs go through slots in the base and in the strip, so no screws and no printing |
| `screen_plate` | 150 x 114 mm plate, same 20 degree tilt, carrying the Waveshare 5 inch HDMI screen (121 x 89.48 mm) on four M2.5 standoffs, facing the user, behind the strip |
| `screen_prop_1`, `screen_prop_2` | Two identical laser-cut props that hold the screen plate (tab and slot, same method as the brackets). The screen stand is these 2 slotted part types (plate and prop) |
| Pi 5 + Active Cooler | On four 10 mm M2.5 standoffs, rotated 180 degrees: power and HDMI face the back so those cables leave straight off the back edge, the GPIO header faces the front toward the breakout, the USB end faces the left |
| Perfboard + ULN2003 | On four 10 mm M3 standoffs, right side |
| GPIO ribbon breakout | Between the Pi and the perfboard, on the base |
| Monitor | MSI PRO MP165 E6 behind the base on its own kickstand. Assembly only, never cut |
| Wires | Thin colour-coded tubes following the wiring table (`blueprints/R5/wiring_diagram_R5.svg`): G green, R red, K yellow, PTT white, LANG orange, COORD green, AGENT 1 white, AGENT 2 blue, GUARD yellow, 5V red, GND black, IN7 grey. Plus the ribbon and the HDMI, USB-C and mic cables |
| Cable-tie slots | Pairs of 3 x 5 mm holes in the base along the wire routes, 4 pairs |

"Slope" is read as 20 degrees from vertical (a dashboard-style strip). That puts the button bodies 50 to 75 mm back into open space above the base. If you meant 20 degrees from horizontal, set `STRIP_TILT = 70` and re-run: the clearance check will tell you what has to move.

## Run it

Tested on Python 3.11. The CadQuery OCP wheels for Python 3.14 were not available when this was built.

```
cd cad
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt     (Windows)
# source .venv/bin/activate && pip install -r requirements.txt   (macOS, Linux)

python build.py              # everything, about a minute
python build.py --no-render  # skip the PNG renders (about 10 s)
python build.py --no-copy    # do not copy finals into ../blueprints/R5
```

`build.py` exits with status 1 and prints a banner if any check fails. It still writes all outputs so you can look at the problem, and `output/CHECKS.md` says what failed.

## Change things

| I want to ... | Edit in `params.py` |
| --- | --- |
| Change the base plate size | `BASE_W`, `BASE_D`, `BASE_RADIUS` (the margin check tells you if parts no longer fit) |
| Change the strip slope or height off the base | `STRIP_TILT`, `STRIP_Z`, `STRIP_Y` |
| Move a button or LED | `GREEN_U`, `RED_U`, `KILL_U`, `PTT_U`, `TOGGLE_U`, `BTN_V`, `LED_V`, `LED_PITCH` |
| Move or tilt the screen stand | `SCREEN_CX`, `SCREEN_Y`, `SCREEN_Z`, `SCREEN_TILT`, `PLATE_*`, `PROP_*` |
| Move the Pi, perfboard or breakout | `PI_X0`, `PI_PORT_EDGE_Y`, `PERF_CX`, `PERF_CY`, `BREAKOUT_CX`, `BREAKOUT_CY` |
| Change acrylic thickness or kerf | `T`, `KERF` (slots, tabs and DXF follow) |
| Turn the monitor, wires or tie slots off | `INCLUDE_MONITOR`, `INCLUDE_WIRES`, `ENABLE_TIE_SLOTS` |

Every line in `params.py` ends with a tag:

- `VERIFIED`: from the brief, a manufacturer drawing, or the official Raspberry Pi STEP. Safe to cut from.
- `ASSUMED`: an estimate. Measure before cutting. Listed at the bottom of this file and in `output/ASSUMED.md`, and drawn in orange with an "A" on the drawings.
- `DESIGN`: a free layout choice. Nothing to measure.

Wire routes live in `wires.py`. They are hand-routed polylines, so if you move a part the wires may need a nudge there. The check measures every wire's length against its limit.

## Files

| File | What it does |
| --- | --- |
| `params.py` | Every dimension and switch, one comment and one tag per line |
| `build.py` | Runs everything and writes the outputs |
| `geo.py` | Shared helpers: tilted-plate frames, Pi, breakout and ULN2003 pin positions |
| `panels.py` | The five laser parts as one 2D model each (outline, holes), plus their 3D solids |
| `parts.py` | Controls, Pi 5, screen, feet, monitor, wire tubes and the assembly |
| `wires.py` | Wire and cable routes, colours, length limits, cable-tie positions |
| `checks.py` | The checks |
| `outputs.py` | STEP, DXF, nesting and the dimensioned drawings |
| `render.py` | Labelled PNG renders (VTK, offscreen) |
| `requirements.txt` | Pinned versions |

## Outputs (all in `output/`, finals also copied to `../blueprints/R5/`)

| File or folder | Contents |
| --- | --- |
| `si_console_assembly_R5.step` | Whole assembly, named parts with colours |
| `step/` | One STEP per part: `base_plate`, `control_strip`, `strip_bracket_1`, `strip_bracket_2`, `screen_plate`, `screen_prop_1`, `screen_prop_2`, the components, and one per wire |
| `dxf/laser_<part>_x<qty>_R5.dxf` | Each laser part as clean cut lines on layer `CUT`, kerf applied. `x2` in the name means cut two |
| `dxf/nested_sheet_N_R5.dxf` | Nested sheets for 12 x 16 in (305 x 406 mm) stock. Part names are on layer `LABEL_NOCUT`, which a laser should not cut |
| `dxf/nested_layout_R5.png` | Picture of the nested sheets |
| `drawings/laser_<part>_R5.svg`, `laser_parts_R5.pdf` | Dimensioned drawing of every laser part: overall size, every hole position and size (or every corner for the plain brackets and props) |
| `renders/` | hero, front, top and exploded, acrylic transparent, wires visible and colour-keyed |
| `CHECKS.md`, `ASSUMED.md` | Check results and the ASSUMED list |

There are no 3D-printed parts in R5, so no STL files.

Sheets used: **2**. Sheet 1 holds the base plate, the control strip, both brackets and one prop; sheet 2 holds the screen plate and the other prop. All of it cannot fit one sheet: the parts add up to more than a sheet's area.

## Checks

| Check | How |
| --- | --- |
| No collisions | Every pair of solid parts is intersected in 3D. Touching is fine, overlap above 0.5 mm3 fails. Wires end on their terminals by construction and are not part of this test |
| Holes | Every hole inside its part, at least 5 mm from any edge and from any other hole (this applies to the cable-tie slots and the tab slots too) |
| Sheet fit | Each part with kerf must fit the 305 x 406 mm sheet minus a 4 mm margin |
| Tabs and slots | Every slot's volume must be filled by the tab of the bracket or prop that belongs there, so the pieces really interlock |
| Clearances | A box behind each control (hole plus 5 mm each side) must contain no other part, including the base plate and the screen. Depth is measured along the button axis from the strip's rear face: 50 mm for green and red, 75 mm for the kill switch. The box must also stay above the base surface |
| Cables | Every wire's routed length (plus 10% slack) against its limit: button wires 30 cm, GPIO to ULN2003 wires 20 cm, ribbon 15 cm, mini HDMI 50 cm |
| Layout | Every part on the base stays 15 mm inside the base edge (cables and plugs may hang off the edge, the feet and the monitor are excluded) |

The cable check is geometry with assumed limits, not a physical test. Do a dry fit with the real cables.

## Measure with calipers before cutting

Everything below is tagged `ASSUMED` in `params.py`. Measure the real part, change the number, and re-run `build.py`. This list is regenerated by `build.py` from `params.py`.

<!-- ASSUMED:START (generated by build.py, do not edit by hand) -->

| Parameter | Value | What it is |
| --- | --- | --- |
| `T` | `3.0` | Acrylic thickness as delivered (cast sheet varies 2.9 to 3.2). Tab and slot fit depends on it. |
| `BASE_W` | `330.0` | Base plate width: the 300 mm strip plus 15 mm margins each side. |
| `BASE_D` | `220.0` | Base plate depth. |
| `FOOT_D` | `15.0` | Rubber foot diameter. |
| `FOOT_H` | `6.0` | Rubber foot height. |
| `FOOT_HOLE_D` | `4.2` | Foot screw hole (M4). |
| `STRIP_W` | `300.0` | Strip width ("about 300"). |
| `STRIP_H` | `70.0` | Strip height ("about 80", trimmed so base plus strip share one 305 mm sheet). |
| `BTN_FLANGE_D` | `36.0` | Arcade button front flange diameter. |
| `BTN_CAP_PROUD` | `10.0` | Arcade cap height in front of the strip. |
| `ARCADE_REAR` | `30.0` | Arcade body depth behind the strip (incl. microswitch). |
| `KILL_HEAD_D` | `40.0` | Kill switch mushroom head diameter. |
| `KILL_HEAD_H` | `22.0` | Kill switch head height in front of the strip. |
| `KILL_REAR` | `55.0` | Kill switch body depth behind the strip. |
| `PTT_HEAD_D` | `14.0` |  |
| `PTT_HEAD_H` | `6.0` |  |
| `PTT_REAR` | `20.0` |  |
| `TOGGLE_LEVER_D` | `4.0` |  |
| `TOGGLE_LEVER_H` | `15.0` |  |
| `TOGGLE_REAR` | `20.0` |  |
| `LED_FLANGE_D` | `5.9` | LED rim, sits behind the strip. |
| `LED_DOME_PROUD` | `1.0` |  |
| `LED_REAR` | `8.0` |  |
| `SCREEN_MODULE_H` | `13.0` | Module thickness incl. rear connectors. |
| `SCREEN_HOLE_INSET` | `3.5` | Module mounting hole distance from each module edge. |
| `MON_TILT` | `15.0` | Kickstand tilt from vertical. |
| `PI_PORT_Z` | `1.7` | Height of USB-C and micro-HDMI port centres above the PCB top. |
| `PI_USB_STACK` | `(17.0, 14.5, 15.9)` | VERIFIED height (official STEP); length and width ASSUMED. |
| `PI_ETH_BOX` | `(21.0, 16.0, 13.5)` | Ethernet length (along BY), width (along BX), height. |
| `COOLER_SIZE` | `(40.0, 40.0, 15.0)` | Active Cooler footprint and height above the PCB top. |
| `COOLER_BX` | `34.0` |  |
| `COOLER_BY` | `26.0` |  |
| `PERF_X` | `90.0` | Perfboard size along X (7 x 9 cm board, long side along X). |
| `PERF_Y` | `70.0` |  |
| `PERF_T` | `1.6` |  |
| `PERF_HOLE_INSET` | `4.0` |  |
| `ULN_SIZE` | `(19.5, 6.5, 4.6)` | ULN2003 DIP-16 length, width, height. |
| `BREAKOUT_SIZE` | `(52.0, 22.0, 8.0)` | GPIO ribbon breakout board. |
| `LIMIT_BUTTON` | `300.0` | Max length of a button wire (wiring table rule: under 30 cm). |
| `LIMIT_LED_IN` | `200.0` | Max length of a GPIO-to-ULN2003 LED wire (rule: under 20 cm). |
| `LIMIT_LED_OUT` | `300.0` | Max length of a ULN2003 output to LED wire (not in the table; same as buttons). |
| `LIMIT_POWER` | `300.0` | Max length of 5V and GND wires. |
| `RIBBON_LEN` | `150.0` | GPIO ribbon cable length available. |
| `HDMI_MINI_LEN` | `500.0` | Cable length from Pi micro-HDMI 1 to the mini screen (wiring table: 0.5 m). |

<!-- ASSUMED:END -->
