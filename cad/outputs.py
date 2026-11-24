"""File outputs: STEP, DXF (single parts and nested sheets), dimensioned drawings."""
import copy
import math
import os

import cadquery as cq
import ezdxf
from shapely import affinity
from shapely.geometry import box as sbox

import params as P

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def outdir(*sub):
    d = os.path.join(OUT, *sub)
    os.makedirs(d, exist_ok=True)
    return d


# ------------------------------------------------------------------ STEP --
def export_step(parts):
    d_step = outdir("step")
    for p in parts:
        cq.exporters.export(cq.Workplane(obj=p["solid"]), os.path.join(d_step, f"{p['name']}_{P.REV}.step"))
    asm = cq.Assembly(name=f"si_console_{P.REV}")
    for p in parts:
        r, g, b = p["colour"]
        asm.add(p["solid"], name=p["name"], color=cq.Color(r, g, b, p["alpha"]))
    f = os.path.join(OUT, f"si_console_assembly_{P.REV}.step")
    asm.save(f)
    return f


# ------------------------------------------------------------------- DXF --
class Cut:
    """Cut geometry of one part, kerf applied, in sheet coordinates (mm), lower left at (0, 0)."""

    def __init__(self, panel, name=None):
        self.name = name or panel.name
        k = P.KERF / 2.0
        self.outer = panel.outline.buffer(k, join_style=2, mitre_limit=10.0)
        self.circles = []
        self.polys = []
        for h in panel.holes:
            if h.kind == "circle":
                self.circles.append((h.cx, h.cy, h.w / 2.0 - k))
            else:
                self.polys.append(sbox(h.cx - h.w / 2 + k, h.cy - h.h / 2 + k, h.cx + h.w / 2 - k, h.cy + h.h / 2 - k))
        b = self.outer.bounds
        self.shift(-b[0], -b[1])

    def shift(self, dx, dy):
        self.outer = affinity.translate(self.outer, dx, dy)
        self.polys = [affinity.translate(g, dx, dy) for g in self.polys]
        self.circles = [(x + dx, y + dy, r) for x, y, r in self.circles]

    def rot90(self):
        self.outer = affinity.rotate(self.outer, 90, origin=(0, 0))
        self.polys = [affinity.rotate(g, 90, origin=(0, 0)) for g in self.polys]
        self.circles = [(-y, x, r) for x, y, r in self.circles]
        b = self.outer.bounds
        self.shift(-b[0], -b[1])

    @property
    def size(self):
        b = self.outer.bounds
        return b[2] - b[0], b[3] - b[1]

    def write(self, msp, dx=0.0, dy=0.0):
        def poly(coords):
            msp.add_lwpolyline([(x + dx, y + dy) for x, y in coords[:-1]], close=True, dxfattribs={"layer": "CUT"})
        poly(list(self.outer.exterior.coords))
        for g in self.polys:
            poly(list(g.exterior.coords))
        for x, y, r in self.circles:
            msp.add_circle((x + dx, y + dy), r, dxfattribs={"layer": "CUT"})


def _new_doc():
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.layers.add("CUT", color=1)
    doc.layers.add("SHEET", color=8)
    doc.layers.add("LABEL_NOCUT", color=3)
    return doc


def export_dxf(panel_dict):
    d = outdir("dxf")
    cuts = {}
    for name, p in panel_dict.items():
        c = Cut(p)
        cuts[name] = c
        doc = _new_doc()
        c.write(doc.modelspace())
        doc.saveas(os.path.join(d, f"laser_{name}_x{p.qty}_{P.REV}.dxf"))
    return cuts


# --------------------------------------------------------------- nesting --
class MaxRects:
    def __init__(self, w, h):
        self.free = [(0.0, 0.0, w, h)]

    def place(self, w, h):
        best = None
        for (x, y, fw, fh) in self.free:
            if w <= fw + 1e-9 and h <= fh + 1e-9:
                score = (min(fw - w, fh - h), max(fw - w, fh - h))
                if best is None or score < best[0]:
                    best = (score, x, y)
        if best is None:
            return None
        _, px, py = best
        new = []
        for (x, y, fw, fh) in self.free:
            if px >= x + fw or px + w <= x or py >= y + fh or py + h <= y:
                new.append((x, y, fw, fh))
                continue
            if px > x:
                new.append((x, y, px - x, fh))
            if px + w < x + fw:
                new.append((px + w, y, x + fw - px - w, fh))
            if py > y:
                new.append((x, y, fw, py - y))
            if py + h < y + fh:
                new.append((x, py + h, fw, y + fh - py - h))
        self.free = [r for i, r in enumerate(new) if not any(j != i and o[0] <= r[0] + 1e-9 and o[1] <= r[1] + 1e-9 and
                                                             o[0] + o[2] >= r[0] + r[2] - 1e-9 and o[1] + o[3] >= r[1] + r[3] - 1e-9 for j, o in enumerate(new))]
        return px, py


