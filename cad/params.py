"""SI Console, Rev R5 (open frame "cyberdeck"): every dimension and switch lives in this file.

No enclosure. One clear acrylic base plate carries everything. A sloped control
strip stands at the front on two brackets, a small angled stand holds the mini
screen, and the Pi, perfboard and wiring sit fully exposed on the base.

Change a number here, run `python build.py`, and every part, laser file, drawing,
render and check is regenerated.

Each parameter carries a tag in its trailing comment:

  VERIFIED  from the brief, a manufacturer drawing, or a published standard.
  ASSUMED   an estimate. MEASURE WITH CALIPERS before cutting. build.py lists
            every ASSUMED parameter in output/ASSUMED.md and marks it on the drawings.
  DESIGN    a free layout choice made in this file. Nothing to measure.

All lengths are millimetres. Assembly axes: X left to right, Y front to back
(0 = front edge of the base plate), Z up (0 = underside of the base plate).
"""

REV = "R5"

# --------------------------------------------------------------------------
# SWITCHES
# --------------------------------------------------------------------------
INCLUDE_MONITOR = True   # DESIGN. Draw the MSI monitor behind the base (assembly only, never cut).
INCLUDE_WIRES = True     # DESIGN. Draw colour-coded wire tubes.
ENABLE_TIE_SLOTS = True  # DESIGN. Cable-tie slot pairs in the base plate along the wire routes.

# --------------------------------------------------------------------------
# LASER MATERIAL AND RULES
# --------------------------------------------------------------------------
T = 3.0          # ASSUMED. Acrylic thickness as delivered (cast sheet varies 2.9 to 3.2). Tab and slot fit depends on it.
KERF = 0.2       # VERIFIED (brief). DXF cut paths are offset by KERF/2 so parts finish at nominal size.
SHEET_W = 305.0  # VERIFIED (brief). 12 in.
SHEET_L = 406.0  # VERIFIED (brief). 16 in.
SHEET_MARGIN = 4.0   # DESIGN. Unused border on every sheet.
NEST_GAP = 5.0       # DESIGN. Spacing between nested parts.
MIN_EDGE_GAP = 5.0   # VERIFIED (brief). Min distance from a hole to any part edge.
MIN_HOLE_GAP = 5.0   # VERIFIED (brief). Min distance between two holes.
PART_MARGIN = 15.0   # VERIFIED (brief). Margin between everything on the base and the base edge (plugs and cables may hang off the edge).

# --------------------------------------------------------------------------
# BASE PLATE
# --------------------------------------------------------------------------
BASE_W = 330.0       # ASSUMED. Base plate width: the 300 mm strip plus 15 mm margins each side.
BASE_D = 220.0       # ASSUMED. Base plate depth.
BASE_RADIUS = 12.0   # DESIGN. Corner radius.
FOOT_D = 15.0        # ASSUMED. Rubber foot diameter.
FOOT_H = 6.0         # ASSUMED. Rubber foot height.
FOOT_HOLE_D = 4.2    # ASSUMED. Foot screw hole (M4).
FOOT_INSET = 22.5    # DESIGN. Foot centre distance from the two nearest edges.
TIE_SLOT = (3.0, 5.0)    # VERIFIED (brief). Cable-tie slot size, width x length.
TIE_PAIR_GAP = 6.0       # DESIGN. Material between the two slots of a tie pair (the strap goes through both).

# --------------------------------------------------------------------------
# CONTROL STRIP (sloped, at the front)
# --------------------------------------------------------------------------
STRIP_X0 = 15.0       # DESIGN. X of the strip's left edge (centres the 300 mm strip on the base).
STRIP_W = 300.0      # ASSUMED. Strip width ("about 300").
STRIP_H = 70.0       # ASSUMED. Strip height ("about 80", trimmed so base plus strip share one 305 mm sheet).
STRIP_RADIUS = 4.0   # DESIGN. Corner radius.
STRIP_TILT = 20.0    # VERIFIED (brief). Slope in degrees, measured from vertical, leaning back so the face looks up at the user.
STRIP_Y = 34.0       # DESIGN. Y of the bottom edge of the strip's front face.
STRIP_Z = 26.0       # DESIGN. Height of that bottom edge above the underside of the base (lets the kill switch zone clear the base).
BRACKET_U = (15.0, 285.0)   # DESIGN. Bracket positions across the strip.
BRACKET_FOOT = 40.0  # DESIGN. How far a bracket's base extends behind its strip contact.
BRACKET_V = (5.0, 65.0)     # DESIGN. Span of the strip rear face that a bracket touches.
BRACKET_TABS_V = ((8.0, 23.0), (47.0, 62.0))  # DESIGN. Tab positions along the strip (15 mm tabs).

