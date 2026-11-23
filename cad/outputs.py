"""File outputs: STEP, STL, DXF (single panels and nested sheets), dimensioned drawings."""
import math
import os

import cadquery as cq
import ezdxf
from shapely import affinity
from shapely.geometry import Polygon, box as sbox

import params as P
import panels as pn

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def outdir(*sub):
    d = os.path.join(OUT, *sub)
    os.makedirs(d, exist_ok=True)
    return d


# ------------------------------------------------------------ STEP / STL --
def export_step_stl(parts):
    d_step = outdir("step")
    d_stl = outdir("stl")
    files = []
    for p in parts:
        wp = cq.Workplane(obj=p["solid"])
        f = os.path.join(d_step, p["name"] + "_R4.step")
        cq.exporters.export(wp, f)
        files.append(f)
        if p["category"] == "print":
            g = os.path.join(d_stl, p["name"] + "_R4.stl")
            cq.exporters.export(wp, g, tolerance=0.05, angularTolerance=0.1)
            files.append(g)
    asm = cq.Assembly(name="si_console_R4")
    for p in parts:
        r, g, b = p["colour"]
        asm.add(p["solid"], name=p["name"], color=cq.Color(r, g, b, p["alpha"]))
    f = os.path.join(OUT, "si_console_assembly_R4.step")
    asm.save(f)
    files.append(f)
    return files


# ------------------------------------------------------------------- DXF --
class Cut:
    """Cut geometry of one panel, kerf applied, in sheet coordinates (mm)."""

    def __init__(self, panel, name=None):
        self.name = name or panel.name
        k = P.KERF / 2.0
        outer = panel.outline.buffer(k, join_style=2, mitre_limit=10.0)
        self.outer = outer
        self.circles = []   # (cx, cy, r)
        self.polys = []     # shapely Polygon (hole polygons)
        for h in panel.holes:
            if h.kind == "circle":
                self.circles.append((h.cx, h.cy, h.w / 2.0 - k))
            else:
                self.polys.append(sbox(h.cx - h.w / 2 + k, h.cy - h.h / 2 + k, h.cx + h.w / 2 - k, h.cy + h.h / 2 - k))
        # shift so the kerf-offset outline starts at (0, 0)
        b = outer.bounds
        self.shift(-b[0], -b[1])

    def shift(self, dx, dy):
        self.outer = affinity.translate(self.outer, dx, dy)
        self.polys = [affinity.translate(g, dx, dy) for g in self.polys]
        self.circles = [(x + dx, y + dy, r) for x, y, r in self.circles]

    def rot90(self):
        """Rotate 90 degrees counter clockwise about the origin, then move back to the positive quadrant."""
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
    doc.layers.add("CUT", color=1)           # red: cut through
    doc.layers.add("SHEET", color=8)         # grey: sheet outline, do not cut
    doc.layers.add("LABEL_NOCUT", color=3)   # green: part names, do not cut
    return doc


def export_dxf(panel_dict):
    d = outdir("dxf")
    files = []
    cuts = {}
    for name, p in panel_dict.items():
        c = Cut(p)
        cuts[name] = c
        doc = _new_doc()
        c.write(doc.modelspace())
        f = os.path.join(d, f"panel_{name}_R4.dxf")
        doc.saveas(f)
        files.append(f)
    return files, cuts


