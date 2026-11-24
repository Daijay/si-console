"""Wire and cable routes (polylines in world coordinates), colour-coded to the wiring table."""
import math

import params as P
import geo

T = P.T

COLOURS = {"green": (0.1, 0.8, 0.2), "red": (0.9, 0.1, 0.1), "yellow": (1.0, 0.85, 0.1), "white": (0.97, 0.97, 0.97),
           "orange": (1.0, 0.5, 0.0), "blue": (0.15, 0.35, 1.0), "grey": (0.6, 0.6, 0.62), "black": (0.08, 0.08, 0.08)}

TRUNK_B_X = 147.0     # centre of the button-wire bundle running toward the strip
TRUNK_B_PITCH = 2.4
TRUNK_B_Y_RUN = 96.0  # first sideways run in front of the screen stand props
LED_TRUNK_X_END = 191.0
LED_LANE_Y0 = 128.0
LED_LANE_PITCH = 2.2
Z_LOW = 4.5


def plen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def _button_end(u, rear):
    return geo.strip_pt(u, T + rear, P.BTN_V), geo.strip_pt(u, T + rear + 18, P.BTN_V)


def button_wires():
    ends = [("G", "green", P.GREEN_U, P.ARCADE_REAR), ("R", "red", P.RED_U, P.ARCADE_REAR), ("K", "yellow", P.KILL_U, P.KILL_REAR),
            ("PTT", "white", P.PTT_U, P.PTT_REAR), ("LANG", "orange", P.TOGGLE_U, P.TOGGLE_REAR), ("GND", "black", P.KILL_U + 12, P.KILL_REAR)]
    out = []
    # wires leaving to the left cross to the left, to the right cross right; order lanes so they do not tangle
    for i, (nm, col, u, rear) in enumerate(ends):
        pad = geo.breakout_pad(1 + i)
        lane_x = TRUNK_B_X + TRUNK_B_PITCH * (i - 2.5)
        y_run = TRUNK_B_Y_RUN - 2.4 * i
        P_end, A = _button_end(u, rear) if nm != "GND" else _button_end(P.KILL_U, P.KILL_REAR)
        if nm == "GND":
            # twisted pair with the kill switch wire: ends beside it
            P_end = (P_end[0] + 4, P_end[1], P_end[2]); A = (A[0] + 4, A[1], A[2])
        pts = [pad, (pad[0], pad[1] - 4, Z_LOW), (lane_x, 146.0, Z_LOW), (lane_x, y_run, Z_LOW), (A[0], y_run, Z_LOW), A, P_end]
        out.append(dict(name=nm, colour=col, r=P.WIRE_R, pts=pts, limit=P.LIMIT_BUTTON, group="button wires (breakout to controls)"))
    return out


def led_in_wires():
    names = [("COORD", "green"), ("AGENT 1", "white"), ("AGENT 2", "blue"), ("GUARD", "yellow"), ("GRN LED", "green"), ("RED LED", "red")]
    out = []
    for i, (nm, col) in enumerate(names):
        pad = geo.breakout_pad(8 + i)
        pin = geo.uln_in(1 + i)
        # IN row is the front row of the ULN2003 (toward the breakout)
        pin = (pin[0], P.PERF_CY - 3.81, pin[2])
        yl = LED_LANE_Y0 + LED_LANE_PITCH * i
        z_hi = geo.perf_top_z() + 2.0
        pts = [pad, (pad[0], pad[1] - 3, Z_LOW), (pad[0], yl, Z_LOW), (LED_TRUNK_X_END, yl, Z_LOW), (LED_TRUNK_X_END, yl, z_hi),
               (pin[0], yl, z_hi), (pin[0], pin[1], z_hi), pin]
        out.append(dict(name=nm, colour=col, r=P.WIRE_R, pts=pts, limit=P.LIMIT_LED_IN, group="LED wires (breakout to ULN2003 inputs)"))
    return out


def led_out_wires():
    out = []
    x0 = P.STRIP_W / 2 - 1.5 * P.LED_PITCH
    for i, nm in enumerate(P.LED_NAMES):
        u = x0 + i * P.LED_PITCH
        pin = geo.uln_out(1 + i)
        pin = (pin[0], P.PERF_CY + 3.81, pin[2])
        P_end = geo.strip_pt(u, T + P.LED_REAR, P.LED_V)
        A = geo.strip_pt(u, T + P.LED_REAR + 18, P.LED_V)
        yc = 140.0 + 2.4 * i
        pts = [pin, (pin[0], pin[1], 26.0 + 2 * i), (pin[0], yc, 26.0 + 2 * i), (220.0 - 2.4 * i, yc, 26.0 + 2 * i), A, P_end]
        out.append(dict(name=nm.upper() + " LED", colour=P.LED_COLOURS[i], r=P.WIRE_R, pts=pts, limit=P.LIMIT_LED_OUT,
                        group="LED wires (ULN2003 outputs to LEDs)"))
    return out


