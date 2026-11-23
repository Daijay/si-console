"""SI Console, Rev R4: every dimension and every switch lives in this file.

Change a number here, run `python build.py`, and every part, drawing, laser
file, render and check is regenerated.

Each parameter carries a tag in its trailing comment:

  VERIFIED  taken from the brief, from a manufacturer drawing, or from a
            published standard. Safe to cut from.
  ASSUMED   an estimate. MEASURE WITH CALIPERS before cutting. build.py lists
            every ASSUMED parameter in output/ASSUMED.md and marks it on the
            drawings.
  DESIGN    a free layout choice made in this file. Nothing to measure; change
            it if you want something different.

All lengths are millimetres. Coordinates in the assembly: X is left to right
(0 to 360), Y is front to back (0 = front face of the front panel, 240 = back
face of the back panel), Z is up (0 = underside of the bottom panel).
"""

REV = "R4"

# --------------------------------------------------------------------------
# SWITCHES (each current design decision can be flipped here)
# --------------------------------------------------------------------------
SCREEN_MODE = "window_under"  # DESIGN. "window_under": window cut to the visible display only, module screwed UNDER the panel. "bezel": full module cutout plus a printed bezel on top.
INCLUDE_MONITOR = True        # DESIGN. Draw the MSI monitor in the assembly (never a cut part).
ENABLE_FAN = True             # DESIGN. 40 mm exhaust fan mount, high on the back panel.
ENABLE_SIDE_VENTS = True      # DESIGN. Intake vent slots low on both side panels.
ENABLE_SPEAKER_GRILLE = False # DESIGN. Off: sound comes from the monitor over HDMI. True adds a slot grille to the lower front panel (speaker body not modelled).
ENABLE_BOTTOM_VENTS = False   # DESIGN. Off: no vents on the bottom. True adds a slot field under the Pi.

# --------------------------------------------------------------------------
# CASE (clear acrylic, finger joints)
# --------------------------------------------------------------------------
CASE_W = 360.0   # VERIFIED (brief). Outer width, X.
CASE_D = 240.0   # VERIFIED (brief). Outer depth, Y.
CASE_H = 140.0   # VERIFIED (brief). Outer height, Z.
T = 3.0          # ASSUMED. Acrylic thickness as delivered (brief says 3 mm, cast sheet varies 2.9 to 3.2). Finger fit depends on it.
KERF = 0.2       # VERIFIED (brief). Laser kerf. DXF cut paths are offset by KERF/2 so finished parts come out at nominal size.
FINGER_W = 15.0  # VERIFIED (brief). Target finger width. Each edge gets an odd number of equal fingers closest to this.

# Laser sheet (12 x 16 inch)
SHEET_W = 305.0       # VERIFIED (brief). 12 in, rounded down from 304.8 would be tighter; brief says 305.
SHEET_L = 406.0       # VERIFIED (brief). 16 in.
SHEET_MARGIN = 5.0    # DESIGN. Unused border on every sheet.
NEST_GAP = 5.0        # DESIGN. Spacing between nested parts.

# Hole rules enforced by the checks
MIN_EDGE_GAP = 5.0    # VERIFIED (brief). Min distance from a hole to any panel edge.
MIN_HOLE_GAP = 5.0    # VERIFIED (brief). Min distance between two holes.

# --------------------------------------------------------------------------
# MINI SCREEN: Waveshare 5inch HDMI LCD (H)
# --------------------------------------------------------------------------
SCREEN_MODULE_W = 121.0     # VERIFIED (brief). Module width.
SCREEN_MODULE_D = 89.48     # VERIFIED (brief). Module depth.
SCREEN_MODULE_H = 13.0      # ASSUMED. Module thickness incl. glass and rear connectors; check the Waveshare drawing.
SCREEN_VIS_W = 109.0        # ASSUMED. Visible display width (brief: about 109). Check the Waveshare drawing.
SCREEN_VIS_D = 66.0         # ASSUMED. Visible display height (brief: about 66). Check the Waveshare drawing.
SCREEN_VIS_OFFSET_X = 0.0   # ASSUMED. Visible area centre offset from module centre, X. Real modules are often off-centre.
SCREEN_VIS_OFFSET_Y = 0.0   # ASSUMED. Visible area centre offset from module centre, Y.
SCREEN_HOLE_INSET = 3.5     # ASSUMED. Module mounting hole centre, distance from each module edge.
SCREEN_HOLE_D = 2.7         # DESIGN. Clearance hole for an M2.5 screw.
SCREEN_GAP = 3.0            # ASSUMED. Space between panel underside and module top face (printed spacer length).
SCREEN_CX = 180.0           # DESIGN. Module centre X in the case.
SCREEN_CY = 100.0           # DESIGN. Module centre Y (from the front).
SCREEN_BEZEL_CLEARANCE = 0.5  # DESIGN. Bezel mode: extra cutout clearance around the full module.
BEZEL_WALL = 7.0            # DESIGN. Bezel mode: printed frame width beyond the cutout.
BEZEL_T = 3.0               # DESIGN. Bezel mode: printed frame thickness.
BEZEL_BOSS_D = 5.0          # DESIGN. Bezel mode: screw boss diameter under the bezel.

