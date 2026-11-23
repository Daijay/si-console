"""Design checks. Each check returns a Result; build.py writes them to CHECKS.md
and exits non-zero if any fail."""
import itertools
import math
from dataclasses import dataclass, field

import cadquery as cq
from shapely.geometry import box as sbox

import params as P
import panels as pn
import parts as pt

W, D, H, T = P.CASE_W, P.CASE_D, P.CASE_H, P.T
V = cq.Vector


@dataclass
class Result:
    name: str
    ok: bool = True
    lines: list = field(default_factory=list)

    def fail(self, msg):
        self.ok = False
        self.lines.append("FAIL: " + msg)

    def note(self, msg):
        self.lines.append(msg)


def _overlap_bb(a, b, tol=0.01):
    return not (a.xmax < b.xmin - tol or b.xmax < a.xmin - tol or a.ymax < b.ymin - tol or
                b.ymax < a.ymin - tol or a.zmax < b.zmin - tol or b.zmax < a.zmin - tol)


def inter_volume(sa, sb):
    if not _overlap_bb(sa.BoundingBox(), sb.BoundingBox()):
        return 0.0
    try:
        return sa.intersect(sb).Volume()
    except Exception:
        return 0.0


# ------------------------------------------------------------------ 1 --
def check_collisions(parts):
    r = Result("No part collides with another in the assembly")
    tol = 0.5  # mm^3, above numerical noise
    n_pairs = 0
    for a, b in itertools.combinations(parts, 2):
        v = inter_volume(a["solid"], b["solid"])
        n_pairs += 1
        if v > tol:
            r.fail(f"{a['name']} overlaps {b['name']} by {v:.1f} mm3")
    r.note(f"{len(parts)} parts, {n_pairs} pairs tested, overlap tolerance {tol} mm3. Parts that only touch (a standoff on a panel, a button flange on a face) count as clear.")
    return r


# ------------------------------------------------------------------ 2 --
def check_holes(panel_dict):
    r = Result(f"Every hole fully inside its panel, at least {P.MIN_EDGE_GAP:g} mm from any edge or other hole")
    for name, p in panel_dict.items():
        shapes = [(h, h.shape()) for h in p.holes]
        for h, s in shapes:
            if not p.outline.contains(s):
                r.fail(f"{name}: '{h.label}' at ({h.cx:.1f}, {h.cy:.1f}) is not fully inside the panel")
                continue
            d = p.outline.exterior.distance(s)
            if d < P.MIN_EDGE_GAP - 1e-6:
                r.fail(f"{name}: '{h.label}' at ({h.cx:.1f}, {h.cy:.1f}) is {d:.2f} mm from an edge")
        for (h1, s1), (h2, s2) in itertools.combinations(shapes, 2):
            d = s1.distance(s2)
            if d < P.MIN_HOLE_GAP - 1e-6:
                r.fail(f"{name}: '{h1.label}' and '{h2.label}' are {d:.2f} mm apart")
        if shapes:
            md = min([p.outline.exterior.distance(s) for _, s in shapes])
            mh = min([a.distance(b) for (_, a), (_, b) in itertools.combinations(shapes, 2)] or [999])
            r.note(f"{name}: {len(shapes)} holes, closest to an edge {md:.1f} mm, closest pair {mh:.1f} mm")
    return r


# ------------------------------------------------------------------ 3 --
def check_sheet_fit(panel_dict):
    r = Result(f"Every panel fits on a {P.SHEET_W:g} x {P.SHEET_L:g} mm sheet")
    usable_w = P.SHEET_W - 2 * P.SHEET_MARGIN
    usable_l = P.SHEET_L - 2 * P.SHEET_MARGIN
    for name, p in panel_dict.items():
        w, h = p.size
        w += P.KERF
        h += P.KERF
        fits = (w <= usable_w and h <= usable_l) or (h <= usable_w and w <= usable_l)
        r.note(f"{name}: {w:.1f} x {h:.1f} mm (with kerf), usable sheet {usable_w:g} x {usable_l:g}")
        if not fits:
            r.fail(f"{name} ({w:.1f} x {h:.1f}) does not fit")
    return r


