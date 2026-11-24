"""Component models (buttons, Pi, screen, fan, ...) and the assembly.

Each part is a dict: name, solid (CadQuery shape in world coordinates),
category ("panel", "component", "print", "reference"), colour (RGB 0..1),
alpha, and a short label used on renders.
"""
import math

import cadquery as cq

import params as P
import panels as pn

V = cq.Vector
W, D, H, T = P.CASE_W, P.CASE_D, P.CASE_H, P.T


# ------------------------------------------------------------ primitives --
def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane(obj=cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0)))


def cyl_y(cx, cz, y0, y1, d):
    """Cylinder with its axis along Y from y0 to y1."""
    return cq.Workplane(obj=cq.Solid.makeCylinder(d / 2, y1 - y0, V(cx, y0, cz), V(0, 1, 0)))


def cyl_z(cx, cy, z0, z1, d):
    return cq.Workplane(obj=cq.Solid.makeCylinder(d / 2, z1 - z0, V(cx, cy, z0), V(0, 0, 1)))


def fuse(*items):
    out = items[0]
    for it in items[1:]:
        out = out.union(it)
    return out


def part(name, solid, category, colour, label, alpha=1.0, own_clear=None):
    s = solid.val() if hasattr(solid, "val") else solid
    return dict(name=name, solid=s, category=category, colour=colour, alpha=alpha, label=label)


ACRYLIC = (0.72, 0.88, 0.95)
GREY = (0.55, 0.55, 0.58)
BLACK = (0.12, 0.12, 0.13)
GREEN_PCB = (0.1, 0.45, 0.2)
LED_RGB = {"green": (0.1, 0.9, 0.2), "white": (0.96, 0.96, 0.96), "blue": (0.15, 0.35, 1.0), "yellow": (1.0, 0.85, 0.1)}


# -------------------------------------------------------------- controls --
def arcade(name, x, body_d, hole, colour, label):
    body_d = hole - P.BTN_BODY_CLEAR
    z = P.BTN_Z
    s = fuse(
        cyl_y(x, z, -3.0, 0.0, P.BTN_FLANGE_D),                      # front flange against the panel face
        cyl_y(x, z, -P.BTN_CAP_PROUD, -3.0, body_d),                 # cap
        cyl_y(x, z, 0.0, T + P.ARCADE_REAR, body_d),                 # body through the hole and behind it
        cyl_y(x, z, T, T + 5.0, P.BTN_FLANGE_D))                     # retaining nut on the inner face
    return part(name, s, "component", colour, label)


def front_controls():
    out = []
    out.append(arcade("btn_green", P.GREEN_X, P.GREEN_BODY, P.GREEN_HOLE, (0.1, 0.75, 0.25), "green button"))
    out.append(arcade("btn_red", P.RED_X, P.RED_BODY, P.RED_HOLE, (0.85, 0.12, 0.12), "red button"))

    kd = P.KILL_HOLE - P.BTN_BODY_CLEAR
    kill = fuse(cyl_y(P.KILL_X, P.BTN_Z, -P.KILL_HEAD_H, 0.0, P.KILL_HEAD_D),
                cyl_y(P.KILL_X, P.BTN_Z, 0.0, T + P.KILL_REAR, kd),
                cyl_y(P.KILL_X, P.BTN_Z, T, T + 5.0, P.KILL_BODY + 10))
    out.append(part("kill_switch", kill, "component", (0.8, 0.05, 0.05), "kill switch"))

    pd = P.PTT_HOLE - P.BTN_BODY_CLEAR
    ptt = fuse(cyl_y(P.PTT_X, P.BTN_Z, -P.PTT_HEAD_H, 0.0, P.PTT_HEAD_D),
               cyl_y(P.PTT_X, P.BTN_Z, 0.0, T + P.PTT_REAR, pd),
               cyl_y(P.PTT_X, P.BTN_Z, T, T + 2.0, P.PTT_HEAD_D + 2))
    out.append(part("btn_ptt", ptt, "component", (0.2, 0.2, 0.25), "push to talk"))

    td = P.TOGGLE_HOLE - P.BTN_BODY_CLEAR
    tog = fuse(cyl_y(P.TOGGLE_X, P.BTN_Z, -P.TOGGLE_LEVER_H, 0.0, P.TOGGLE_LEVER_D),
               cyl_y(P.TOGGLE_X, P.BTN_Z, 0.0, T + P.TOGGLE_REAR, td),
               cyl_y(P.TOGGLE_X, P.BTN_Z, T, T + 2.0, P.TOGGLE_HOLE + 2))
    out.append(part("toggle_lang", tog, "component", (0.75, 0.75, 0.78), "EN/ZH toggle"))

    x0 = W / 2 - 1.5 * P.LED_PITCH
    for i, nm in enumerate(P.LED_NAMES):
        x = x0 + i * P.LED_PITCH
        body_d = P.LED_HOLE - P.BTN_BODY_CLEAR / 2
        led = fuse(cyl_y(x, P.LED_Z, -P.LED_DOME_PROUD, T + P.LED_REAR, body_d),
                   cyl_y(x, P.LED_Z, T, T + 1.0, P.LED_FLANGE_D))
        out.append(part(f"led_{nm}", led, "component", LED_RGB[P.LED_COLOURS[i]], f"LED {nm.upper()}"))
    return out


