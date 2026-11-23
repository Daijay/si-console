"""PNG renders with VTK (offscreen) plus labelled call-outs drawn with Pillow."""
import math
import os

import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont
from vtk.util import numpy_support

import params as P

W, D, H, T = P.CASE_W, P.CASE_D, P.CASE_H, P.T
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "renders")


def _polydata(shape, tol=0.4, ang=0.3):
    verts, tris = shape.tessellate(tol, ang)
    pts = vtk.vtkPoints()
    arr = np.array([[v.x, v.y, v.z] for v in verts], dtype=float)
    pts.SetData(numpy_support.numpy_to_vtk(arr, deep=True))
    cells = vtk.vtkCellArray()
    for a, b, c in tris:
        cells.InsertNextCell(3, (a, b, c))
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(cells)
    n = vtk.vtkPolyDataNormals()
    n.SetInputData(pd)
    n.SetFeatureAngle(35)
    n.SplittingOn()
    n.Update()
    return n.GetOutput()


# Where each part moves in the exploded view (dx, dy, dz)
EXPLODE = {
    "case_top_panel": (0, 0, 95), "case_bottom": (0, 0, -55), "case_front_panel": (0, -85, 0),
    "case_back_panel": (0, 85, 0), "case_side_left": (-85, 0, 0), "case_side_right": (85, 0, 0),
    "btn_green": (0, -45, 0), "btn_red": (0, -45, 0), "kill_switch": (0, -45, 0), "btn_ptt": (0, -45, 0),
    "toggle_lang": (0, -45, 0), "led_coord": (0, -45, 0), "led_agent1": (0, -45, 0), "led_agent2": (0, -45, 0),
    "led_guard": (0, -45, 0), "mini_screen": (0, 0, 48), "screen_spacer": (0, 0, 70), "screen_bezel": (0, 0, 130),
    "case_fan": (0, 45, 0), "rubber_feet": (0, 0, -85), "monitor": (0, 95, 0),
    "pi5": (0, 0, 22), "perfboard": (0, 0, 22), "uln2003": (0, 0, 40), "gpio_breakout": (0, 0, 10),
    "pi5_standoffs": (0, 0, 8), "perf_standoffs": (0, 0, 8),
}

# Label shown on renders and the part names that carry it (several parts share one label)
LABELS = [
    ("Top panel (screen window)", ["case_top_panel"]), ("Bottom panel", ["case_bottom"]),
    ("Front panel", ["case_front_panel"]), ("Back panel (cable cutouts, fan)", ["case_back_panel"]),
    ("Left side (intake vents)", ["case_side_left"]), ("Right side (intake vents)", ["case_side_right"]),
    ("Green button", ["btn_green"]), ("Red button", ["btn_red"]), ("Kill switch", ["kill_switch"]),
    ("Push to talk", ["btn_ptt"]), ("EN/ZH toggle", ["toggle_lang"]),
    ("LEDs: COORD, AGENT 1, AGENT 2, GUARD", ["led_coord", "led_agent1", "led_agent2", "led_guard"]),
    ("5 in HDMI screen", ["mini_screen"]), ("Screen spacers (printed)", ["screen_spacer"]), ("Screen bezel (printed)", ["screen_bezel"]),
    ("Raspberry Pi 5 + Active Cooler", ["pi5"]), ("Pi standoffs 10 mm", ["pi5_standoffs"]),
    ("Perfboard on M3 standoffs", ["perfboard", "perf_standoffs"]), ("ULN2003", ["uln2003"]),
    ("GPIO ribbon breakout", ["gpio_breakout"]), ("40 mm exhaust fan", ["case_fan"]),
    ("Rubber feet", ["rubber_feet"]), ("MSI MP165 E6 monitor", ["monitor"]),
]


# Hand-picked anchor points for the clear panels (their centroids sit in the middle of the scene)
PANEL_ANCHORS = {
    "iso": {"case_top_panel": (300, 190, H), "case_front_panel": (28, 0, 118), "case_side_left": (0, 200, 110),
            "case_back_panel": (330, D, 118), "case_side_right": (W, 90, 100), "case_bottom": (330, 40, 0)},
    "front": {"case_front_panel": (20, 0, 20)},
    "top": {"case_top_panel": (330, 205, H)},
    "back": {"case_back_panel": (330, D, 90)},
}
VIEW_NAMES = {
    "front": {"case_front_panel", "btn_green", "btn_red", "kill_switch", "btn_ptt", "toggle_lang", "led_coord", "led_agent1",
              "led_agent2", "led_guard", "monitor", "rubber_feet"},
    "top": {"case_top_panel", "mini_screen", "screen_spacer", "screen_bezel", "pi5", "perfboard", "perf_standoffs", "gpio_breakout",
            "case_fan", "monitor", "uln2003"},
    "back": {"case_back_panel", "case_fan", "monitor", "pi5", "rubber_feet"},
}
EXTRA = {"back": [("Cable cutouts: HDMI, USB-C, mic USB, screen power", (82, D, P.CUT_Z))]}