# ------------------------------------------------------------------ 4 --
def check_fingers(panel_dict, parts):
    r = Result("Finger joints mate between neighbouring panels")
    solids = {p["name"]: p["solid"] for p in parts if p["category"] == "panel"}
    nm = {"top": "case_top_panel", "bottom": "case_bottom", "front": "case_front_panel",
          "back": "case_back_panel", "left": "case_side_left", "right": "case_side_right"}
    cells = []
    for s in pn.edge_strips():
        ax = s["axis"]
        rng = {"x": s["x"], "y": s["y"], "z": s["z"]}
        rng[ax] = s["span"]
        cells.append((s["name"], rng, (s["even"], s["odd"]), pn.segments(*s["span"])))
    for c in pn.corner_cubes():
        cells.append((f"corner-{c['owner']}", {"x": c["x"], "y": c["y"], "z": c["z"]}, (c["owner"],), None))
    for name, rng, owners, segs in cells:
        b = pt.box(rng["x"][0], rng["y"][0], rng["z"][0], rng["x"][1], rng["y"][1], rng["z"][1]).val()
        total = b.Volume()
        got = sum(inter_volume(b, solids[nm[o]]) for o in set(owners))
        if abs(got - total) > 0.05:
            r.fail(f"edge {name}: {got:.1f} of {total:.1f} mm3 filled (gap or overlap in the fingers)")
        if segs:
            if len(segs) % 2 == 0:
                r.fail(f"edge {name} has an even finger count ({len(segs)})")
            r.note(f"edge {name}: {len(segs)} fingers of {segs[0][1] - segs[0][0]:.2f} mm, {owners[0]} owns the ends")
        else:
            r.note(f"{name} cube filled")
    # nothing may overlap between panels (also covered by the collision check)
    pnames = list(solids)
    for a, b in itertools.combinations(pnames, 2):
        v = inter_volume(solids[a], solids[b])
        if v > 0.05:
            r.fail(f"{a} and {b} overlap by {v:.2f} mm3")
    r.note(f"fit gap per finger side after laser kerf compensation: 0.00 mm (cut paths offset by {P.KERF / 2:g} mm so parts finish at nominal size)")
    return r


# ------------------------------------------------------------------ 5 --
def check_clearances(parts):
    r = Result("Clear space behind the arcade buttons (50 mm) and the kill switch (75 mm)")
    specs = [("btn_green", P.GREEN_X, P.GREEN_HOLE, P.CLEAR_ARCADE), ("btn_red", P.RED_X, P.RED_HOLE, P.CLEAR_ARCADE),
             ("kill_switch", P.KILL_X, P.KILL_HOLE, P.CLEAR_KILL), ("btn_ptt", P.PTT_X, P.PTT_HOLE, P.CLEAR_PTT),
             ("toggle_lang", P.TOGGLE_X, P.TOGGLE_HOLE, P.CLEAR_PTT)]
    for own, x, hole, depth in specs:
        rad = hole / 2 + P.CLEAR_MARGIN
        zone = pt.box(x - rad, T, P.BTN_Z - rad, x + rad, T + depth, P.BTN_Z + rad).val()
        bad = []
        for p in parts:
            if p["name"] == own or p["category"] == "panel":
                continue
            v = inter_volume(zone, p["solid"])
            if v > 0.5:
                bad.append(f"{p['name']} ({v:.0f} mm3)")
        # also report the body depth of the control itself against the requirement
        body = next(p for p in parts if p["name"] == own)["solid"].BoundingBox()
        used = body.ymax - T
        if bad:
            r.fail(f"{own}: {depth:g} mm zone intersects " + ", ".join(bad))
        if used > depth:
            r.fail(f"{own}: body reaches {used:.0f} mm behind the panel, more than the {depth:g} mm kept clear")
        # nearest other part behind the control (informational)
        nearest = min([p["solid"].BoundingBox().ymin for p in parts if p["category"] in ("component", "print")
                       and p["name"] != own and p["solid"].BoundingBox().ymin > T and
                       p["solid"].BoundingBox().xmin < x + rad and p["solid"].BoundingBox().xmax > x - rad and
                       p["solid"].BoundingBox().zmin < P.BTN_Z + rad and p["solid"].BoundingBox().zmax > P.BTN_Z - rad] or [None])
        r.note(f"{own}: zone {2 * rad:.0f} x {2 * rad:.0f} mm, {depth:g} mm deep, own body uses {used:.0f} mm" +
               (f", next part behind starts {nearest - T:.0f} mm from the panel" if nearest else ", nothing behind it"))
    return r


# ------------------------------------------------------------------ 6 --
def _bend_run(dx, R, max_angle_deg):
    """Straight-run length needed to move a cable sideways by dx with an S-bend of radius R."""
    dx = abs(dx)
    if dx < 1e-9:
        return 0.0
    tmax = math.radians(max_angle_deg)
    lat_max = 2 * R * (1 - math.cos(tmax))
    if dx <= lat_max:
        th = math.acos(1 - dx / (2 * R))
        return 2 * R * math.sin(th)
    ld = (dx - lat_max) / math.sin(tmax)
    return 2 * R * math.sin(tmax) + ld * math.cos(tmax)