# Control positions on the strip face: U from its left edge, V up from its bottom edge
BTN_V = 26.0       # DESIGN. Height of the button row.
LED_V = 56.0       # DESIGN. Height of the LED row (above the buttons).
GREEN_U = 50.0     # DESIGN.
GREEN_BODY = 30.0  # VERIFIED (brief). 30 mm arcade button.
GREEN_HOLE = 30.2  # VERIFIED (brief).
RED_U = 105.0      # DESIGN.
RED_BODY = 30.0    # VERIFIED (brief).
RED_HOLE = 30.2    # VERIFIED (brief).
KILL_U = 165.0     # DESIGN.
KILL_BODY = 22.0   # VERIFIED (brief). 22 mm kill switch.
KILL_HOLE = 22.3   # VERIFIED (brief).
PTT_U = 220.0      # DESIGN.
PTT_BODY = 12.0    # VERIFIED (brief). Push-to-talk.
PTT_HOLE = 12.2    # VERIFIED (brief).
TOGGLE_U = 260.0   # DESIGN. EN/ZH toggle.
TOGGLE_BODY = 12.0 # VERIFIED (brief).
TOGGLE_HOLE = 12.2 # VERIFIED (brief).
LED_BODY = 5.0     # VERIFIED (brief). 5 mm LEDs.
LED_HOLE = 5.2     # VERIFIED (brief).
LED_PITCH = 30.0   # DESIGN. Spacing of the 4 LEDs, centred on the strip.
LED_COLOURS = ["green", "white", "blue", "yellow"]  # VERIFIED (brief). Left to right: COORD, AGENT 1, AGENT 2, GUARD.
LED_NAMES = ["coord", "agent1", "agent2", "guard"]  # DESIGN.

CLEAR_ARCADE = 50.0   # VERIFIED (brief). Clear space behind the green and red buttons, measured along the button axis from the strip's rear face.
CLEAR_KILL = 75.0     # VERIFIED (brief). Behind the kill switch.
CLEAR_PTT = 30.0      # DESIGN. Behind PTT and toggle (not in the brief).
CLEAR_MARGIN = 5.0    # DESIGN. Sideways margin added around each control for the clear-space box.

# Control body models
BTN_FLANGE_D = 36.0   # ASSUMED. Arcade button front flange diameter.
BTN_CAP_PROUD = 10.0  # ASSUMED. Arcade cap height in front of the strip.
BTN_BODY_CLEAR = 0.4  # DESIGN. Body is this much smaller than the hole (diameter).
ARCADE_REAR = 30.0    # ASSUMED. Arcade body depth behind the strip (incl. microswitch).
KILL_HEAD_D = 40.0    # ASSUMED. Kill switch mushroom head diameter.
KILL_HEAD_H = 22.0    # ASSUMED. Kill switch head height in front of the strip.
KILL_REAR = 55.0      # ASSUMED. Kill switch body depth behind the strip.
PTT_HEAD_D = 14.0     # ASSUMED.
PTT_HEAD_H = 6.0      # ASSUMED.
PTT_REAR = 20.0       # ASSUMED.
TOGGLE_LEVER_D = 4.0  # ASSUMED.
TOGGLE_LEVER_H = 15.0 # ASSUMED.
TOGGLE_REAR = 20.0    # ASSUMED.
LED_FLANGE_D = 5.9    # ASSUMED. LED rim, sits behind the strip.
LED_DOME_PROUD = 1.0  # ASSUMED.
LED_REAR = 8.0        # ASSUMED.