def nest(panel_dict, cuts):
    """Pack every instance on as few sheets as possible. Returns a list of sheets, each a list of
    (instance name, laser part, rotated, x, y, w, h)."""
    g = P.NEST_GAP
    uw, ul = P.SHEET_W - 2 * P.SHEET_MARGIN + g, P.SHEET_L - 2 * P.SHEET_MARGIN + g
    items = []
    for key, p in panel_dict.items():
        w, h = cuts[key].size
        for (inst, _) in p.instances:
            items.append((inst, key, w, h))
    best = None
    orders = [sorted(items, key=lambda t: -t[2] * t[3]), sorted(items, key=lambda t: -max(t[2], t[3])), sorted(items, key=lambda t: -t[3]),
              sorted(items, key=lambda t: -t[2])]
    for order in orders:
        sheets = []
        ok = True
        for (inst, key, w, h) in order:
            placed = False
            for sh in sheets:
                for (ww, hh, rot) in ((w, h, False), (h, w, True)):
                    pos = sh["mr"].place(ww + g, hh + g)
                    if pos:
                        sh["items"].append((inst, key, rot, pos[0], pos[1], ww, hh))
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                sh = dict(mr=MaxRects(uw, ul), items=[])
                sheets.append(sh)
                for (ww, hh, rot) in ((w, h, False), (h, w, True)):
                    pos = sh["mr"].place(ww + g, hh + g)
                    if pos:
                        sh["items"].append((inst, key, rot, pos[0], pos[1], ww, hh))
                        placed = True
                        break
                if not placed:
                    ok = False
                    break
        if ok:
            res = [s["items"] for s in sheets]
            if best is None or len(res) < len(best):
                best = res
    if best is None:
        raise RuntimeError("a part does not fit on the sheet")
    return best


def export_nested(cuts, sheets):
    d = outdir("dxf")
    files = []
    for i, placed in enumerate(sheets, 1):
        doc = _new_doc()
        msp = doc.modelspace()
        msp.add_lwpolyline([(0, 0), (P.SHEET_W, 0), (P.SHEET_W, P.SHEET_L), (0, P.SHEET_L)], close=True, dxfattribs={"layer": "SHEET"})
        for (inst, key, rot, x, y, w, h) in placed:
            c = copy.deepcopy(cuts[key])
            if rot:
                c.rot90()
            ox, oy = P.SHEET_MARGIN + x, P.SHEET_MARGIN + y
            c.write(msp, ox, oy)
            msp.add_text(inst, dxfattribs={"layer": "LABEL_NOCUT", "height": 5}).set_placement((ox + 6, oy + 6))
        f = os.path.join(d, f"nested_sheet_{i}_{P.REV}.dxf")
        doc.saveas(f)
        files.append(f)
    return files


def nest_preview(cuts, sheets):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(sheets)
    fig, axes = plt.subplots(1, n, figsize=(4.4 * n, 6.4), squeeze=False)
    for i, (ax, placed) in enumerate(zip(axes[0], sheets), 1):
        ax.add_patch(plt.Rectangle((0, 0), P.SHEET_W, P.SHEET_L, fill=False, ec="#888"))
        for (inst, key, rot, x, y, w, h) in placed:
            c = copy.deepcopy(cuts[key])
            if rot:
                c.rot90()
            ox, oy = P.SHEET_MARGIN + x, P.SHEET_MARGIN + y
            xs, ys = c.outer.exterior.xy
            ax.fill([a + ox for a in xs], [b + oy for b in ys], fc="#cfe8f5", ec="#c00", lw=0.8)
            for gq in c.polys:
                hx, hy = gq.exterior.xy
                ax.plot([a + ox for a in hx], [b + oy for b in hy], color="#c00", lw=0.6)
            for cx, cy, r in c.circles:
                ax.add_patch(plt.Circle((cx + ox, cy + oy), r, fill=False, ec="#c00", lw=0.6))
            ax.text(ox + w / 2, oy + h / 2, inst, ha="center", va="center", fontsize=7, rotation=90 if h > 2 * w else 0)
        ax.set_xlim(-5, P.SHEET_W + 5)
        ax.set_ylim(-5, P.SHEET_L + 5)
        ax.set_aspect("equal")
        ax.set_title(f"Sheet {i} of {n} ({P.SHEET_W:g} x {P.SHEET_L:g} mm)", fontsize=9)
        ax.tick_params(labelsize=6)
    fig.tight_layout()
    f = os.path.join(outdir("dxf"), f"nested_layout_{P.REV}.png")
    fig.savefig(f, dpi=110)
    plt.close(fig)
    return f


