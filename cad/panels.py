"""Panel geometry: finger-jointed outlines, holes, and the matching 3D solids.

Every panel is described in its own "view" coordinates (u, v), the way you
would look at it from outside. The same 2D model feeds the 3D STEP solids,
the DXF laser files and the dimensioned drawings, so they cannot disagree.
"""
import math
from dataclasses import dataclass, field

import cadquery as cq
from shapely.geometry import box as sbox
from shapely.ops import transform, unary_union

import params as P

W, D, H, T = P.CASE_W, P.CASE_D, P.CASE_H, P.T


# ---------------------------------------------------------------- holes --
@dataclass
class Hole:
    kind: str            # "circle" or "rect"
    cx: float
    cy: float
    w: float             # diameter for circles
    h: float = 0.0
    label: str = ""
    assumed: bool = False
    vent: bool = False   # vent holes are exempt from the hole to hole spacing rule

    def shape(self):
        if self.kind == "circle":
            from shapely.geometry import Point
            return Point(self.cx, self.cy).buffer(self.w / 2.0, 64)
        return sbox(self.cx - self.w / 2, self.cy - self.h / 2,
                    self.cx + self.w / 2, self.cy + self.h / 2)


def circle(cx, cy, d, label, assumed=False):
    return Hole("circle", cx, cy, d, 0.0, label, assumed)


def rect(cx, cy, w, h, label, assumed=False):
    return Hole("rect", cx, cy, w, h, label, assumed)


# --------------------------------------------------------------- panels --
@dataclass
class Panel:
    name: str
    view: str                      # description of the view the (u,v) axes are drawn in
    outline: object                # shapely Polygon in view coords
    holes: list = field(default_factory=list)
    origin: tuple = (0, 0, 0)      # world position of view (0,0) on the extrusion start face
    udir: tuple = (1, 0, 0)
    vdir: tuple = (0, 1, 0)
    thickness_dir: int = 1         # kept for clarity: extrusion is always along udir x vdir

    @property
    def bounds(self):
        return self.outline.bounds

    @property
    def size(self):
        b = self.bounds
        return (b[2] - b[0], b[3] - b[1])


def finger_count(length):
    """Odd number of equal fingers closest to FINGER_W."""
    n = max(3, round(length / P.FINGER_W))
    if n % 2 == 0:
        # pick the odd neighbour that keeps the width closest to the target
        lo, hi = n - 1, n + 1
        n = lo if abs(length / lo - P.FINGER_W) <= abs(length / hi - P.FINGER_W) else hi
    return n


def segments(lo, hi):
    n = finger_count(hi - lo)
    w = (hi - lo) / n
    return [(lo + i * w, lo + (i + 1) * w) for i in range(n)]


# A strip is the T x T x L bar along one case edge where two panels interlock.
# even = panel owning segments 0, 2, 4 ...; odd = panel owning segments 1, 3, ...
# cross = (xrange, yrange, zrange) with the strip axis range replaced by its span.
def edge_strips():
    S = []
    # horizontal edges on top and bottom plates
    for zname, (z0, z1) in (("top", (H - T, H)), ("bottom", (0, T))):
        S.append(dict(name=f"{zname}-front", axis="x", span=(T, W - T), x=None, y=(0, T), z=(z0, z1), even=zname, odd="front"))
        S.append(dict(name=f"{zname}-back", axis="x", span=(T, W - T), x=None, y=(D - T, D), z=(z0, z1), even=zname, odd="back"))
        S.append(dict(name=f"{zname}-left", axis="y", span=(T, D - T), x=(0, T), y=None, z=(z0, z1), even=zname, odd="left"))
        S.append(dict(name=f"{zname}-right", axis="y", span=(T, D - T), x=(W - T, W), y=None, z=(z0, z1), even=zname, odd="right"))
    # vertical edges
    for nm, ys, a, b in (("front", (0, T), "front", None), ("back", (D - T, D), "back", None)):
        S.append(dict(name=f"{nm}-left", axis="z", span=(T, H - T), x=(0, T), y=ys, z=None, even=nm, odd="left"))
        S.append(dict(name=f"{nm}-right", axis="z", span=(T, H - T), x=(W - T, W), y=ys, z=None, even=nm, odd="right"))
    return S