# ------------------------------------------------------------ Raspberry Pi --
def pi_board_local():
    """Pi 5 in board coordinates: X along the 85 mm length from the left edge, Y from the
    power/HDMI long edge, Z up from the PCB underside (PCB occupies 0..1.6)."""
    pcb = cq.Workplane("XY").box(P.PI_L, P.PI_W, P.PI_PCB_T, centered=False)
    for bx in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SX):
        for by in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SY):
            pcb = pcb.cut(cq.Workplane("XY").center(bx, by).circle(P.PI_HOLE_D / 2).extrude(P.PI_PCB_T))
    top = P.PI_PCB_T
    items = [pcb]
    # USB-C power and the two micro-HDMI sockets on the HDMI long edge (by = 0 side)
    items.append(box(P.PI_USBC_BX - 4.5, -P.PI_EDGE_OVERHANG, top, P.PI_USBC_BX + 4.5, 7.3, top + 3.2))
    for bx in (P.PI_HDMI0_BX, P.PI_HDMI1_BX):
        items.append(box(bx - 3.5, -P.PI_EDGE_OVERHANG, top, bx + 3.5, 6.5, top + 3.4))
    # USB stacks and Ethernet on the right short edge
    ul, uw, uh = P.PI_USB_STACK
    for by in P.PI_USB_BY:
        items.append(box(P.PI_L + P.PI_PORT_OVERHANG - ul, by - uw / 2, top, P.PI_L + P.PI_PORT_OVERHANG, by + uw / 2, top + uh))
    el, ew, eh = P.PI_ETH_BOX
    items.append(box(P.PI_L + P.PI_PORT_OVERHANG - ew, max(0.0, P.PI_ETH_BY - el / 2), top,
                     P.PI_L + P.PI_PORT_OVERHANG, P.PI_ETH_BY + el / 2, top + eh))
    # GPIO header
    items.append(box(P.PI_GPIO_BX - 25.4, P.PI_GPIO_BY - 2.5, top, P.PI_GPIO_BX + 25.4, P.PI_GPIO_BY + 2.5, top + P.PI_GPIO_H))
    # Active Cooler
    cx, cy, ch = P.COOLER_SIZE
    items.append(box(P.COOLER_BX - cx / 2, P.COOLER_BY - cy / 2, top, P.COOLER_BX + cx / 2, P.COOLER_BY + cy / 2, top + ch))
    return fuse(*items)


def pi_to_world(shape):
    """Rotate 180 degrees about Z (HDMI edge to the back, GPIO to the front, USB end to the left)
    and place on the standoffs."""
    s = shape.val() if hasattr(shape, "val") else shape
    s = s.rotate(V(0, 0, 0), V(0, 0, 1), 180)
    return cq.Workplane(obj=s.translate(V(P.PI_X0 + P.PI_L, pn.pi_y0() + P.PI_W, T + P.PI_STANDOFF_H)))


def pi_world(bx, by):
    """World (x, y) of a point given in board coordinates."""
    return (P.PI_X0 + P.PI_L - bx, pn.pi_y0() + P.PI_W - by)


def pi_pcb_top_z():
    return T + P.PI_STANDOFF_H + P.PI_PCB_T


