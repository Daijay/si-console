"""Laser-cut parts of Rev R5: base plate, control strip, strip brackets, screen plate, screen props.

Each part is one 2D outline plus holes in its own (u, v) view coordinates. The same 2D model feeds the
3D STEP solids, the DXF laser files and the dimensioned drawings, so they cannot disagree.
"""
from dataclasses import dataclass, field

import cadquery as cq
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

import geo
import params as P
import wires

T = P.T
V = cq.Vector


@dataclass
class Hole:
    kind: str            # "circle" or "rect"
    cx: float
    cy: float
    w: float             # diameter for circles
    h: float = 0.0
    label: str = ""
    assumed: bool = False

    def shape(self):
        if self.kind == "circle":
            return Point(self.cx, self.cy).buffer(self.w / 2.0, 64)
        return sbox(self.cx - self.w / 2, self.cy - self.h / 2, self.cx + self.w / 2, self.cy + self.h / 2)


def circle(cx, cy, d, label, assumed=False):
    return Hole("circle", cx, cy, d, 0.0, label, assumed)


def rect(cx, cy, w, h, label, assumed=False):
    return Hole("rect", cx, cy, w, h, label, assumed)


@dataclass
class Panel:
    name: str                 # laser part name, e.g. "base_plate"
    view: str
    outline: object           # shapely Polygon in view coordinates
    holes: list = field(default_factory=list)
    instances: list = field(default_factory=list)   # [(solid name, plane origin)]
    udir: tuple = (1, 0, 0)
    vdir: tuple = (0, 1, 0)
    xf: tuple = None          # (rotate about X in degrees, (tx, ty, tz)) applied after extrusion
    desc: str = ""

    @property
    def qty(self):
        return len(self.instances)

    @property
    def size(self):
        b = self.outline.bounds
        return (b[2] - b[0], b[3] - b[1])


def rrect(w, h, r):
    return sbox(0, 0, w, h).buffer(-r).buffer(r, resolution=16)


# ----------------------------------------------------------- brackets --
def support_profile(frame, v_span, tabs_v, foot):
    """Side profile (view coords u = world Y, v = world Z) of a bracket or prop: a triangle-ish body
    standing on the base with a sloped edge that touches the plate's rear face, tabs that pass through
    the plate (sloped edge) and tabs that pass through the base (bottom edge)."""
    deg = frame[3]
    s, c = geo.tilt_cs(deg)
    nrm = (-c, s)                                   # outward normal of the plate (y, z)

    def R(v):
        return geo.rear_face_pt(frame, v)

    s1, s2 = R(v_span[0]), R(v_span[1])
    y_end = s2[0] + foot
    body = Polygon([(s1[0], T), (y_end, T), (s2[0], s2[1]), (s1[0], s1[1])])
    parts = [body]
    for (a, b) in tabs_v:
        ra, rb = R(a), R(b)
        parts.append(Polygon([ra, rb, (rb[0] + T * nrm[0], rb[1] + T * nrm[1]), (ra[0] + T * nrm[0], ra[1] + T * nrm[1])]))
    length = y_end - s1[0]
    tl = 15.0
    if length >= 55:
        ys = [s1[0] + 5, y_end - 5 - tl]
    else:
        ys = [s1[0] + (length - tl) / 2]
    for y in ys:
        parts.append(sbox(y, 0, y + tl, T))
    u = unary_union([g.buffer(1e-4, join_style=2) for g in parts]).buffer(-1e-4, join_style=2).simplify(1e-6)
    assert u.geom_type == "Polygon", u.geom_type
    return u, ys, tl


def tab_slot_v(tabs_v):
    return [((a + b) / 2, b - a) for a, b in tabs_v]


def tilt_xf(frame):
    x0, y0, z0, deg = frame
    return (-deg, (x0, y0, z0))