def corner_cubes():
    """The 8 T x T x T corner cubes. Top and bottom plates own them."""
    out = []
    for zname, (z0, z1) in (("top", (H - T, H)), ("bottom", (0, T))):
        for x in ((0, T), (W - T, W)):
            for y in ((0, T), (D - T, D)):
                out.append(dict(owner=zname, x=x, y=y, z=(z0, z1)))
    return out


PLANE_AXES = {"top": ("x", "y"), "bottom": ("x", "y"), "front": ("x", "z"),
              "back": ("x", "z"), "left": ("y", "z"), "right": ("y", "z")}
SLAB = {"top": ("z", (H - T, H)), "bottom": ("z", (0, T)), "front": ("y", (0, T)),
        "back": ("y", (D - T, D)), "left": ("x", (0, T)), "right": ("x", (W - T, W))}
CORE = {"top": [(T, W - T), (T, D - T)], "bottom": [(T, W - T), (T, D - T)],
        "front": [(T, W - T), (T, H - T)], "back": [(T, W - T), (T, H - T)],
        "left": [(T, D - T), (T, H - T)], "right": [(T, D - T), (T, H - T)]}


def owned_rects(panel):
    """Rectangles (in this panel's world-plane axes) that the panel owns on the edge strips."""
    a_ax, b_ax = PLANE_AXES[panel]
    rects = []
    for s in edge_strips():
        if panel not in (s["even"], s["odd"]):
            continue
        mine = 0 if s["even"] == panel else 1
        ax = s["axis"]
        assert ax in (a_ax, b_ax), (panel, s["name"])
        # the strip's cross range on the panel's thickness axis must be the panel slab
        t_ax, t_rng = SLAB[panel]
        assert tuple(s[t_ax]) == tuple(t_rng), (panel, s["name"], t_ax)
        other = b_ax if ax == a_ax else a_ax
        for i, (lo, hi) in enumerate(segments(*s["span"])):
            if i % 2 != mine:
                continue
            r = {ax: (lo, hi), other: s[other]}
            rects.append((r[a_ax], r[b_ax]))
    for c in corner_cubes():
        if c["owner"] == panel:
            rects.append((c[a_ax], c[b_ax]))
    return rects


def world_outline(panel):
    (a0, a1), (b0, b1) = CORE[panel]
    geoms = [sbox(a0, b0, a1, b1)]
    for (ra, rb) in owned_rects(panel):
        geoms.append(sbox(ra[0], rb[0], ra[1], rb[1]))
    return unary_union(geoms).simplify(1e-9)


# world-plane (a, b) -> view (u, v)
def _view_fn(panel):
    if panel == "back":
        return lambda a, b, z=None: (W - a, b)
    if panel == "left":
        return lambda a, b, z=None: (D - a, b)
    return lambda a, b, z=None: (a, b)


def view_outline(panel):
    f = _view_fn(panel)
    return transform(lambda xs, ys, zs=None: tuple(zip(*[f(x, y) for x, y in zip(xs, ys)])), world_outline(panel))


PLACEMENT = {
    # origin of view (0,0) on the extrusion start face, u direction, v direction.
    # Extrusion runs along u x v and ends on the far face of the slab.
    "top": ((0, 0, H - T), (1, 0, 0), (0, 1, 0), "outside view from above"),
    "bottom": ((0, 0, 0), (1, 0, 0), (0, 1, 0), "plan view from above (inside face up)"),
    "front": ((0, T, 0), (1, 0, 0), (0, 0, 1), "outside view from the front"),
    "back": ((W, D - T, 0), (-1, 0, 0), (0, 0, 1), "outside view from the back"),
    "left": ((T, D, 0), (0, -1, 0), (0, 0, 1), "outside view from the left"),
    "right": ((W - T, 0, 0), (0, 1, 0), (0, 0, 1), "outside view from the right"),
}


def view_to_world(panel, u, v, face="start"):
    o, ud, vd, _ = PLACEMENT[panel]
    return tuple(o[i] + ud[i] * u + vd[i] * v for i in range(3))


# ---------------------------------------------------------- hole layouts --
def x_to_u(panel, x):
    """World X to view U for the back panel (mirrored); identity otherwise."""
    return W - x if panel == "back" else x


