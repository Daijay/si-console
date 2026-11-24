"""Component models (controls, Pi 5, screen, wires, ...) and the assembly.

Each part is a dict: name, solid (CadQuery shape in world coordinates), category
("panel" = laser-cut acrylic, "component", "wire", "reference"), colour (RGB 0..1), alpha, label.
"""
import math

import cadquery as cq

import geo
import panels as pn
import params as P
import wires as wr

V = cq.Vector
T = P.T


# ------------------------------------------------------------ primitives --
def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane(obj=cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0)))


def cyl_y(cx, cz, y0, y1, d):
    return cq.Workplane(obj=cq.Solid.makeCylinder(d / 2, y1 - y0, V(cx, y0, cz), V(0, 1, 0)))


def cyl_z(cx, cy, z0, z1, d):
    return cq.Workplane(obj=cq.Solid.makeCylinder(d / 2, z1 - z0, V(cx, cy, z0), V(0, 0, 1)))


def fuse(*items):
    out = items[0]
    for it in items[1:]:
        out = out.union(it)
    return out


def part(name, solid, category, colour, label, alpha=1.0):
    s = solid.val() if hasattr(solid, "val") else solid
    return dict(name=name, solid=s, category=category, colour=colour, alpha=alpha, label=label)


def tube(pts, r):
    segs = []
    for a, b in zip(pts, pts[1:]):
        d = V(*b) - V(*a)
        if d.Length < 1e-6:
            continue
        segs.append(cq.Solid.makeCylinder(r, d.Length, V(*a), d))
    for p in pts[1:-1]:
        segs.append(cq.Solid.makeSphere(r, V(*p), angleDegrees1=-90, angleDegrees2=90))
    return cq.Compound.makeCompound(segs)


ACRYLIC = (0.72, 0.88, 0.95)
GREEN_PCB = (0.1, 0.45, 0.2)
BLACK = (0.12, 0.12, 0.13)
LED_RGB = {"green": (0.1, 0.9, 0.2), "white": (0.96, 0.96, 0.96), "blue": (0.15, 0.35, 1.0), "yellow": (1.0, 0.85, 0.1)}


def to_frame(shape, frame):
    """Move a shape built in a tilted plate's local frame into the world."""
    x0, y0, z0, deg = frame
    s = shape.val() if hasattr(shape, "val") else shape
    return s.rotate(V(0, 0, 0), V(1, 0, 0), -deg).translate(V(x0, y0, z0))


# -------------------------------------------------------------- controls --
def arcade(name, u, hole, colour, label):
    body_d = hole - P.BTN_BODY_CLEAR
    z = P.BTN_V
    s = fuse(cyl_y(u, z, -3.0, 0.0, P.BTN_FLANGE_D), cyl_y(u, z, -P.BTN_CAP_PROUD, -3.0, body_d),
             cyl_y(u, z, 0.0, T + P.ARCADE_REAR, body_d), cyl_y(u, z, T, T + 5.0, P.BTN_FLANGE_D))
    return part(name, to_frame(s, geo.STRIP_FRAME), "component", colour, label)