# ---------------------------------------------------------------- nesting --
def nest(cuts):
    """Shelf packing of the panels' bounding boxes onto sheets. Returns a list of sheets,
    each a list of (name, rotated, x, y, w, h)."""
    uw = P.SHEET_W - 2 * P.SHEET_MARGIN
    ul = P.SHEET_L - 2 * P.SHEET_MARGIN
    items = []
    for n, c in cuts.items():
        w, h = c.size
        items.append((n, w, h))
    items.sort(key=lambda t: -t[1] * t[2])
    sheets = []   # each: dict(shelves=[dict(y,h,x)], placed=[])

    def try_place(sh, n, w, h, rot):
        for s in sh["shelves"]:
            if h <= s["h"] + 1e-9 and s["x"] + w <= uw + 1e-9:
                sh["placed"].append((n, rot, s["x"], s["y"], w, h))
                s["x"] += w + P.NEST_GAP
                return True
        used = sh["shelves"][-1]["y"] + sh["shelves"][-1]["h"] + P.NEST_GAP if sh["shelves"] else 0.0
        if used + h <= ul + 1e-9 and w <= uw + 1e-9:
            sh["shelves"].append(dict(y=used, h=h, x=w + P.NEST_GAP))
            sh["placed"].append((n, rot, 0.0, used, w, h))
            return True
        return False

    for n, w, h in items:
        done = False
        # prefer the orientation with the long side along the sheet length
        orients = [(h, w, True), (w, h, False)] if w > h else [(w, h, False), (h, w, True)]
        for sh in sheets:
            for ww, hh, rot in orients:
                if try_place(sh, n, ww, hh, rot):
                    done = True
                    break
            if done:
                break
        if not done:
            sh = dict(shelves=[], placed=[])
            sheets.append(sh)
            for ww, hh, rot in orients:
                if try_place(sh, n, ww, hh, rot):
                    done = True
                    break
        if not done:
            raise RuntimeError(f"panel {n} does not fit on a {P.SHEET_W} x {P.SHEET_L} sheet")
    return [s["placed"] for s in sheets]


def export_nested(cuts, sheets):
    d = outdir("dxf")
    files = []
    for i, placed in enumerate(sheets, 1):
        doc = _new_doc()
        msp = doc.modelspace()
        msp.add_lwpolyline([(0, 0), (P.SHEET_W, 0), (P.SHEET_W, P.SHEET_L), (0, P.SHEET_L)], close=True, dxfattribs={"layer": "SHEET"})
        for (n, rot, x, y, w, h) in placed:
            c = Cut_copy(cuts[n])
            if rot:
                c.rot90()
            ox, oy = P.SHEET_MARGIN + x, P.SHEET_MARGIN + y
            c.write(msp, ox, oy)
            msp.add_text(n.upper(), dxfattribs={"layer": "LABEL_NOCUT", "height": 6}).set_placement((ox + 8, oy + h / 2))
        f = os.path.join(d, f"nested_sheet_{i}_R4.dxf")
        doc.saveas(f)
        files.append(f)
    return files


def Cut_copy(c):
    import copy
    return copy.deepcopy(c)


def nest_preview(cuts, sheets):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(sheets)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 6.2), squeeze=False)
    for i, (ax, placed) in enumerate(zip(axes[0], sheets), 1):
        ax.add_patch(plt.Rectangle((0, 0), P.SHEET_W, P.SHEET_L, fill=False, ec="#888"))
        for (nm, rot, x, y, w, h) in placed:
            c = Cut_copy(cuts[nm])
            if rot:
                c.rot90()
            ox, oy = P.SHEET_MARGIN + x, P.SHEET_MARGIN + y
            xs, ys = c.outer.exterior.xy
            ax.fill([a + ox for a in xs], [b + oy for b in ys], fc="#cfe8f5", ec="#c00", lw=0.8)
            for g in c.polys:
                hx, hy = g.exterior.xy
                ax.plot([a + ox for a in hx], [b + oy for b in hy], color="#c00", lw=0.6)
            for cx, cy, r in c.circles:
                ax.add_patch(plt.Circle((cx + ox, cy + oy), r, fill=False, ec="#c00", lw=0.6))
            ax.text(ox + w / 2, oy + h / 2, nm, ha="center", va="center", fontsize=9)
        ax.set_xlim(-5, P.SHEET_W + 5)
        ax.set_ylim(-5, P.SHEET_L + 5)
        ax.set_aspect("equal")
        ax.set_title(f"Sheet {i} of {n} ({P.SHEET_W:g} x {P.SHEET_L:g} mm)", fontsize=9)
        ax.tick_params(labelsize=6)
    fig.tight_layout()
    f = os.path.join(outdir("dxf"), "nested_layout_R4.png")
    fig.savefig(f, dpi=110)
    plt.close(fig)
    return f