# --------------------------------------------------------------------------
# MAIN MONITOR: MSI PRO MP165 E6 (assembly only)
# --------------------------------------------------------------------------
MON_W = 356.5      # VERIFIED (brief).
MON_H = 210.35     # VERIFIED (brief).
MON_T = 13.85      # VERIFIED (brief).
MON_TILT = 15.0    # ASSUMED. Kickstand tilt from vertical, degrees.
MON_GAP = 45.0     # DESIGN. Desk gap between the back of the case and the monitor's lowest front edge (also the exhaust air gap).

# --------------------------------------------------------------------------
# FRONT PANEL CONTROLS (positions are on the front face, X from the left edge
# of the case, Z from the underside of the bottom panel; hole = cut diameter)
# --------------------------------------------------------------------------
BTN_Z = 62.0       # DESIGN. Height of the button row.
LED_Z = 100.0      # DESIGN. Height of the LED row (above the buttons).

GREEN_X = 64.0     # DESIGN.
GREEN_BODY = 30.0  # VERIFIED (brief). 30 mm arcade button.
GREEN_HOLE = 30.2  # VERIFIED (brief).
RED_X = 124.0      # DESIGN.
RED_BODY = 30.0    # VERIFIED (brief).
RED_HOLE = 30.2    # VERIFIED (brief).
KILL_X = 199.0     # DESIGN.
KILL_BODY = 22.0   # VERIFIED (brief). 22 mm kill switch.
KILL_HOLE = 22.3   # VERIFIED (brief).
PTT_X = 259.0      # DESIGN.
PTT_BODY = 12.0    # VERIFIED (brief). Push-to-talk.
PTT_HOLE = 12.2    # VERIFIED (brief).
TOGGLE_X = 304.0   # DESIGN. EN/ZH toggle.
TOGGLE_BODY = 12.0 # VERIFIED (brief).
TOGGLE_HOLE = 12.2 # VERIFIED (brief).

LED_BODY = 5.0     # VERIFIED (brief). 5 mm LEDs.
LED_HOLE = 5.2     # VERIFIED (brief).
LED_PITCH = 30.0   # DESIGN. Spacing of the 4 LEDs, centred on the panel.
LED_COLOURS = ["green", "white", "blue", "yellow"]  # VERIFIED (brief). Left to right: COORD, AGENT 1, AGENT 2, GUARD.
LED_NAMES = ["coord", "agent1", "agent2", "guard"]  # DESIGN.

# Clear space required behind the front panel (measured from its inner face)
CLEAR_ARCADE = 50.0   # VERIFIED (brief). Behind the green and red buttons.
CLEAR_KILL = 75.0     # VERIFIED (brief). Behind the kill switch.
CLEAR_PTT = 30.0      # DESIGN. Behind PTT and toggle (not in the brief; own bodies are shorter).
CLEAR_MARGIN = 5.0    # DESIGN. Sideways margin added around each control's footprint for the clear-space box.

# Control body models (used for the assembly and the clearance check)
BTN_FLANGE_D = 36.0   # ASSUMED. Arcade button front flange diameter.
BTN_CAP_PROUD = 10.0  # ASSUMED. Arcade cap height in front of the panel.
BTN_BODY_CLEAR = 0.4  # DESIGN. Body is this much smaller than the hole (total, diameter).
ARCADE_REAR = 30.0    # ASSUMED. Arcade body depth behind the panel inner face (incl. microswitch).
KILL_HEAD_D = 40.0    # ASSUMED. Kill switch mushroom head diameter.
KILL_HEAD_H = 22.0    # ASSUMED. Kill switch head height in front of the panel.
KILL_REAR = 55.0      # ASSUMED. Kill switch body depth behind the panel inner face.
PTT_HEAD_D = 14.0     # ASSUMED.
PTT_HEAD_H = 6.0      # ASSUMED.
PTT_REAR = 20.0       # ASSUMED.
TOGGLE_LEVER_D = 4.0  # ASSUMED.
TOGGLE_LEVER_H = 15.0 # ASSUMED.
TOGGLE_REAR = 20.0    # ASSUMED.
LED_FLANGE_D = 5.9    # ASSUMED. LED rim, sits behind the panel.
LED_DOME_PROUD = 1.0  # ASSUMED. LED dome in front of the panel.
LED_REAR = 8.0        # ASSUMED. LED body behind the panel.