def front_controls():
    f = geo.STRIP_FRAME
    out = [arcade("btn_green", P.GREEN_U, P.GREEN_HOLE, (0.1, 0.75, 0.25), "green button"),
           arcade("btn_red", P.RED_U, P.RED_HOLE, (0.85, 0.12, 0.12), "red button")]
    kd = P.KILL_HOLE - P.BTN_BODY_CLEAR
    kill = fuse(cyl_y(P.KILL_U, P.BTN_V, -P.KILL_HEAD_H, 0.0, P.KILL_HEAD_D), cyl_y(P.KILL_U, P.BTN_V, 0.0, T + P.KILL_REAR, kd),
                cyl_y(P.KILL_U, P.BTN_V, T, T + 5.0, P.KILL_BODY + 10))
    out.append(part("kill_switch", to_frame(kill, f), "component", (0.8, 0.05, 0.05), "kill switch"))
    pd = P.PTT_HOLE - P.BTN_BODY_CLEAR
    ptt = fuse(cyl_y(P.PTT_U, P.BTN_V, -P.PTT_HEAD_H, 0.0, P.PTT_HEAD_D), cyl_y(P.PTT_U, P.BTN_V, 0.0, T + P.PTT_REAR, pd),
               cyl_y(P.PTT_U, P.BTN_V, T, T + 2.0, P.PTT_HEAD_D + 2))
    out.append(part("btn_ptt", to_frame(ptt, f), "component", (0.2, 0.2, 0.25), "push to talk"))
    td = P.TOGGLE_HOLE - P.BTN_BODY_CLEAR
    tog = fuse(cyl_y(P.TOGGLE_U, P.BTN_V, -P.TOGGLE_LEVER_H, 0.0, P.TOGGLE_LEVER_D), cyl_y(P.TOGGLE_U, P.BTN_V, 0.0, T + P.TOGGLE_REAR, td),
               cyl_y(P.TOGGLE_U, P.BTN_V, T, T + 2.0, P.TOGGLE_HOLE + 2))
    out.append(part("toggle_lang", to_frame(tog, f), "component", (0.75, 0.75, 0.78), "EN/ZH toggle"))
    x0 = P.STRIP_W / 2 - 1.5 * P.LED_PITCH
    for i, nm in enumerate(P.LED_NAMES):
        x = x0 + i * P.LED_PITCH
        led = fuse(cyl_y(x, P.LED_V, -P.LED_DOME_PROUD, T + P.LED_REAR, P.LED_HOLE - P.BTN_BODY_CLEAR / 2),
                   cyl_y(x, P.LED_V, T, T + 1.0, P.LED_FLANGE_D))
        out.append(part(f"led_{nm}", to_frame(led, f), "component", LED_RGB[P.LED_COLOURS[i]], f"LED {nm.upper()}"))
    return out


# ------------------------------------------------------------ Raspberry Pi --
def pi_board_local():
    """Pi 5 in board coordinates: X along the 85 mm length from the left edge, Y from the power/HDMI long edge,
    Z up from the PCB underside (PCB occupies 0..1.6)."""
    pcb = cq.Workplane("XY").box(P.PI_L, P.PI_W, P.PI_PCB_T, centered=False)
    for bx in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SX):
        for by in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SY):
            pcb = pcb.cut(cq.Workplane("XY").center(bx, by).circle(P.PI_HOLE_D / 2).extrude(P.PI_PCB_T))
    top = P.PI_PCB_T
    items = [pcb]
    items.append(box(P.PI_USBC_BX - 4.5, -P.PI_EDGE_OVERHANG, top, P.PI_USBC_BX + 4.5, 7.3, top + 3.2))
    for bx in (P.PI_HDMI0_BX, P.PI_HDMI1_BX):
        items.append(box(bx - 3.5, -P.PI_EDGE_OVERHANG, top, bx + 3.5, 6.5, top + 3.4))
    ul, uw, uh = P.PI_USB_STACK
    for by in P.PI_USB_BY:
        items.append(box(P.PI_L + P.PI_PORT_OVERHANG - ul, by - uw / 2, top, P.PI_L + P.PI_PORT_OVERHANG, by + uw / 2, top + uh))
    el, ew, eh = P.PI_ETH_BOX
    items.append(box(P.PI_L + P.PI_PORT_OVERHANG - ew, max(0.0, P.PI_ETH_BY - el / 2), top, P.PI_L + P.PI_PORT_OVERHANG, P.PI_ETH_BY + el / 2, top + eh))
    items.append(box(P.PI_GPIO_BX - 25.4, P.PI_GPIO_BY - 2.5, top, P.PI_GPIO_BX + 25.4, P.PI_GPIO_BY + 2.5, top + P.PI_GPIO_H))
    cx, cy, ch = P.COOLER_SIZE
    items.append(box(P.COOLER_BX - cx / 2, P.COOLER_BY - cy / 2, top, P.COOLER_BX + cx / 2, P.COOLER_BY + cy / 2, top + ch))
    return fuse(*items)


def pi_to_world(shape):
    s = shape.val() if hasattr(shape, "val") else shape
    s = s.rotate(V(0, 0, 0), V(0, 0, 1), 180)
    return cq.Workplane(obj=s.translate(V(P.PI_X0 + P.PI_L, geo.pi_y0() + P.PI_W, T + P.PI_STANDOFF_H)))