# -------------------------------------------------- perfboard and friends --
def perf_pieces():
    z0 = T + P.PERF_STANDOFF_H
    pb = box(P.PERF_CX - P.PERF_X / 2, P.PERF_CY - P.PERF_Y / 2, z0,
             P.PERF_CX + P.PERF_X / 2, P.PERF_CY + P.PERF_Y / 2, z0 + P.PERF_T)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = P.PERF_CX + sx * (P.PERF_X / 2 - P.PERF_HOLE_INSET)
            y = P.PERF_CY + sy * (P.PERF_Y / 2 - P.PERF_HOLE_INSET)
            pb = pb.cut(cyl_z(x, y, z0, z0 + P.PERF_T, P.PERF_HOLE_D))
    L, Wd, Ht = P.ULN_SIZE
    uln = box(P.PERF_CX - L / 2, P.PERF_CY - Wd / 2, z0 + P.PERF_T, P.PERF_CX + L / 2, P.PERF_CY + Wd / 2, z0 + P.PERF_T + Ht)
    return pb, uln


def standoffs():
    out = []
    for bx in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SX):
        for by in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SY):
            x, y = pi_world(bx, by)
            out.append(cyl_z(x, y, T, T + P.PI_STANDOFF_H, P.PI_STANDOFF_D))
    pi_so = fuse(*out)
    out = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = P.PERF_CX + sx * (P.PERF_X / 2 - P.PERF_HOLE_INSET)
            y = P.PERF_CY + sy * (P.PERF_Y / 2 - P.PERF_HOLE_INSET)
            out.append(cyl_z(x, y, T, T + P.PERF_STANDOFF_H, P.PERF_STANDOFF_D))
    return pi_so, fuse(*out)


# --------------------------------------------------------------- screen --
def screen_z_top():
    """Z of the module's top (glass) face."""
    if P.SCREEN_MODE == "window_under":
        return H - T - P.SCREEN_GAP
    return H - T - P.SCREEN_GAP


def screen_parts():
    zt = screen_z_top()
    zb = zt - P.SCREEN_MODULE_H
    mod = box(P.SCREEN_CX - P.SCREEN_MODULE_W / 2, P.SCREEN_CY - P.SCREEN_MODULE_D / 2, zb,
              P.SCREEN_CX + P.SCREEN_MODULE_W / 2, P.SCREEN_CY + P.SCREEN_MODULE_D / 2, zt)
    hole_pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            hole_pts.append((P.SCREEN_CX + sx * (P.SCREEN_MODULE_W / 2 - P.SCREEN_HOLE_INSET),
                             P.SCREEN_CY + sy * (P.SCREEN_MODULE_D / 2 - P.SCREEN_HOLE_INSET)))
    for (x, y) in hole_pts:
        mod = mod.cut(cyl_z(x, y, zb, zt, P.SCREEN_HOLE_D))
    out = [part("mini_screen", mod, "component", (0.05, 0.05, 0.08), "5 in screen")]
    ztop_panel = H - T
    if P.SCREEN_MODE == "window_under":
        sp = [cyl_z(x, y, zt, ztop_panel, P.SPACER_OD).cut(cyl_z(x, y, zt, ztop_panel, P.SCREEN_HOLE_D)) for (x, y) in hole_pts]
        out.append(part("screen_spacer", fuse(*sp), "print", (0.9, 0.55, 0.1), "screen spacers (x4)"))
    else:
        bz0 = H  # bezel sits on top of the panel
        cut_w = P.SCREEN_MODULE_W + 2 * P.SCREEN_BEZEL_CLEARANCE
        cut_d = P.SCREEN_MODULE_D + 2 * P.SCREEN_BEZEL_CLEARANCE
        bw, bd = cut_w + 2 * P.BEZEL_WALL, cut_d + 2 * P.BEZEL_WALL
        bez = box(P.SCREEN_CX - bw / 2, P.SCREEN_CY - bd / 2, bz0, P.SCREEN_CX + bw / 2, P.SCREEN_CY + bd / 2, bz0 + P.BEZEL_T)
        bez = bez.cut(box(P.SCREEN_CX + P.SCREEN_VIS_OFFSET_X - P.SCREEN_VIS_W / 2, P.SCREEN_CY + P.SCREEN_VIS_OFFSET_Y - P.SCREEN_VIS_D / 2, bz0,
                          P.SCREEN_CX + P.SCREEN_VIS_OFFSET_X + P.SCREEN_VIS_W / 2, P.SCREEN_CY + P.SCREEN_VIS_OFFSET_Y + P.SCREEN_VIS_D / 2, bz0 + P.BEZEL_T))
        posts = [cyl_z(x, y, zt, bz0, P.BEZEL_BOSS_D).cut(cyl_z(x, y, zt, bz0 + P.BEZEL_T, P.SCREEN_HOLE_D)) for (x, y) in hole_pts]
        bez = bez.union(fuse(*posts))
        bez = bez.cut(fuse(*[cyl_z(x, y, zt, bz0 + P.BEZEL_T, P.SCREEN_HOLE_D) for (x, y) in hole_pts]))
        out.append(part("screen_bezel", bez, "print", (0.9, 0.55, 0.1), "printed bezel"))
    return out