# Speaker grille (only when ENABLE_SPEAKER_GRILLE)
GRILLE_Z = 25.0       # DESIGN.
GRILLE_SLOT_W = 3.0   # DESIGN.
GRILLE_SLOT_L = 40.0  # DESIGN.
GRILLE_COUNT = 8      # DESIGN.
GRILLE_PITCH = 20.0   # DESIGN.

# --------------------------------------------------------------------------
# RASPBERRY PI 5 + Active Cooler (official mechanical drawing, rev 2026)
# --------------------------------------------------------------------------
PI_L = 85.0               # VERIFIED (brief, official drawing). Board length.
PI_W = 56.0               # VERIFIED (brief, official drawing). Board width.
PI_PCB_T = 1.6            # VERIFIED. Standard PCB thickness.
PI_HOLE_SX = 58.0         # VERIFIED (brief, official drawing). Hole spacing along the length.
PI_HOLE_SY = 49.0         # VERIFIED (brief, official drawing). Hole spacing along the width.
PI_HOLE_INSET = 3.5       # VERIFIED (brief, official drawing). Hole centre from board edges.
PI_HOLE_D = 2.7           # VERIFIED (official drawing). Board hole diameter, M2.5.
PI_STANDOFF_H = 10.0      # VERIFIED (brief). M2.5 standoff height.
PI_STANDOFF_D = 5.0       # DESIGN. Standoff outer diameter.
# Port positions measured on the official drawing, in board coordinates
# (BX from the left edge, BY from the long edge that carries the power and HDMI ports)
PI_USBC_BX = 11.2         # VERIFIED (official drawing). USB-C power centre along the long edge.
PI_HDMI0_BX = 25.8        # VERIFIED (official drawing). micro-HDMI 0.
PI_HDMI1_BX = 39.2        # VERIFIED (official drawing). micro-HDMI 1.
PI_USB_BY = (29.1, 47.0)  # VERIFIED (official drawing). Centres of the two USB stacks, measured from the HDMI long edge.
PI_ETH_BY = 10.2          # VERIFIED (official drawing). Ethernet centre, measured from the HDMI long edge.
PI_PORT_Z = 1.7           # ASSUMED. Height of the USB-C and micro-HDMI port centres above the PCB top.
PI_USB_STACK = (17.0, 14.5, 15.9)  # VERIFIED height (official STEP, top at 17.5 above PCB underside); length and width ASSUMED.
PI_ETH_BOX = (21.0, 16.0, 13.5)    # ASSUMED. Ethernet length (along BY), width (along BX, inside board), height.
PI_PORT_OVERHANG = 3.0    # VERIFIED (official STEP bbox: 88.05 vs 85). How far the USB/Ethernet shells hang past the short edge.
PI_EDGE_OVERHANG = 1.6    # VERIFIED (official STEP bbox: -1.63). How far the USB-C/HDMI shells hang past the long edge.
PI_GPIO_BX = 32.5         # VERIFIED (official drawing). GPIO header centre along the length.
PI_GPIO_BY = 52.5         # VERIFIED (standard 40-pin position). GPIO header centre from the HDMI long edge.
PI_GPIO_H = 8.5           # VERIFIED. Header height above PCB.
COOLER_SIZE = (40.0, 40.0, 15.0)   # ASSUMED. Active Cooler footprint X, Y and height above the PCB top.
COOLER_BX = 34.0          # ASSUMED. Cooler centre along the length.
COOLER_BY = 26.0          # ASSUMED. Cooler centre from the HDMI long edge.

# Placement. The board is rotated 180 degrees so its long power/HDMI edge faces
# the back panel and the GPIO header faces the front (toward the perfboard).
# That puts the USB/Ethernet end against the LEFT wall.
PI_X0 = 38.0              # DESIGN. World X of the board's left edge.
PI_BACK_GAP = 65.0        # DESIGN. Gap from the Pi power/HDMI edge to the inner face of the back panel (room for plugs and bends).