# --------------------------------------------------------------------------
# MINI SCREEN: Waveshare 5inch HDMI LCD (H) on an angled stand
# --------------------------------------------------------------------------
SCREEN_MODULE_W = 121.0   # VERIFIED (brief).
SCREEN_MODULE_D = 89.48   # VERIFIED (brief).
SCREEN_MODULE_H = 13.0    # ASSUMED. Module thickness incl. rear connectors.
SCREEN_HOLE_INSET = 3.5   # ASSUMED. Module mounting hole distance from each module edge.
SCREEN_HOLE_D = 2.7       # DESIGN. M2.5 clearance.
SCREEN_STANDOFF_H = 5.0   # DESIGN. M2.5 standoff between the stand plate and the module.
SCREEN_STANDOFF_D = 5.0   # DESIGN.
SCREEN_TILT = 20.0        # DESIGN. Plate tilt from vertical, leaning back (faces the user).
SCREEN_CX = 165.0         # DESIGN. Plate centre X.
SCREEN_Y = 96.0           # DESIGN. Y of the plate's bottom edge (front face).
SCREEN_Z = 60.0           # DESIGN. Height of that bottom edge above the base underside.
PLATE_W = 150.0           # DESIGN. Screen plate width.
PLATE_H = 114.0           # DESIGN. Screen plate height.
PLATE_MOD_V0 = 18.0       # DESIGN. Module bottom edge, up from the plate bottom.
PLATE_RADIUS = 4.0        # DESIGN.
PROP_U = (7.0, 143.0)     # DESIGN. Prop positions across the plate (at its edges, clear of the module screws).
PROP_V = (6.0, 56.0)      # DESIGN. Span of the plate rear face that a prop touches.
PROP_FOOT = 10.0          # DESIGN. How far a prop's base extends behind its plate contact.
PROP_TABS_V = ((8.0, 23.0), (38.0, 53.0))  # DESIGN. Tab positions along the plate.

# --------------------------------------------------------------------------
# MAIN MONITOR: MSI PRO MP165 E6 (assembly only)
# --------------------------------------------------------------------------
MON_W = 356.5      # VERIFIED (brief).
MON_H = 210.35     # VERIFIED (brief).
MON_T = 13.85      # VERIFIED (brief).
MON_TILT = 15.0    # ASSUMED. Kickstand tilt from vertical.
MON_GAP = 40.0     # DESIGN. Desk gap between the back of the base and the monitor's lowest front edge (cables run through it).

# --------------------------------------------------------------------------
# RASPBERRY PI 5 + Active Cooler (official mechanical drawing and STEP)
# --------------------------------------------------------------------------
PI_L = 85.0               # VERIFIED (brief, official drawing).
PI_W = 56.0               # VERIFIED (brief, official drawing).
PI_PCB_T = 1.6            # VERIFIED.
PI_HOLE_SX = 58.0         # VERIFIED (brief, official drawing).
PI_HOLE_SY = 49.0         # VERIFIED (brief, official drawing).
PI_HOLE_INSET = 3.5       # VERIFIED (brief, official drawing).
PI_HOLE_D = 2.7           # VERIFIED (official drawing).
PI_STANDOFF_H = 10.0      # VERIFIED (brief). M2.5 standoff height.
PI_STANDOFF_D = 5.0       # DESIGN.
PI_USBC_BX = 11.2         # VERIFIED (official drawing). Port positions along the power/HDMI long edge.
PI_HDMI0_BX = 25.8        # VERIFIED (official drawing).
PI_HDMI1_BX = 39.2        # VERIFIED (official drawing).
PI_USB_BY = (29.1, 47.0)  # VERIFIED (official drawing). USB stack centres from the HDMI long edge.
PI_ETH_BY = 10.2          # VERIFIED (official drawing).
PI_PORT_Z = 1.7           # ASSUMED. Height of USB-C and micro-HDMI port centres above the PCB top.
PI_USB_STACK = (17.0, 14.5, 15.9)  # VERIFIED height (official STEP); length and width ASSUMED.
PI_ETH_BOX = (21.0, 16.0, 13.5)    # ASSUMED. Ethernet length (along BY), width (along BX), height.
PI_PORT_OVERHANG = 3.0    # VERIFIED (official STEP). USB/Ethernet overhang past the short edge.
PI_EDGE_OVERHANG = 1.6    # VERIFIED (official STEP). USB-C/HDMI overhang past the long edge.
PI_GPIO_BX = 32.5         # VERIFIED (official drawing). GPIO header centre along the length.
PI_GPIO_BY = 52.5         # VERIFIED (standard 40-pin position). From the HDMI long edge.
PI_GPIO_H = 8.5           # VERIFIED. Header height above PCB.
COOLER_SIZE = (40.0, 40.0, 15.0)   # ASSUMED. Active Cooler footprint and height above the PCB top.
COOLER_BX = 34.0          # ASSUMED.
COOLER_BY = 26.0          # ASSUMED.
# The board is rotated 180 degrees: power and HDMI edge faces the back so the cables leave off the back edge
# of the base; the GPIO header faces the front, toward the breakout; the USB/Ethernet end faces the left.
PI_X0 = 35.0              # DESIGN. World X of the board's left edge.
PI_PORT_EDGE_Y = 203.0    # DESIGN. World Y of the power/HDMI edge (plugs hang past the base back edge at 220).