# ------------------------------------------------------------------- fan --
def fan_part():
    y1 = D - T
    y0 = y1 - P.FAN_T
    body = box(P.FAN_CX - P.FAN_SIZE / 2, y0, P.FAN_CZ - P.FAN_SIZE / 2, P.FAN_CX + P.FAN_SIZE / 2, y1, P.FAN_CZ + P.FAN_SIZE / 2)
    body = body.cut(cyl_y(P.FAN_CX, P.FAN_CZ, y0, y1, P.FAN_SIZE - 3))
    hub = cyl_y(P.FAN_CX, P.FAN_CZ, y0 + 1, y1 - 1, 18)
    spokes = box(P.FAN_CX - 1, y0 + 3, P.FAN_CZ - (P.FAN_SIZE - 1) / 2, P.FAN_CX + 1, y0 + 6, P.FAN_CZ + (P.FAN_SIZE - 1) / 2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            body = body.cut(cyl_y(P.FAN_CX + sx * P.FAN_HOLE_SPACING / 2, P.FAN_CZ + sz * P.FAN_HOLE_SPACING / 2, y0, y1, P.FAN_SCREW_D))
    return part("case_fan", fuse(body, hub, spokes), "component", (0.15, 0.15, 0.17), "40 mm exhaust fan")


# ------------------------------------------------------------------ feet --
def feet_part():
    out = []
    for fx in (P.FOOT_INSET, W - P.FOOT_INSET):
        for fy in (P.FOOT_INSET, D - P.FOOT_INSET):
            out.append(cyl_z(fx, fy, -P.FOOT_H, 0.0, P.FOOT_D))
    return part("rubber_feet", fuse(*out), "component", (0.1, 0.1, 0.1), "rubber feet (x4)")


# --------------------------------------------------------------- monitor --
def monitor_part():
    m = box(-P.MON_W / 2, 0, 0, P.MON_W / 2, P.MON_T, P.MON_H)
    # stand: a wedge strut on the back
    s = m.val().rotate(V(0, 0, 0), V(1, 0, 0), -P.MON_TILT)   # top moves toward +Y
    bb = s.BoundingBox()
    s = s.translate(V(W / 2, (D + P.MON_GAP) - bb.ymin, -P.FOOT_H - bb.zmin))
    return part("monitor", s, "reference", (0.1, 0.1, 0.12), "MSI MP165 E6 monitor", alpha=1.0)


# -------------------------------------------------------------- assembly --
def case_parts(panel_dict):
    names = {"top": "case_top_panel", "bottom": "case_bottom", "front": "case_front_panel",
             "back": "case_back_panel", "left": "case_side_left", "right": "case_side_right"}
    out = []
    for k, p in panel_dict.items():
        out.append(part(names[k], pn.panel_solid(p), "panel", ACRYLIC, f"{k} panel", alpha=0.35))
    return out


def all_parts(panel_dict):
    parts = case_parts(panel_dict)
    parts += front_controls()
    pi_so, perf_so = standoffs()
    parts.append(part("pi5_standoffs", pi_so, "component", (0.8, 0.7, 0.2), "Pi standoffs"))
    parts.append(part("perf_standoffs", perf_so, "component", (0.8, 0.7, 0.2), "perfboard standoffs"))
    parts.append(part("pi5", pi_to_world(pi_board_local()), "component", GREEN_PCB, "Raspberry Pi 5 + Active Cooler"))
    pb, uln = perf_pieces()
    parts.append(part("perfboard", pb, "component", (0.75, 0.6, 0.3), "perfboard"))
    parts.append(part("uln2003", uln, "component", BLACK, "ULN2003"))
    bx, by, bz = P.BREAKOUT_SIZE
    parts.append(part("gpio_breakout", box(P.BREAKOUT_CX - bx / 2, P.BREAKOUT_CY - by / 2, T, P.BREAKOUT_CX + bx / 2, P.BREAKOUT_CY + by / 2, T + bz),
                      "component", (0.1, 0.3, 0.6), "GPIO ribbon breakout"))
    parts += screen_parts()
    if P.ENABLE_FAN:
        parts.append(fan_part())
    parts.append(feet_part())
    if P.INCLUDE_MONITOR:
        parts.append(monitor_part())
    return parts