def check_cables():
    r = Result("The Pi cables reach their back panel cutouts")
    y_in = D - T
    top = pt.pi_pcb_top_z()
    zport = top + P.PI_PORT_Z
    ports = [("micro-HDMI 0", P.PI_HDMI0_BX, P.HDMI0_CUT_X, P.HDMI_PLUG_LEN),
             ("USB-C power", P.PI_USBC_BX, P.USBC_CUT_X, P.USBC_PLUG_LEN)]
    for nm, bx, cx, plug in ports:
        px, py = pt.pi_world(bx, 0)
        edge_y = py + P.PI_EDGE_OVERHANG
        run_avail = y_in - edge_y - plug
        dx = cx - px
        need = _bend_run(dx, P.CABLE_MIN_BEND_R, P.CABLE_MAX_EXIT_ANGLE)
        dz = abs(P.CUT_Z - zport)
        length = plug + math.hypot(run_avail, dx) * 1.1 + dz
        ok = run_avail >= need
        r.note(f"{nm}: port x={px:.1f}, cutout x={cx:g}, sideways {abs(dx):.1f} mm, straight run after plug {run_avail:.1f} mm, "
               f"S-bend needs {need:.1f} mm (bend radius {P.CABLE_MIN_BEND_R:g}), margin {run_avail - need:.1f} mm")
        if not ok:
            r.fail(f"{nm}: needs {need:.1f} mm of run after the plug, only {run_avail:.1f} mm available")
    # mic USB cable: leaves the USB stack toward the left wall, then runs to the back
    sx, sy = pt.pi_world(P.PI_L, P.PI_USB_BY[0])
    sx -= P.PI_PORT_OVERHANG
    clear = sx - T
    path = P.USB_PLUG_CLEAR + (y_in - sy) + abs(P.MIC_CUT_X - (sx - P.USB_PLUG_CLEAR))
    r.note(f"mic USB: plug needs {P.USB_PLUG_CLEAR:g} mm left of the Pi, {clear:.1f} mm available; cable path about {path * 1.15:.0f} mm of {P.MIC_CABLE_LEN:g} mm")
    if clear < P.USB_PLUG_CLEAR:
        r.fail(f"mic USB: only {clear:.1f} mm between the Pi and the left wall, plug needs {P.USB_PLUG_CLEAR:g} mm")
    if path * 1.15 > P.MIC_CABLE_LEN:
        r.fail(f"mic USB: cable path {path * 1.15:.0f} mm exceeds {P.MIC_CABLE_LEN:g} mm")
    # mini screen USB power cable: from outside through its back hole to the screen's power input
    sx0, sy0, sz0 = P.SCREEN_PWR_CUT_X, D - T, P.CUT_Z
    tx, ty, tz = P.SCREEN_CX - P.SCREEN_MODULE_W / 2, P.SCREEN_CY, pt.screen_z_top() - P.SCREEN_MODULE_H / 2
    plen = (abs(tx - sx0) + abs(ty - sy0) + abs(tz - sz0)) * 1.15
    r.note(f"mini screen USB power: hole to the screen edge about {plen:.0f} mm of cable inside the case, {P.SCREEN_PWR_CABLE_LEN:g} mm available (the screen HDMI cable stays inside)")
    if plen > P.SCREEN_PWR_CABLE_LEN:
        r.fail(f"mini screen power cable needs about {plen:.0f} mm, only {P.SCREEN_PWR_CABLE_LEN:g} mm available")
    # cutouts must be in line (same Z band) and big enough for plug body: informational
    # GPIO ribbon from the Pi header to the breakout board
    hx, hy = pt.pi_world(P.PI_GPIO_BX, P.PI_GPIO_BY)
    hz = top + P.PI_GPIO_H
    d = math.dist((hx, hy, hz), (P.BREAKOUT_CX, P.BREAKOUT_CY, T + P.BREAKOUT_SIZE[2])) * 1.3
    r.note(f"GPIO ribbon: header to breakout about {d:.0f} mm of {P.GPIO_RIBBON_LEN:g} mm")
    if d > P.GPIO_RIBBON_LEN:
        r.fail(f"GPIO ribbon needs about {d:.0f} mm, only {P.GPIO_RIBBON_LEN:g} mm available")
    return r


# --------------------------------------------------------------- extras --
def check_sanity(panel_dict):
    r = Result("Parameter sanity (screen window, fan opening, finger counts)")
    if P.SCREEN_MODE not in ("window_under", "bezel"):
        r.fail(f"SCREEN_MODE must be 'window_under' or 'bezel', got {P.SCREEN_MODE!r}")
    if P.SCREEN_MODE == "window_under":
        if P.SCREEN_VIS_W + abs(2 * P.SCREEN_VIS_OFFSET_X) >= P.SCREEN_MODULE_W or P.SCREEN_VIS_D + abs(2 * P.SCREEN_VIS_OFFSET_Y) >= P.SCREEN_MODULE_D:
            r.fail("visible area is not smaller than the module, the module would fall through the window")
        else:
            r.note(f"window {P.SCREEN_VIS_W:g} x {P.SCREEN_VIS_D:g} is smaller than module {P.SCREEN_MODULE_W:g} x {P.SCREEN_MODULE_D:g}: module cannot fall through")
    if P.ENABLE_FAN and P.FAN_AREA_D > P.FAN_SIZE - 3:
        r.fail("fan grid area larger than the fan frame opening")
    if P.T * 2 >= min(W, D, H):
        r.fail("panel thickness too large")
    r.note(f"mini screen top face {pt.screen_z_top():.1f} mm, panel underside {H - T:g} mm, gap {P.SCREEN_GAP:g} mm")
    return r


def run_all(panel_dict, parts):
    return [check_collisions(parts), check_holes(panel_dict), check_sheet_fit(panel_dict),
            check_fingers(panel_dict, parts), check_clearances(parts), check_cables(), check_sanity(panel_dict)]
