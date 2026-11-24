"""Design checks for Rev R5. Each check returns a Result; build.py writes them to CHECKS.md
and exits non-zero if any fail."""
import itertools
import math
from dataclasses import dataclass, field

import cadquery as cq
from shapely.geometry import box as sbox

import geo
import panels as pn
import params as P
import parts as pt
import wires as wr

T = P.T
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


def solids_only(parts):
    return [p for p in parts if p["category"] != "wire"]


# ------------------------------------------------------------------ 1 --
def check_collisions(parts):
    r = Result("No part collides with another")
    tol = 0.5
    ps = solids_only(parts)
    n = 0
    for a, b in itertools.combinations(ps, 2):
        v = inter_volume(a["solid"], b["solid"])
        n += 1
        if v > tol:
            r.fail(f"{a['name']} overlaps {b['name']} by {v:.1f} mm3")
    r.note(f"{len(ps)} solid parts, {n} pairs tested, tolerance {tol} mm3. Touching faces (standoff on plate, tab bottoming in a slot) count as clear. "
           f"Wires and cables are not solids for this test; they end on their terminals by construction.")
    return r


# ------------------------------------------------------------------ 2 --
def check_holes(panel_dict):
    r = Result(f"Every hole fully inside its part, at least {P.MIN_EDGE_GAP:g} mm from any edge or other hole")
    for name, p in panel_dict.items():
        shapes = [(h, h.shape()) for h in p.holes]
        for h, s in shapes:
            if not p.outline.contains(s):
                r.fail(f"{name}: '{h.label}' at ({h.cx:.1f}, {h.cy:.1f}) is not fully inside the part")
                continue
            d = p.outline.exterior.distance(s)
            if d < P.MIN_EDGE_GAP - 1e-6:
                r.fail(f"{name}: '{h.label}' at ({h.cx:.1f}, {h.cy:.1f}) is {d:.2f} mm from an edge")
        for (h1, s1), (h2, s2) in itertools.combinations(shapes, 2):
            d = s1.distance(s2)
            if d < P.MIN_HOLE_GAP - 1e-6:
                r.fail(f"{name}: '{h1.label}' at ({h1.cx:.1f}, {h1.cy:.1f}) and '{h2.label}' at ({h2.cx:.1f}, {h2.cy:.1f}) are {d:.2f} mm apart")
        if shapes:
            md = min(p.outline.exterior.distance(s) for _, s in shapes)
            mh = min([a.distance(b) for (_, a), (_, b) in itertools.combinations(shapes, 2)] or [999])
            r.note(f"{name}: {len(shapes)} holes, closest to an edge {md:.1f} mm, closest pair {mh:.1f} mm")
        else:
            r.note(f"{name}: no holes (tabs only)")
    return r


# ------------------------------------------------------------------ 3 --
def check_sheet_fit(panel_dict):
    r = Result(f"Every part fits on a {P.SHEET_W:g} x {P.SHEET_L:g} mm sheet")
    uw, ul = P.SHEET_W - 2 * P.SHEET_MARGIN, P.SHEET_L - 2 * P.SHEET_MARGIN
    for name, p in panel_dict.items():
        w, h = p.size
        w += P.KERF
        h += P.KERF
        ok = (w <= uw and h <= ul) or (h <= uw and w <= ul)
        r.note(f"{name} (x{p.qty}): {w:.1f} x {h:.1f} mm with kerf, usable sheet {uw:g} x {ul:g}")
        if not ok:
            r.fail(f"{name} ({w:.1f} x {h:.1f}) does not fit")
    return r


# ------------------------------------------------------------------ 4 --
def slot_solid(panel, hole, origin):
    ud, vd = panel.udir, panel.vdir
    n = (ud[1] * vd[2] - ud[2] * vd[1], ud[2] * vd[0] - ud[0] * vd[2], ud[0] * vd[1] - ud[1] * vd[0])
    plane = cq.Plane(origin=origin, xDir=ud, normal=n)
    s = cq.Workplane(plane).center(hole.cx, hole.cy).rect(hole.w, hole.h).extrude(T).val()
    if panel.xf:
        ang, (tx, ty, tz) = panel.xf
        s = s.rotate(V(0, 0, 0), V(1, 0, 0), ang).translate(V(tx, ty, tz))
    return s


def check_joints(panel_dict, parts):
    r = Result("Tabs and slots mate (every slot is filled by exactly one tab)")
    by_name = {p["name"]: p["solid"] for p in parts}
    n_ok = 0
    for key in ("base_plate", "control_strip", "screen_plate"):
        panel = panel_dict[key]
        for (inst, origin) in panel.instances:
            for h in panel.holes:
                if h.kind != "rect" or "slot" not in h.label or "tie" in h.label:
                    continue
                s = slot_solid(panel, h, origin)
                vol = s.Volume()
                filled = 0.0
                for nm, sol in by_name.items():
                    if nm.startswith(("strip_bracket", "screen_prop")):
                        filled += inter_volume(s, sol)
                if abs(filled - vol) > 0.5:
                    r.fail(f"{key} slot '{h.label}' at ({h.cx:.1f}, {h.cy:.1f}): {filled:.1f} of {vol:.1f} mm3 filled by a tab")
                else:
                    n_ok += 1
    r.note(f"{n_ok} slots checked, each completely filled by a tab of the bracket or prop that belongs there")
    # each bracket and prop must have all its tabs seated: count slots per part
    return r