# -------------------------------------------------------------- parts --
def build_panels():
    panels = {}
    # ---------------- control strip
    sh = []
    sh.append(circle(P.GREEN_U, P.BTN_V, P.GREEN_HOLE, "green button"))
    sh.append(circle(P.RED_U, P.BTN_V, P.RED_HOLE, "red button"))
    sh.append(circle(P.KILL_U, P.BTN_V, P.KILL_HOLE, "kill switch"))
    sh.append(circle(P.PTT_U, P.BTN_V, P.PTT_HOLE, "push to talk"))
    sh.append(circle(P.TOGGLE_U, P.BTN_V, P.TOGGLE_HOLE, "EN/ZH toggle"))
    x0 = P.STRIP_W / 2 - 1.5 * P.LED_PITCH
    for i, nm in enumerate(P.LED_NAMES):
        sh.append(circle(x0 + i * P.LED_PITCH, P.LED_V, P.LED_HOLE, f"LED {nm} ({P.LED_COLOURS[i]})"))
    for k, u in enumerate(P.BRACKET_U):
        for (vc, ln) in tab_slot_v(P.BRACKET_TABS_V):
            sh.append(rect(u, vc, T, ln, f"bracket {k + 1} slot"))
    sf = geo.STRIP_FRAME
    panels["control_strip"] = Panel("control_strip", "front face, as the user sees it (U right, V up the slope)",
                                    rrect(P.STRIP_W, P.STRIP_H, P.STRIP_RADIUS), sh, [("control_strip", (0, T, 0))],
                                    (1, 0, 0), (0, 0, 1), tilt_xf(sf), "sloped control strip")
    prof, ys_strip, tl = support_profile(sf, P.BRACKET_V, P.BRACKET_TABS_V, P.BRACKET_FOOT)
    panels["strip_bracket"] = Panel("strip_bracket", "side view (U = depth Y, V = height Z), console front to the left", prof, [],
                                    [(f"strip_bracket_{k + 1}", (P.STRIP_X0 + u - T / 2, 0, 0)) for k, u in enumerate(P.BRACKET_U)],
                                    (0, 1, 0), (0, 0, 1), None, "strip bracket")
    # ---------------- screen plate and props
    pf = geo.plate_frame()
    ph = []
    mx0 = (P.PLATE_W - P.SCREEN_MODULE_W) / 2
    for sx in (0, 1):
        for sy in (0, 1):
            hu = mx0 + (P.SCREEN_HOLE_INSET if sx == 0 else P.SCREEN_MODULE_W - P.SCREEN_HOLE_INSET)
            hv = P.PLATE_MOD_V0 + (P.SCREEN_HOLE_INSET if sy == 0 else P.SCREEN_MODULE_D - P.SCREEN_HOLE_INSET)
            ph.append(circle(hu, hv, P.SCREEN_HOLE_D, "screen standoff screw", assumed=True))
    for k, u in enumerate(P.PROP_U):
        for (vc, ln) in tab_slot_v(P.PROP_TABS_V):
            ph.append(rect(u, vc, T, ln, f"prop {k + 1} slot"))
    panels["screen_plate"] = Panel("screen_plate", "front face, as the user sees it (U right, V up the slope)",
                                   rrect(P.PLATE_W, P.PLATE_H, P.PLATE_RADIUS), ph, [("screen_plate", (0, T, 0))],
                                   (1, 0, 0), (0, 0, 1), tilt_xf(pf), "mini screen plate")
    prof2, ys_prop, tl2 = support_profile(pf, P.PROP_V, P.PROP_TABS_V, P.PROP_FOOT)
    px0 = pf[0]
    panels["screen_prop"] = Panel("screen_prop", "side view (U = depth Y, V = height Z), console front to the left", prof2, [],
                                  [(f"screen_prop_{k + 1}", (px0 + u - T / 2, 0, 0)) for k, u in enumerate(P.PROP_U)],
                                  (0, 1, 0), (0, 0, 1), None, "mini screen prop")
    # ---------------- base plate
    bh = []
    for bx in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SX):
        for by in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SY):
            x, y = geo.pi_world(bx, by)
            bh.append(circle(x, y, P.PI_HOLE_D, "Pi standoff (M2.5)"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            bh.append(circle(P.PERF_CX + sx * (P.PERF_X / 2 - P.PERF_HOLE_INSET), P.PERF_CY + sy * (P.PERF_Y / 2 - P.PERF_HOLE_INSET),
                             P.PERF_HOLE_D, "perfboard standoff (M3)"))
    for fx in (P.FOOT_INSET, P.BASE_W - P.FOOT_INSET):
        for fy in (P.FOOT_INSET, P.BASE_D - P.FOOT_INSET):
            bh.append(circle(fx, fy, P.FOOT_HOLE_D, "rubber foot", assumed=True))
    for k, u in enumerate(P.BRACKET_U):
        for y in ys_strip:
            bh.append(rect(P.STRIP_X0 + u, y + tl / 2, T, tl, f"strip bracket {k + 1} tab slot"))
    for k, u in enumerate(P.PROP_U):
        for y in ys_prop:
            bh.append(rect(px0 + u, y + tl2 / 2, T, tl2, f"screen prop {k + 1} tab slot"))
    if P.ENABLE_TIE_SLOTS:
        tw, tlen = P.TIE_SLOT
        for (cx, cy, along, span) in wires.tie_pairs():
            off = span / 2 + P.WIRE_R + tw / 2 + 1.0
            for sgn in (-1, 1):
                if along == "y":
                    bh.append(rect(cx + sgn * off, cy, tw, tlen, "cable tie slot"))
                else:
                    bh.append(rect(cx, cy + sgn * off, tlen, tw, "cable tie slot"))
    panels["base_plate"] = Panel("base_plate", "plan view from above", rrect(P.BASE_W, P.BASE_D, P.BASE_RADIUS), bh,
                                 [("base_plate", (0, 0, 0))], (1, 0, 0), (0, 1, 0), None, "base plate")
    return panels


# ------------------------------------------------------------- 3D solids --
def panel_solid(p: Panel, origin):
    ud, vd = p.udir, p.vdir
    n = (ud[1] * vd[2] - ud[2] * vd[1], ud[2] * vd[0] - ud[0] * vd[2], ud[0] * vd[1] - ud[1] * vd[0])
    plane = cq.Plane(origin=origin, xDir=ud, normal=n)
    coords = list(p.outline.exterior.coords)[:-1]
    wp = cq.Workplane(plane).polyline(coords).close().extrude(T)
    for hl in p.holes:
        if hl.kind == "circle":
            cut = cq.Workplane(plane).center(hl.cx, hl.cy).circle(hl.w / 2).extrude(T)
        else:
            cut = cq.Workplane(plane).center(hl.cx, hl.cy).rect(hl.w, hl.h).extrude(T)
        wp = wp.cut(cut)
    s = wp.val()
    if p.xf:
        ang, (tx, ty, tz) = p.xf
        s = s.rotate(V(0, 0, 0), V(1, 0, 0), ang).translate(V(tx, ty, tz))
    return s