def power_wires():
    hx, hy = geo.pi_world(P.PI_GPIO_BX, P.PI_GPIO_BY)
    hz = geo.pi_pcb_top_z() + P.PI_GPIO_H
    out = []
    for nm, col, dx, yy, zz in (("5V", "red", -20.0, 146.0, 33.0), ("GND PWR", "black", -17.5, 144.0, 31.0)):
        start = (hx + dx, hy, hz)
        end = (P.PERF_CX - P.PERF_X / 2 + 4, P.PERF_CY - P.PERF_Y / 2 + 4 + (0 if nm == "5V" else 3), geo.perf_top_z() + 0.6)
        pts = [start, (start[0], start[1], zz), (start[0], yy, zz), (end[0] - 6, yy, zz), (end[0] - 6, end[1], zz), (end[0] - 6, end[1], end[2] + 1), end]
        out.append(dict(name=nm, colour=col, r=P.WIRE_R, pts=pts, limit=P.LIMIT_POWER, group="power (Pi header to perfboard)"))
    p7 = geo.uln_in(7)
    p7 = (p7[0], P.PERF_CY - 3.81, p7[2])
    out.append(dict(name="IN7", colour="grey", r=P.WIRE_R, pts=[p7, (p7[0], p7[1], p7[2] + 6), (p7[0] + 12, p7[1] - 6, p7[2] + 6), (p7[0] + 12, p7[1] - 6, p7[2])],
                    limit=50.0, group="ULN2003 IN7 tied to GND"))
    return out


def ribbon():
    hx, hy = geo.pi_world(P.PI_GPIO_BX, P.PI_GPIO_BY)
    hz = geo.pi_pcb_top_z() + P.PI_GPIO_H
    bx0 = P.BREAKOUT_CX - P.BREAKOUT_SIZE[0] / 2
    end = (bx0 + 3, P.BREAKOUT_CY, geo.breakout_top_z() + 1)
    pts = [(hx, hy, hz), (hx, hy, hz + 5), (bx0 - 6, hy + 2, hz + 5), (bx0 - 1, P.BREAKOUT_CY - 2, geo.breakout_top_z() + 6), end]
    return [dict(name="GPIO ribbon", colour="grey", r=P.RIBBON_R, pts=pts, limit=P.RIBBON_LEN, group="GPIO ribbon (Pi header to breakout)")]


def cables():
    z = geo.pi_pcb_top_z() + P.PI_PORT_Z
    ye = P.PI_PORT_EDGE_Y + P.PI_EDGE_OVERHANG
    h0 = geo.pi_world(P.PI_HDMI0_BX, 0)[0]
    h1 = geo.pi_world(P.PI_HDMI1_BX, 0)[0]
    uc = geo.pi_world(P.PI_USBC_BX, 0)[0]
    ux, uy = geo.pi_world(P.PI_L, P.PI_USB_BY[0])
    out = []
    out.append(dict(name="HDMI MAIN", colour="black", r=P.CABLE_R, limit=1000.0, group="cables out of the Pi",
                    pts=[(h0, ye, z), (h0, ye + 25, z), (h0 - 6, ye + 45, z + 8), (h0 - 40, P.BASE_D + P.MON_GAP + 10, 60)]))
    out.append(dict(name="USB-C POWER", colour="black", r=P.CABLE_R, limit=1200.0, group="cables out of the Pi",
                    pts=[(uc, ye, z), (uc, ye + 22, z), (uc + 6, ye + 45, z - 4), (uc + 40, P.BASE_D + 60, -P.FOOT_H + 2)]))
    out.append(dict(name="USB MIC", colour="black", r=P.CABLE_R, limit=1000.0, group="cables out of the Pi",
                    pts=[(ux - P.PI_PORT_OVERHANG, uy, geo.pi_pcb_top_z() + 7), (ux - 30, uy, geo.pi_pcb_top_z() + 7), (ux - 48, uy + 20, geo.pi_pcb_top_z() + 3),
                         (ux - 60, uy + 70, -P.FOOT_H + 2)]))
    fr = geo.plate_frame()
    end = geo.local_to_world(fr, 25.0, -9.0, 12.0)
    out.append(dict(name="HDMI MINI", colour="black", r=P.CABLE_R, limit=P.HDMI_MINI_LEN, group="cables out of the Pi",
                    pts=[(h1, ye, z), (h1, ye + 14, z), (h1, ye + 14, 40.0), (end[0] + 5, 140.0, 40.0), (end[0], 88.0, 40.0), end]))
    return out


def all_wires():
    return ribbon() + button_wires() + led_in_wires() + led_out_wires() + power_wires() + cables()


def tie_pairs():
    """(cx, cy, along, span) cable-tie slot pairs. `along` is the wire direction; span is the bundle width."""
    out = []
    bw = TRUNK_B_PITCH * 5 + 2 * P.WIRE_R
    for y in (136.0, 124.0, 110.0):
        out.append((TRUNK_B_X, y, "y", bw))
    lw = LED_LANE_PITCH * 5 + 2 * P.WIRE_R
    out.append((186.0, LED_LANE_Y0 + LED_LANE_PITCH * 2.5, "x", lw))
    return out