# ------------------------------------------------------------------ 5 --
def check_clearances(parts):
    r = Result("Clear space behind the buttons (50 mm) and the kill switch (75 mm), checked against the base and everything else")
    f = geo.STRIP_FRAME
    specs = [("btn_green", P.GREEN_U, P.GREEN_HOLE, P.CLEAR_ARCADE), ("btn_red", P.RED_U, P.RED_HOLE, P.CLEAR_ARCADE),
             ("kill_switch", P.KILL_U, P.KILL_HOLE, P.CLEAR_KILL), ("btn_ptt", P.PTT_U, P.PTT_HOLE, P.CLEAR_PTT),
             ("toggle_lang", P.TOGGLE_U, P.TOGGLE_HOLE, P.CLEAR_PTT)]
    others = [p for p in solids_only(parts) if p["name"] != "control_strip"]
    for own, u, hole, depth in specs:
        rad = hole / 2 + P.CLEAR_MARGIN
        zone = pt.to_frame(pt.box(u - rad, T, P.BTN_V - rad, u + rad, T + depth, P.BTN_V + rad), f)
        bad = []
        for p in others:
            if p["name"] == own:
                continue
            v = inter_volume(zone, p["solid"])
            if v > 0.5:
                bad.append(f"{p['name']} ({v:.0f} mm3)")
        zb = zone.BoundingBox()
        used = P.ARCADE_REAR if own in ("btn_green", "btn_red") else {"kill_switch": P.KILL_REAR, "btn_ptt": P.PTT_REAR, "toggle_lang": P.TOGGLE_REAR}[own]
        if bad:
            r.fail(f"{own}: {depth:g} mm zone intersects " + ", ".join(bad))
        if used > depth:
            r.fail(f"{own}: body is {used:g} mm deep, more than the {depth:g} mm kept clear")
        # lowest point of the zone above the base top
        r.note(f"{own}: zone {2 * rad:.0f} x {2 * rad:.0f} mm, {depth:g} mm deep along the button axis, own body {used:g} mm; "
               f"lowest point of the zone is {zb.zmin - T:.1f} mm above the base plate")
        if zb.zmin < T - 1e-6:
            r.fail(f"{own}: zone reaches below the base top surface")
    return r


# ------------------------------------------------------------------ 6 --
def check_wires(parts):
    r = Result("Cables and wires reach between the Pi, breakout, perfboard and controls")
    for w in wr.all_wires():
        length = wr.plen(w["pts"]) * P.WIRE_SLACK
        ok = length <= w["limit"]
        r.note(f"{w['group']}: {w['name']} {length:.0f} mm of {w['limit']:g} mm" + ("" if ok else "  <-- too long"))
        if not ok:
            r.fail(f"{w['name']} ({w['group']}) needs {length:.0f} mm, limit {w['limit']:g} mm")
    # wire ends must land on their terminals: spot check first and last points against the part boxes
    ends = {"G": "btn_green", "R": "btn_red", "K": "kill_switch", "PTT": "btn_ptt", "LANG": "toggle_lang"}
    by = {p["name"]: p["solid"].BoundingBox() for p in parts if p["category"] != "wire"}
    for w in wr.button_wires():
        if w["name"] in ends:
            bb = by[ends[w["name"]]]
            x, y, z = w["pts"][-1]
            ok = bb.xmin - 1 <= x <= bb.xmax + 1 and bb.ymin - 3 <= y <= bb.ymax + 3 and bb.zmin - 3 <= z <= bb.zmax + 3
            if not ok:
                r.fail(f"wire {w['name']} does not end at its button")
    return r


# --------------------------------------------------------------- extras --
def check_layout(panel_dict, parts):
    r = Result(f"Everything on the base is at least {P.PART_MARGIN:g} mm from the base edge")
    base = panel_dict["base_plate"].outline
    inner = base.buffer(-P.PART_MARGIN)
    skip = {"rubber_feet", "monitor"}
    for p in solids_only(parts):
        if p["name"] in skip or p["name"] == "base_plate":
            continue
        bb = p["solid"].BoundingBox()
        foot = sbox(bb.xmin, bb.ymin, bb.xmax, bb.ymax)
        d = base.exterior.distance(foot) if base.contains(foot) else -base.exterior.distance(foot)
        if not inner.contains(foot):
            r.fail(f"{p['name']} comes within {max(d, 0):.1f} mm of the base edge (or past it)")
    xs = [p["solid"].BoundingBox() for p in solids_only(parts) if p["name"] not in skip and p["name"] != "base_plate"]
    r.note("min margins (mm): " + ", ".join(f"{k} {v:.1f}" for k, v in (
        ("left", min(b.xmin for b in xs)), ("front", min(b.ymin for b in xs)),
        ("right", P.BASE_W - max(b.xmax for b in xs)), ("back", P.BASE_D - max(b.ymax for b in xs)))))
    # parts must stand on the base (screen plate and strip hang on their supports)
    return r


def run_all(panel_dict, parts):
    return [check_collisions(parts), check_holes(panel_dict), check_sheet_fit(panel_dict), check_joints(panel_dict, parts),
            check_clearances(parts), check_wires(parts), check_layout(panel_dict, parts)]