class Scene:
    def __init__(self, parts, size=P.RENDER_SIZE):
        self.parts = parts
        self.size = size

    def render(self, fname, view, panel_alpha=0.30, explode=False, labels=True, label_set=None, title=None, hide=()):
        w, h = self.size
        ren = vtk.vtkRenderer()
        ren.SetBackground(1, 1, 1)
        ren.SetBackground2(0.88, 0.92, 0.96)
        ren.GradientBackgroundOn()
        rw = vtk.vtkRenderWindow()
        rw.SetOffScreenRendering(1)
        rw.SetSize(w, h)
        rw.SetMultiSamples(0)
        rw.AddRenderer(ren)
        ren.UseDepthPeelingOn()
        ren.SetMaximumNumberOfPeels(60)
        ren.SetOcclusionRatio(0.0)
        rw.SetAlphaBitPlanes(1)

        anchors = {}
        bounds = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
        for p in self.parts:
            if p["name"] in hide:
                continue
            pd = _polydata(p["solid"])
            off = EXPLODE.get(p["name"], (0, 0, 0)) if explode else (0, 0, 0)
            tf = vtk.vtkTransform()
            tf.Translate(*off)
            m = vtk.vtkPolyDataMapper()
            m.SetInputData(pd)
            a = vtk.vtkActor()
            a.SetMapper(m)
            a.SetUserTransform(tf)
            r, g, b = p["colour"]
            a.GetProperty().SetColor(r, g, b)
            alpha = panel_alpha if p["category"] == "panel" else 1.0
            a.GetProperty().SetOpacity(alpha)
            a.GetProperty().SetSpecular(0.35)
            a.GetProperty().SetSpecularPower(40)
            a.GetProperty().SetAmbient(0.25)
            a.GetProperty().SetDiffuse(0.8)
            if p["category"] == "panel":
                a.GetProperty().SetEdgeVisibility(0)
            ren.AddActor(a)
            bb = p["solid"].BoundingBox()
            c = ((bb.xmin + bb.xmax) / 2 + off[0], (bb.ymin + bb.ymax) / 2 + off[1], (bb.zmin + bb.zmax) / 2 + off[2])
            anchors[p["name"]] = (c, bb, off)
            for i, (lo, hi) in enumerate(((bb.xmin, bb.xmax), (bb.ymin, bb.ymax), (bb.zmin, bb.zmax))):
                bounds[2 * i] = min(bounds[2 * i], lo + off[i])
                bounds[2 * i + 1] = max(bounds[2 * i + 1], hi + off[i])

        cx, cy, cz = [(bounds[2 * i] + bounds[2 * i + 1]) / 2 for i in range(3)]
        diag = math.dist((bounds[0], bounds[2], bounds[4]), (bounds[1], bounds[3], bounds[5]))
        cam = ren.GetActiveCamera()
        cam.SetFocalPoint(cx, cy, cz)
        if view == "iso" or view == "iso_back":
            sgn = -1 if view == "iso" else 1
            d = (-0.75, sgn * 1.0, 0.62) if view == "iso" else (0.75, 1.0, 0.62)
            n = math.sqrt(sum(x * x for x in d))
            cam.SetPosition(*(c + diag * 2.15 * x / n for c, x in zip((cx, cy, cz), d)))
            cam.SetViewUp(0, 0, 1)
            cam.SetViewAngle(24)
        else:
            dirs = {"front": ((0, -1, 0), (0, 0, 1)), "back": ((0, 1, 0), (0, 0, 1)), "top": ((0, 0, 1), (0, 1, 0))}[view]
            cam.SetPosition(cx + dirs[0][0] * 2000, cy + dirs[0][1] * 2000, cz + dirs[0][2] * 2000)
            cam.SetViewUp(*dirs[1])
            cam.ParallelProjectionOn()
            ext = {"front": (bounds[1] - bounds[0], bounds[5] - bounds[4]), "back": (bounds[1] - bounds[0], bounds[5] - bounds[4]),
                   "top": (bounds[1] - bounds[0], bounds[3] - bounds[2])}[view]
            aspect = w / h
            cam.SetParallelScale(max(ext[1] / 2, ext[0] / 2 / aspect) * 1.18)
        ren.ResetCameraClippingRange()
        light = vtk.vtkLight()
        light.SetLightTypeToCameraLight()
        light.SetPosition(0.5, 0.8, 1)
        ren.AddLight(light)

        rw.Render()
        wif = vtk.vtkWindowToImageFilter()
        wif.SetInput(rw)
        wif.SetInputBufferTypeToRGB()
        wif.ReadFrontBufferOff()
        wif.Update()
        img = wif.GetOutput()
        arr = numpy_support.vtk_to_numpy(img.GetPointData().GetScalars()).reshape(h, w, 3)[::-1]
        im = Image.fromarray(arr.copy())

        if labels:
            proj = _projector(ren, w, h)
            lab = [(t, ns) for (t, ns) in (label_set or LABELS) if view not in VIEW_NAMES or set(ns) <= VIEW_NAMES[view]]
            pts = {}
            for t, pt in EXTRA.get(view, []):
                lab.append((t, [t]))
                anchors[t] = (pt, None, (0, 0, 0))
            if not explode:
                for n, pt in PANEL_ANCHORS.get(view, {}).items():
                    if n in anchors:
                        anchors[n] = (pt, anchors[n][1], anchors[n][2])
            im = _draw_labels(im, proj, anchors, lab, title or "", view)
        elif title:
            _title(im, title)
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, fname)
        im.save(path)
        return path