def perf_pieces():
    z0 = T + P.PERF_STANDOFF_H
    pb = box(P.PERF_CX - P.PERF_X / 2, P.PERF_CY - P.PERF_Y / 2, z0, P.PERF_CX + P.PERF_X / 2, P.PERF_CY + P.PERF_Y / 2, z0 + P.PERF_T)
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
            x, y = geo.pi_world(bx, by)
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
def screen_parts():
    f = geo.plate_frame()
    mx0 = (P.PLATE_W - P.SCREEN_MODULE_W) / 2
    v0 = P.PLATE_MOD_V0
    y_a = -P.SCREEN_STANDOFF_H
    y_b = y_a - P.SCREEN_MODULE_H
    mod = box(mx0, y_b, v0, mx0 + P.SCREEN_MODULE_W, y_a, v0 + P.SCREEN_MODULE_D)
    pts = []
    for sx in (0, 1):
        for sy in (0, 1):
            hu = mx0 + (P.SCREEN_HOLE_INSET if sx == 0 else P.SCREEN_MODULE_W - P.SCREEN_HOLE_INSET)
            hv = v0 + (P.SCREEN_HOLE_INSET if sy == 0 else P.SCREEN_MODULE_D - P.SCREEN_HOLE_INSET)
            pts.append((hu, hv))
    for (hu, hv) in pts:
        mod = mod.cut(cyl_y(hu, hv, y_b, y_a, P.SCREEN_HOLE_D))
    so = fuse(*[cyl_y(hu, hv, y_a, 0.0, P.SCREEN_STANDOFF_D) for (hu, hv) in pts])
    return [part("mini_screen", to_frame(mod, f), "component", (0.05, 0.05, 0.08), "5 in HDMI screen"),
            part("screen_standoffs", to_frame(so, f), "component", (0.8, 0.7, 0.2), "screen standoffs (x4)")]


def feet_part():
    out = []
    for fx in (P.FOOT_INSET, P.BASE_W - P.FOOT_INSET):
        for fy in (P.FOOT_INSET, P.BASE_D - P.FOOT_INSET):
            out.append(cyl_z(fx, fy, -P.FOOT_H, 0.0, P.FOOT_D))
    return part("rubber_feet", fuse(*out), "component", (0.1, 0.1, 0.1), "rubber feet (x4)")


def monitor_part():
    m = box(-P.MON_W / 2, 0, 0, P.MON_W / 2, P.MON_T, P.MON_H)
    s = m.val().rotate(V(0, 0, 0), V(1, 0, 0), -P.MON_TILT)
    bb = s.BoundingBox()
    s = s.translate(V(P.BASE_W / 2, (P.BASE_D + P.MON_GAP) - bb.ymin, -P.FOOT_H - bb.zmin))
    return part("monitor", s, "reference", (0.1, 0.1, 0.12), "MSI MP165 E6 monitor")


def wire_parts():
    out = []
    for w in wr.all_wires():
        nm = "wire_" + w["name"].lower().replace(" ", "_").replace("-", "_")
        p = part(nm, tube(w["pts"], w["r"]), "wire", wr.COLOURS[w["colour"]], w["name"])
        p["wire"] = w
        out.append(p)
    return out


# -------------------------------------------------------------- assembly --
def panel_parts(panel_dict):
    out = []
    labels = {"base_plate": "Base plate", "control_strip": "Control strip", "strip_bracket": "Strip bracket",
              "screen_plate": "Screen plate", "screen_prop": "Screen prop"}
    for key, p in panel_dict.items():
        for (nm, origin) in p.instances:
            q = part(nm, pn.panel_solid(p, origin), "panel", ACRYLIC, labels[key], alpha=0.35)
            q["laser"] = key
            out.append(q)
    return out


def all_parts(panel_dict):
    parts = panel_parts(panel_dict)
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
    parts.append(feet_part())
    if P.INCLUDE_MONITOR:
        parts.append(monitor_part())
    if P.INCLUDE_WIRES:
        parts += wire_parts()
    return parts