def build_holes():
    h = {k: [] for k in PLACEMENT}

    # ---- front panel (u = x, v = z)
    fr = h["front"]
    fr.append(circle(P.GREEN_X, P.BTN_Z, P.GREEN_HOLE, "green button"))
    fr.append(circle(P.RED_X, P.BTN_Z, P.RED_HOLE, "red button"))
    fr.append(circle(P.KILL_X, P.BTN_Z, P.KILL_HOLE, "kill switch"))
    fr.append(circle(P.PTT_X, P.BTN_Z, P.PTT_HOLE, "push to talk"))
    fr.append(circle(P.TOGGLE_X, P.BTN_Z, P.TOGGLE_HOLE, "EN/ZH toggle"))
    x0 = W / 2 - 1.5 * P.LED_PITCH
    for i, nm in enumerate(P.LED_NAMES):
        fr.append(circle(x0 + i * P.LED_PITCH, P.LED_Z, P.LED_HOLE, f"LED {nm} ({P.LED_COLOURS[i]})"))
    if P.ENABLE_SPEAKER_GRILLE:
        gx0 = W / 2 - (P.GRILLE_COUNT - 1) * P.GRILLE_PITCH / 2
        for i in range(P.GRILLE_COUNT):
            fr.append(rect(gx0 + i * P.GRILLE_PITCH, P.GRILLE_Z, P.GRILLE_SLOT_L, P.GRILLE_SLOT_W, f"grille {i + 1}"))

    # ---- top panel (u = x, v = y)
    tp = h["top"]
    if P.SCREEN_MODE == "window_under":
        wx = P.SCREEN_CX + P.SCREEN_VIS_OFFSET_X
        wy = P.SCREEN_CY + P.SCREEN_VIS_OFFSET_Y
        tp.append(rect(wx, wy, P.SCREEN_VIS_W, P.SCREEN_VIS_D, "screen window (visible area)", assumed=True))
        for sx in (-1, 1):
            for sy in (-1, 1):
                hx = P.SCREEN_CX + sx * (P.SCREEN_MODULE_W / 2 - P.SCREEN_HOLE_INSET)
                hy = P.SCREEN_CY + sy * (P.SCREEN_MODULE_D / 2 - P.SCREEN_HOLE_INSET)
                tp.append(circle(hx, hy, P.SCREEN_HOLE_D, "screen screw", assumed=True))
    else:
        tp.append(rect(P.SCREEN_CX, P.SCREEN_CY, P.SCREEN_MODULE_W + 2 * P.SCREEN_BEZEL_CLEARANCE,
                       P.SCREEN_MODULE_D + 2 * P.SCREEN_BEZEL_CLEARANCE, "screen cutout (full module, bezel mode)"))

    # ---- back panel (u = W - x, v = z)
    bk = h["back"]
    z = P.CUT_Z
    bk.append(rect(W - P.HDMI0_CUT_X, z, *P.HDMI_CUT, "micro-HDMI 0 cable (main monitor)", assumed=True))
    bk.append(rect(W - P.SCREEN_PWR_CUT_X, z, *P.SCREEN_PWR_CUT, "mini screen USB power cable", assumed=True))
    bk.append(rect(W - P.USBC_CUT_X, z, *P.USBC_CUT, "Pi USB-C power", assumed=True))
    bk.append(rect(W - P.MIC_CUT_X, z, *P.MIC_CUT, "mic USB cable", assumed=True))
    if P.ENABLE_FAN:
        u = W - P.FAN_CX
        screws = []
        for sx in (-1, 1):
            for sz in (-1, 1):
                screws.append(circle(u + sx * P.FAN_HOLE_SPACING / 2, P.FAN_CZ + sz * P.FAN_HOLE_SPACING / 2,
                                     P.FAN_SCREW_D, "fan screw"))
        bk.extend(screws)
        FAN_INFO.clear()
        FAN_INFO.update(fan_grille(u, P.FAN_CZ, screws))
        bk.extend(FAN_INFO["holes"])

    # ---- side panels: intake slots low down
    if P.ENABLE_SIDE_VENTS:
        for side in ("left", "right"):
            for zr in P.VENT_ROWS_Z:
                for uc in P.VENT_COLS_U:
                    h[side].append(rect(uc, zr, P.VENT_SLOT_L, P.VENT_SLOT_W, "vent"))

    # ---- bottom panel (u = x, v = y)
    bt = h["bottom"]
    x0 = P.PI_X0
    y0 = pi_y0()
    for bx in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SX):
        for by in (P.PI_HOLE_INSET, P.PI_HOLE_INSET + P.PI_HOLE_SY):
            bt.append(circle(x0 + P.PI_L - bx, y0 + P.PI_W - by, P.PI_HOLE_D, "Pi standoff (M2.5)"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            bt.append(circle(P.PERF_CX + sx * (P.PERF_X / 2 - P.PERF_HOLE_INSET),
                             P.PERF_CY + sy * (P.PERF_Y / 2 - P.PERF_HOLE_INSET), P.PERF_HOLE_D, "perfboard standoff (M3)"))
    for fx in (P.FOOT_INSET, W - P.FOOT_INSET):
        for fy in (P.FOOT_INSET, D - P.FOOT_INSET):
            bt.append(circle(fx, fy, P.FOOT_HOLE_D, "rubber foot", assumed=True))
    if P.ENABLE_BOTTOM_VENTS:
        for i in range(4):
            bt.append(rect(P.PI_X0 + 42.5, P.BOTTOM_VENT_Y + i * 10, 60, 4, "bottom vent"))
    return h


FAN_INFO = {}


def fan_grille(cx, cz, screws):
    """Staggered grille of small holes with FAN_GRILLE_WEB between neighbours, across the fan
    area. Keeps MIN_HOLE_GAP to the screw holes. Falls back to one plain opening when the
    open area is below FAN_GRILLE_MIN_RATIO of that opening."""
    r = P.FAN_GRILLE_HOLE_D / 2
    pitch = P.FAN_GRILLE_HOLE_D + P.FAN_GRILLE_WEB
    rowh = pitch * math.sqrt(3) / 2
    best = []
    for ox in (0.0, pitch / 2):
        for oz in (0.0, rowh / 2):
            hs = []
            n = int(P.FAN_AREA_D // pitch) + 2
            for j in range(-n, n + 1):
                for i in range(-n, n + 1):
                    x = cx + ox + i * pitch + (pitch / 2 if j % 2 else 0)
                    z = cz + oz + j * rowh
                    if math.hypot(x - cx, z - cz) + r > P.FAN_AREA_D / 2 + 1e-9:
                        continue
                    h = circle(x, z, P.FAN_GRILLE_HOLE_D, "fan grille")
                    h.vent = True
                    if any(h.shape().distance(s.shape()) < P.MIN_HOLE_GAP + 1e-6 for s in screws):
                        continue
                    hs.append(h)
            if len(hs) > len(best):
                best = hs
    area = len(best) * math.pi * r * r
    plain = math.pi * (P.FAN_PLAIN_OPENING_D / 2) ** 2
    ratio = area / plain
    if ratio >= P.FAN_GRILLE_MIN_RATIO:
        return dict(holes=best, mode="grille", count=len(best), area=area, plain=plain, ratio=ratio)
    h = circle(cx, cz, P.FAN_PLAIN_OPENING_D, "fan opening")
    return dict(holes=[h], mode="plain", count=len(best), area=area, plain=plain, ratio=ratio)


def pi_y0():
    """World Y of the Pi board's front edge (board rotated so the HDMI edge faces back)."""
    return (D - T) - P.PI_BACK_GAP - P.PI_W


def build_panels():
    holes = build_holes()
    panels = {}
    for name, (o, ud, vd, view) in PLACEMENT.items():
        panels[name] = Panel(name, view, view_outline(name), holes[name], o, ud, vd)
    return panels


# ------------------------------------------------------------- 3D solids --
def panel_solid(p: Panel):
    """CadQuery solid at nominal size (no kerf) in world coordinates."""
    ud, vd = p.udir, p.vdir
    n = (ud[1] * vd[2] - ud[2] * vd[1], ud[2] * vd[0] - ud[0] * vd[2], ud[0] * vd[1] - ud[1] * vd[0])
    plane = cq.Plane(origin=p.origin, xDir=ud, normal=n)
    coords = list(p.outline.exterior.coords)[:-1]
    wp = cq.Workplane(plane).polyline(coords).close().extrude(T)
    for hl in p.holes:
        if hl.kind == "circle":
            cut = cq.Workplane(plane).center(hl.cx, hl.cy).circle(hl.w / 2).extrude(T)
        else:
            cut = cq.Workplane(plane).center(hl.cx, hl.cy).rect(hl.w, hl.h).extrude(T)
        wp = wp.cut(cut)
    return wp.val()