# --------------------------------------------------------------- drawings --
def export_drawings(panel_dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    matplotlib.rcParams["svg.fonttype"] = "none"
    matplotlib.rcParams["pdf.fonttype"] = 42
    d = outdir("drawings")
    pdf_path = os.path.join(d, f"laser_parts_{P.REV}.pdf")
    with PdfPages(pdf_path) as pdf:
        for name, p in panel_dict.items():
            fig = draw_panel(plt, p)
            fig.savefig(os.path.join(d, f"laser_{name}_{P.REV}.svg"))
            pdf.savefig(fig)
            plt.close(fig)
    return pdf_path


def draw_panel(plt, p):
    from matplotlib.patches import Circle, Polygon as MPoly, Rectangle
    PW, PH = 420.0, 297.0
    fig = plt.figure(figsize=(PW / 25.4, PH / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, PW)
    ax.set_ylim(0, PH)
    ax.axis("off")
    b = p.outline.bounds
    w, h = b[2] - b[0], b[3] - b[1]
    ORANGE, INK, DIM = "#e07800", "#111", "#0a58a8"
    s = min(330.0 / w, 120.0 / h)
    ox = 50.0 + (330.0 - w * s) / 2 - b[0] * s
    oy = 112.0 + (120.0 - h * s) / 2 - b[1] * s

    def X(u):
        return ox + u * s

    def Y(v):
        return oy + v * s

    def rel(u, v):
        return u - b[0], v - b[1]

    ax.add_patch(Rectangle((8, 8), PW - 16, PH - 16, fill=False, ec="#444", lw=0.8))
    xs, ys = p.outline.exterior.xy
    ax.add_patch(MPoly([(X(a), Y(c)) for a, c in zip(xs, ys)], closed=True, fc="#e8f3fa", ec=INK, lw=1.0))
    rows = []
    for i, hl in enumerate(p.holes, 1):
        col = ORANGE if hl.assumed else INK
        if hl.kind == "circle":
            ax.add_patch(Circle((X(hl.cx), Y(hl.cy)), hl.w / 2 * s, fc="white", ec=col, lw=0.9))
            size = f"dia {hl.w:g}"
        else:
            ax.add_patch(Rectangle((X(hl.cx - hl.w / 2), Y(hl.cy - hl.h / 2)), hl.w * s, hl.h * s, fc="white", ec=col, lw=0.9))
            size = f"{hl.w:g} x {hl.h:g}"
        ax.plot([X(hl.cx) - 1.2, X(hl.cx) + 1.2], [Y(hl.cy)] * 2, color=col, lw=0.4)
        ax.plot([X(hl.cx)] * 2, [Y(hl.cy) - 1.2, Y(hl.cy) + 1.2], color=col, lw=0.4)
        rows.append((i, hl.label, size, hl.cx - b[0], hl.cy - b[1], hl.assumed))
    for (i, label, size, cx, cy, asm) in rows:
        hl = p.holes[i - 1]
        r = (hl.w / 2 if hl.kind == "circle" else max(hl.w, hl.h) / 2) * s
        ax.text(X(cx + b[0]) + r + 0.8, Y(cy + b[1]) + r + 0.5, str(i) + ("A" if asm else ""), fontsize=5, color=ORANGE if asm else INK, ha="left", va="bottom")

    def dim(x0, y0, x1, y1, txt, rot=0):
        ax.annotate("", xy=(x0, y0), xytext=(x1, y1), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.6, shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, txt, color=DIM, fontsize=7, ha="center", va="center", rotation=rot, bbox=dict(fc="white", ec="none", pad=0.6))

    yb = Y(b[1]) - 14.0
    xl = X(b[0]) - 14.0
    dim(X(b[0]), yb, X(b[2]), yb, f"{w:g}")
    dim(xl, Y(b[1]), xl, Y(b[3]), f"{h:g}", rot=90)
    # ordinate dimensions for hole centres, or for outline corners when the part has no holes
    pts = [(r[3] + b[0], r[4] + b[1]) for r in rows]
    if not pts:
        pts = [(x, y) for x, y in zip(xs, ys)]
        # also mark every polygon corner
        for (x, y) in pts:
            ax.plot([X(x)], [Y(y)], marker="o", ms=1.6, color=DIM)
    ux = sorted({round(x - b[0], 1) for x, y in pts})
    uy = sorted({round(y - b[1], 1) for x, y in pts})
    for u in ux:
        ax.plot([X(u + b[0])] * 2, [yb + 3, Y(min(y for x, y in pts if round(x - b[0], 1) == u))], color=DIM, lw=0.25, ls=(0, (3, 2)))
        ax.text(X(u + b[0]), yb + 4.0, f"{u:g}", color=DIM, fontsize=4.6, rotation=90, ha="center", va="bottom")
    for v in uy:
        ax.plot([xl + 3, X(min(x for x, y in pts if round(y - b[1], 1) == v))], [Y(v + b[1])] * 2, color=DIM, lw=0.25, ls=(0, (3, 2)))
        ax.text(xl + 3.5, Y(v + b[1]) + 0.6, f"{v:g}", color=DIM, fontsize=4.6, ha="left", va="bottom")
    ax.text(X(b[0]), Y(b[3]) + 4, f"{p.name.upper()}  x{p.qty}  |  {p.desc}  |  view: {p.view}", fontsize=8, color=INK, ha="left", va="bottom", weight="bold")

    # hole table
    ty = 92.0
    for xx, t in ((16, "No."), (30, "Hole"), (100, "Size"), (130, "X"), (150, "Y"), (166, "Status")):
        ax.text(xx, ty, t, fontsize=6.5, weight="bold")
    ax.plot([14, 200], [ty - 1.2, ty - 1.2], color="#444", lw=0.4)
    n = len(rows)
    ncol = 2 if n > 12 else 1
    per = math.ceil(n / ncol) if n else 1
    for idx, (i, label, size, cx, cy, asm) in enumerate(rows):
        col, row = divmod(idx, per)
        xo = 16 + col * 200
        yy = ty - 5.0 - row * 4.3
        c = ORANGE if asm else INK
        for dx, t in ((0, f"{i}"), (14, label), (84, size), (114, f"{cx:.1f}"), (134, f"{cy:.1f}"), (150, "ASSUMED (A)" if asm else "verified/design")):
            ax.text(xo + dx, yy, t, fontsize=5.6, color=c)
    if not rows:
        ax.text(16, ty - 5, "No holes. Outline corner coordinates are dimensioned on the drawing (blue).", fontsize=6.5)

    notes = [f"SI Console Rev {P.REV}. Material: clear acrylic {P.T:g} mm (thickness ASSUMED, measure the sheet). Quantity to cut: {p.qty}.",
             f"Kerf {P.KERF:g} mm: DXF cut paths are offset by {P.KERF / 2:g} mm; this drawing shows nominal finished sizes. Origin = lower left of the part's bounding box.",
             joint_note(p),
             "Orange and 'A' = ASSUMED dimension, measure with calipers before cutting. Blue = dimension. Hole centres are X,Y from the origin.",
             f"Drawing scale about {s:.2f}:1 on A3. Cut from the DXF, not from this sheet."]
    for k, t in enumerate(notes):
        ax.text(16, 38 - k * 5.0, t, fontsize=6.0, color="#222")
    ax.text(PW - 16, 16, f"{p.name.upper()}  |  Rev {P.REV}  |  {w:g} x {h:g} mm", fontsize=8, ha="right", weight="bold")
    return fig


def joint_note(p):
    if p.name == "control_strip":
        return (f"Mounted {P.STRIP_TILT:g} deg from vertical, leaning back. Four 3 x 15 slots take the tabs of the two strip brackets. "
                f"Control holes: green and red 30.2, kill switch 22.3, PTT and toggle 12.2, LEDs 5.2.")
    if p.name == "screen_plate":
        return f"Mounted {P.SCREEN_TILT:g} deg from vertical, leaning back. Four 3 x 15 slots take the screen prop tabs. Four 2.7 holes for the M2.5 standoffs under the module."
    if p.name == "base_plate":
        return "Slots 3 x 15 take the tabs of the strip brackets and screen props. Slot pairs 3 x 5 are for cable ties. Standoff holes: Pi M2.5 (2.7), perfboard M3 (3.2). Foot holes 4.2."
    return "Side profile. The bottom tab goes through the base plate; the tabs on the sloped edge go through the slots in the plate it holds."