def _projector(ren, w, h):
    coord = vtk.vtkCoordinate()
    coord.SetCoordinateSystemToWorld()

    def f(pt):
        coord.SetValue(*pt)
        x, y = coord.GetComputedDoubleDisplayValue(ren)
        return x, h - y
    return f


def _font(size):
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _title(im, title):
    d = ImageDraw.Draw(im)
    d.text((28, 22), title, fill=(20, 30, 40), font=_font(34))
    d.text((28, 66), f"SI Console Rev {P.REV}", fill=(90, 100, 110), font=_font(20))


def _draw_labels(im, proj, anchors, label_set, title, view):
    w, h = im.size
    d = ImageDraw.Draw(im)
    font = _font(19)
    _title(im, title)
    items = []
    for text, names in label_set:
        pts = []
        for n in names:
            if n in anchors:
                c, bb, off = anchors[n]
                pts.append(proj(c))
        if not pts:
            continue
        ax = sum(p[0] for p in pts) / len(pts)
        ay = sum(p[1] for p in pts) / len(pts)
        if 0 <= ax <= w and 0 <= ay <= h:
            items.append([text, ax, ay])
    # two columns, spread vertically so labels never overlap
    mid = w / 2
    cols = {"L": [it for it in items if it[1] < mid], "R": [it for it in items if it[1] >= mid]}
    if len(cols["L"]) > len(cols["R"]) + 4:
        extra = sorted(cols["L"], key=lambda it: -it[1])[:(len(cols["L"]) - len(cols["R"])) // 2]
        for e in extra:
            cols["L"].remove(e)
            cols["R"].append(e)
    elif len(cols["R"]) > len(cols["L"]) + 4:
        extra = sorted(cols["R"], key=lambda it: it[1])[:(len(cols["R"]) - len(cols["L"])) // 2]
        for e in extra:
            cols["R"].remove(e)
            cols["L"].append(e)
    gap = 30
    for side, its in cols.items():
        its.sort(key=lambda it: it[2])
        ys = [it[2] for it in its]
        for i in range(1, len(ys)):
            ys[i] = max(ys[i], ys[i - 1] + gap)
        shift = max(0, ys[-1] - (h - 30)) if ys else 0
        ys = [y - shift for y in ys]
        for i in range(len(ys) - 2, -1, -1):
            ys[i] = min(ys[i], ys[i + 1] - gap)
        for it, ly in zip(its, ys):
            text, ax, ay = it
            tw = d.textlength(text, font=font)
            if side == "L":
                lx = 24
                ex = lx + tw + 10
                d.text((lx, ly - 11), text, fill=(15, 25, 35), font=font)
            else:
                lx = w - 24 - tw
                ex = lx - 10
                d.text((lx, ly - 11), text, fill=(15, 25, 35), font=font)
            d.line([(ex, ly), (ax, ay)], fill=(190, 40, 40), width=2)
            d.ellipse([ax - 4, ay - 4, ax + 4, ay + 4], fill=(190, 40, 40))
    return im


def render_all(parts):
    sc = Scene(parts)
    files = []
    files.append(sc.render(f"render_hero_{P.REV}.png", "iso", panel_alpha=0.28, title="SI Console, hero view"))
    files.append(sc.render(f"render_front_{P.REV}.png", "front", panel_alpha=0.25, title="Front view", hide=()))
    files.append(sc.render(f"render_top_{P.REV}.png", "top", panel_alpha=0.22, title="Top view (through the clear lid)"))
    files.append(sc.render(f"render_back_{P.REV}.png", "back", panel_alpha=0.25, title="Back view (monitor hidden)", hide=("monitor",)))
    files.append(sc.render(f"render_exploded_{P.REV}.png", "iso", panel_alpha=0.45, explode=True, title="Exploded view"))
    files.append(sc.render(f"render_see_through_{P.REV}.png", "iso", panel_alpha=0.12, title="See-through view"))
    return files