# ---------------------------------------------------------------- drawings --
def export_drawings(panel_dict, assumed_names):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    matplotlib.rcParams["svg.fonttype"] = "none"
    matplotlib.rcParams["pdf.fonttype"] = 42
    d = outdir("drawings")
    files = []
    pdf_path = os.path.join(d, "panels_R4.pdf")
    with PdfPages(pdf_path) as pdf:
        for name, p in panel_dict.items():
            fig = draw_panel(plt, p, assumed_names)
            f = os.path.join(d, f"panel_{name}_R4.svg")
            fig.savefig(f)
            pdf.savefig(fig)
            plt.close(fig)
            files.append(f)
    files.append(pdf_path)
    return files


def draw_panel(plt, p, assumed_names):
    from matplotlib.patches import Circle, Polygon as MPoly, Rectangle
    PW, PH = 420.0, 297.0           # A3 landscape, paper mm
    fig = plt.figure(figsize=(PW / 25.4, PH / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, PW)
    ax.set_ylim(0, PH)
    ax.axis("off")
    b = p.outline.bounds
    w, h = b[2] - b[0], b[3] - b[1]
    ORANGE, INK, DIM = "#e07800", "#111", "#0a58a8"
    # drawing area for the panel: paper x 30..400, y 105..255
    s = min(340.0 / w, 120.0 / h)
    ox = 40.0 + (340.0 - w * s) / 2 - b[0] * s
    oy = 110.0 + (120.0 - h * s) / 2 - b[1] * s

    def X(u):
        return ox + u * s

    def Y(v):
        return oy + v * s

    ax.add_patch(Rectangle((8, 8), PW - 16, PH - 16, fill=False, ec="#444", lw=0.8))
    xs, ys = p.outline.exterior.xy
    ax.add_patch(MPoly([(X(a), Y(c)) for a, c in zip(xs, ys)], closed=True, fc="#e8f3fa", ec=INK, lw=1.0))
    rows = []
    for i, hl in enumerate(p.holes, 1):
        asm = hl.assumed
        col = ORANGE if asm else INK
        if hl.kind == "circle":
            ax.add_patch(Circle((X(hl.cx), Y(hl.cy)), hl.w / 2 * s, fc="white", ec=col, lw=0.9))
            size = f"dia {hl.w:g}"
        else:
            ax.add_patch(Rectangle((X(hl.cx - hl.w / 2), Y(hl.cy - hl.h / 2)), hl.w * s, hl.h * s, fc="white", ec=col, lw=0.9))
            size = f"{hl.w:g} x {hl.h:g}"
        ax.plot([X(hl.cx) - 1.5, X(hl.cx) + 1.5], [Y(hl.cy)] * 2, color=col, lw=0.4)
        ax.plot([X(hl.cx)] * 2, [Y(hl.cy) - 1.5, Y(hl.cy) + 1.5], color=col, lw=0.4)
        rows.append((i, hl.label, size, hl.cx, hl.cy, asm))

    # number tags: small, beside each hole
    for (i, label, size, cx, cy, asm) in rows:
        hl = p.holes[i - 1]
        r = (hl.w / 2 if hl.kind == "circle" else max(hl.w, hl.h) / 2) * s
        ax.text(X(cx) + r + 1.0, Y(cy) + r + 0.8, str(i) + ("A" if asm else ""), fontsize=5.5, color=ORANGE if asm else INK, ha="left", va="bottom")

    # overall dimensions
    def dim(x0, y0, x1, y1, txt, off=(0, 0), rot=0):
        ax.annotate("", xy=(x0, y0), xytext=(x1, y1), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.6, shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], txt, color=DIM, fontsize=7, ha="center", va="center", rotation=rot,
                bbox=dict(fc="white", ec="none", pad=0.6))

    yb = Y(b[1]) - 14.0
    dim(X(b[0]), yb, X(b[2]), yb, f"{w:g}")
    xl = X(b[0]) - 14.0
    dim(xl, Y(b[1]), xl, Y(b[3]), f"{h:g}", rot=90)
    # ordinate dimensions: x positions below, y positions on the left
    ux = sorted({round(r[3], 2) for r in rows})
    uy = sorted({round(r[4], 2) for r in rows})
    for u in ux:
        ax.plot([X(u), X(u)], [yb + 3, Y(min(r[4] for r in rows if round(r[3], 2) == u))], color=DIM, lw=0.25, ls=(0, (3, 2)))
        ax.text(X(u), yb + 4.0, f"{u:g}", color=DIM, fontsize=4.8, rotation=90, ha="center", va="bottom")
    for v in uy:
        ax.plot([xl + 3, X(min(r[3] for r in rows if round(r[4], 2) == v))], [Y(v), Y(v)], color=DIM, lw=0.25, ls=(0, (3, 2)))
        ax.text(xl + 3.5, Y(v) + 0.6, f"{v:g}", color=DIM, fontsize=4.8, ha="left", va="bottom")
    ax.text(X(b[0]), Y(b[3]) + 4, f"{p.name.upper()} PANEL, {p.view}. Origin = bottom left of the view. All sizes mm, nominal (no kerf).",
            fontsize=8, color=INK, ha="left", va="bottom", weight="bold")

    # hole table
    ty = 92.0
    ax.text(16, ty, "No.", fontsize=6.5, weight="bold")
    ax.text(30, ty, "Hole", fontsize=6.5, weight="bold")
    ax.text(100, ty, "Size", fontsize=6.5, weight="bold")
    ax.text(130, ty, "X", fontsize=6.5, weight="bold")
    ax.text(150, ty, "Y", fontsize=6.5, weight="bold")
    ax.text(166, ty, "Status", fontsize=6.5, weight="bold")
    ax.plot([14, 200], [ty - 1.2, ty - 1.2], color="#444", lw=0.4)
    n = len(rows)
    ncol = 2 if n > 12 else 1
    per = math.ceil(n / ncol)
    for idx, (i, label, size, cx, cy, asm) in enumerate(rows):
        col, row = divmod(idx, per)
        xo = 16 + col * 200 if ncol == 2 else 16
        if col == 1 and row == 0:
            pass
        yy = ty - 5.0 - row * 4.6
        c = ORANGE if asm else INK
        tx = xo
        ax.text(tx, yy, f"{i}", fontsize=5.8, color=c)
        ax.text(tx + 14, yy, label, fontsize=5.8, color=c)
        ax.text(tx + 84, yy, size, fontsize=5.8, color=c)
        ax.text(tx + 114, yy, f"{cx:.1f}", fontsize=5.8, color=c)
        ax.text(tx + 134, yy, f"{cy:.1f}", fontsize=5.8, color=c)
        ax.text(tx + 150, yy, "ASSUMED (A)" if asm else "verified/design", fontsize=5.8, color=c)

    # title block
    fingers = finger_note(p.name)
    notes = [f"SI Console Rev {P.REV}. Material: clear acrylic {P.T:g} mm (thickness is ASSUMED, measure the sheet).",
             f"Kerf {P.KERF:g} mm: the DXF cut paths are offset by {P.KERF / 2:g} mm, this drawing shows nominal finished sizes.",
             fingers,
             "Orange and 'A' = ASSUMED dimension, measure with calipers before cutting. Blue = dimension. Hole centres are X,Y from the view's bottom left.",
             ("Overall height includes the 3 mm finger tabs top and bottom; the face between the top and bottom plates is %g mm." % (P.CASE_H - 2 * P.T)) if panel_vertical(p.name) else "Plates are the full 360 x 240 footprint; neighbouring panels fit into the notched edges.",
             f"Drawing scale about {s:.2f}:1 on A3. Cut from the DXF, not from this sheet."]
    for k, t in enumerate(notes):
        ax.text(16, 38 - k * 5.0, t, fontsize=6.2, color="#222")
    ax.text(PW - 16, 16, f"{p.name.upper()}  |  Rev {P.REV}  |  {w:g} x {h:g} mm", fontsize=8, ha="right", weight="bold")
    return fig


def panel_vertical(name):
    return name in ("front", "back", "left", "right")


def finger_note(panel):
    parts = []
    seen = set()
    for st in pn.edge_strips():
        if panel in (st["even"], st["odd"]):
            segs = pn.segments(*st["span"])
            other = st["odd"] if st["even"] == panel else st["even"]
            mine = len([i for i in range(len(segs)) if (i % 2 == 0) == (st["even"] == panel)])
            parts.append(f"{other}: {len(segs)} x {segs[0][1] - segs[0][0]:.2f} ({mine} tabs on this panel)")
    return "Finger joints (count x width): " + "; ".join(parts)