# --------------------------------------------------------------------------
# PERFBOARD, ULN2003, GPIO BREAKOUT
# --------------------------------------------------------------------------
PERF_X = 90.0             # ASSUMED. Perfboard size along X (7 x 9 cm board, long side along X).
PERF_Y = 70.0             # ASSUMED.
PERF_T = 1.6              # ASSUMED.
PERF_HOLE_INSET = 4.0     # ASSUMED.
PERF_HOLE_D = 3.2         # DESIGN. M3 clearance.
PERF_STANDOFF_H = 10.0    # VERIFIED (brief). M3 standoff height.
PERF_STANDOFF_D = 6.0     # DESIGN.
PERF_CX = 240.0           # DESIGN. Perfboard centre X.
PERF_CY = 170.0           # DESIGN. Perfboard centre Y.
ULN_SIZE = (19.5, 6.5, 4.6)  # ASSUMED. ULN2003 DIP-16 length, width, height.
BREAKOUT_SIZE = (52.0, 22.0, 8.0)  # ASSUMED. GPIO ribbon breakout board.
BREAKOUT_CX = 156.0       # DESIGN. Between the Pi and the perfboard.
BREAKOUT_CY = 161.0       # DESIGN.
BREAKOUT_PAD_PITCH = 4.0  # DESIGN. Pitch of the signal pads along the breakout.

# --------------------------------------------------------------------------
# WIRES (thin tubes, colours follow the wiring table in blueprints/R5/wiring_diagram_R5.svg)
# --------------------------------------------------------------------------
WIRE_R = 0.9              # DESIGN. Wire tube radius.
CABLE_R = 2.5             # DESIGN. HDMI and USB cable tube radius.
RIBBON_R = 3.0            # DESIGN. GPIO ribbon tube radius.
WIRE_SLACK = 1.10         # DESIGN. Extra length over the straight path for bends.
LIMIT_BUTTON = 300.0      # ASSUMED. Max length of a button wire (wiring table rule: under 30 cm).
LIMIT_LED_IN = 200.0      # ASSUMED. Max length of a GPIO-to-ULN2003 LED wire (rule: under 20 cm).
LIMIT_LED_OUT = 300.0     # ASSUMED. Max length of a ULN2003 output to LED wire (not in the table; same as buttons).
LIMIT_POWER = 300.0       # ASSUMED. Max length of 5V and GND wires.
RIBBON_LEN = 150.0        # ASSUMED. GPIO ribbon cable length available.
HDMI_MINI_LEN = 500.0     # ASSUMED. Cable length from Pi micro-HDMI 1 to the mini screen (wiring table: 0.5 m).

# --------------------------------------------------------------------------
# RENDERING
# --------------------------------------------------------------------------
RENDER_SIZE = (1600, 1100)  # DESIGN. PNG size in pixels.