# --------------------------------------------------------------------------
# PERFBOARD, ULN2003, GPIO BREAKOUT
# --------------------------------------------------------------------------
PERF_X = 70.0             # ASSUMED. Perfboard size along X (7 x 9 cm board).
PERF_Y = 90.0             # ASSUMED. Perfboard size along Y.
PERF_T = 1.6              # ASSUMED.
PERF_HOLE_INSET = 4.0     # ASSUMED. Mounting hole inset from each edge.
PERF_HOLE_D = 3.2         # DESIGN. M3 clearance.
PERF_STANDOFF_H = 10.0    # VERIFIED (brief). M3 standoff height.
PERF_STANDOFF_D = 6.0     # DESIGN.
PERF_CX = 180.0           # DESIGN. Perfboard centre X (centre of the case).
PERF_CY = 125.0           # DESIGN. Perfboard centre Y.
ULN_SIZE = (19.5, 6.5, 4.6)  # ASSUMED. ULN2003 DIP-16 length, width, height.
BREAKOUT_SIZE = (52.0, 22.0, 8.0)  # ASSUMED. GPIO ribbon breakout board.
BREAKOUT_CX = 90.0        # DESIGN. Between the Pi header and the perfboard.
BREAKOUT_CY = 96.0        # DESIGN.
GPIO_RIBBON_LEN = 150.0   # ASSUMED. Ribbon cable length available.

# --------------------------------------------------------------------------
# BOTTOM PANEL
# --------------------------------------------------------------------------
FOOT_D = 15.0         # ASSUMED. Rubber foot diameter.
FOOT_H = 6.0          # ASSUMED. Rubber foot height.
FOOT_HOLE_D = 4.2     # ASSUMED. Foot screw hole (M4).
FOOT_INSET = 30.0     # DESIGN. Foot centre distance from the two nearest outer edges.
BOTTOM_VENT_Y = 60.0  # DESIGN. Only used when ENABLE_BOTTOM_VENTS.

# --------------------------------------------------------------------------
# BACK PANEL: cable cutouts and fan (positions are world X, so inside the case
# they line up with what is in front of them)
# --------------------------------------------------------------------------
CUT_Z = 24.0           # DESIGN. Centre height of the cable cutouts.
HDMI_CUT = (24.0, 12.0)   # ASSUMED. micro-HDMI to HDMI adapter cable, plug passes through. Width, height.
USBC_CUT = (18.0, 10.0)   # ASSUMED. Pi USB-C power plug passes through.
MIC_CUT = (16.0, 10.0)    # ASSUMED. USB-A plug of the mic cable passes through.
HDMI0_CUT_X = 98.0     # DESIGN. Cutout for the cable from micro-HDMI 0.
HDMI1_CUT_X = 68.0     # DESIGN. Cutout for the cable from micro-HDMI 1.
USBC_CUT_X = 127.0     # DESIGN.
MIC_CUT_X = 38.0       # DESIGN.

FAN_SIZE = 40.0           # VERIFIED (brief). 40 mm fan.
FAN_T = 10.0              # ASSUMED. Fan thickness.
FAN_HOLE_SPACING = 32.0   # VERIFIED (brief). Screw hole spacing.
FAN_SCREW_D = 3.4         # DESIGN. M3 clearance.
FAN_OPENING_D = 31.0      # DESIGN. Airflow opening. Limited to 31 so it keeps 5 mm to the screw holes; raise it and the hole-gap check fails.
FAN_CX = 90.0             # DESIGN. World X of the fan centre.
FAN_CZ = 110.0            # DESIGN. High on the back.

# Cable reach rules (used by the checks)
HDMI_PLUG_LEN = 25.0      # ASSUMED. Straight, stiff length of a micro-HDMI plug plus strain relief.
USBC_PLUG_LEN = 22.0      # ASSUMED. Same for the USB-C power plug.
CABLE_MIN_BEND_R = 20.0   # ASSUMED. Smallest comfortable cable bend radius.
CABLE_MAX_EXIT_ANGLE = 45.0   # DESIGN. Steepest angle a cable may leave its plug axis, degrees.
USB_PLUG_CLEAR = 30.0     # ASSUMED. Room needed left of the Pi for the mic USB-A plug.
MIC_CABLE_LEN = 500.0     # ASSUMED. Mic cable length available inside the case.

# --------------------------------------------------------------------------
# SIDE VENTS (intake, low on both sides)
# --------------------------------------------------------------------------
VENT_SLOT_W = 4.0              # DESIGN.
VENT_SLOT_L = 40.0             # DESIGN.
VENT_ROWS_Z = (17.0, 29.0)     # DESIGN. Row centre heights.
VENT_COLS_U = (50.0, 100.0, 150.0, 200.0)  # DESIGN. Slot centres along the side panel (outside view, from its left edge).

# --------------------------------------------------------------------------
# PRINTED PARTS AND RENDERING
# --------------------------------------------------------------------------
SPACER_OD = 5.0           # DESIGN. Printed screen spacer outer diameter.
RENDER_SIZE = (1600, 1100)  # DESIGN. PNG size in pixels.
