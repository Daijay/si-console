"""PNG renders with VTK (offscreen) plus labelled call-outs drawn with Pillow."""
import math
import os

import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont
from vtk.util import numpy_support

import geo
import params as P
import parts as pt

T = P.T
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


# Exploded view: group offsets
G_ELEC = (0, 0, 30)
G_STRIP = (0, -70, 45)
G_BRACKET = (0, -30, 18)
G_SCREEN = (0, 0, 75)
G_PROP = (0, 0, 28)
EXPLODE = {"base_plate": (0, 0, -35), "rubber_feet": (0, 0, -55), "monitor": (0, 70, 0),
           "control_strip": G_STRIP, "btn_green": G_STRIP, "btn_red": G_STRIP, "kill_switch": G_STRIP, "btn_ptt": G_STRIP,
           "toggle_lang": G_STRIP, "led_coord": G_STRIP, "led_agent1": G_STRIP, "led_agent2": G_STRIP, "led_guard": G_STRIP,
           "strip_bracket_1": G_BRACKET, "strip_bracket_2": G_BRACKET, "screen_plate": G_SCREEN, "mini_screen": G_SCREEN,
           "screen_standoffs": G_SCREEN, "screen_prop_1": G_PROP, "screen_prop_2": G_PROP,
           "pi5": G_ELEC, "pi5_standoffs": G_ELEC, "perfboard": G_ELEC, "perf_standoffs": G_ELEC, "uln2003": G_ELEC, "gpio_breakout": G_ELEC}
STRIP_SIDE = {"button wires (breakout to controls)", "LED wires (ULN2003 outputs to LEDs)"}
SCREEN_SIDE = {"HDMI MINI"}


def wire_offsets(w):
    """(start offset, end offset) of a wire in the exploded view."""
    if w["group"] in STRIP_SIDE:
        return G_ELEC, G_STRIP
    if w["name"] in SCREEN_SIDE:
        return G_ELEC, G_SCREEN
    return G_ELEC, G_ELEC


PANEL_ANCHORS = {
    "iso": {"base_plate": (P.BASE_W - 25, 30, 0), "control_strip": geo.strip_pt(40, -1, 64), "strip_bracket_1": None,
            "screen_plate": geo.local_to_world(geo.plate_frame(), 120, 0, 104), "screen_prop_1": None, "screen_prop_2": None},
    "front": {"base_plate": (P.BASE_W - 20, 0, 0), "control_strip": geo.strip_pt(15, -1, 60)},
    "top": {"base_plate": (P.BASE_W - 20, 25, T), "control_strip": geo.strip_pt(20, -1, 40), "screen_plate": geo.local_to_world(geo.plate_frame(), 135, 0, 60)},
}
LABELS = [
    ("Base plate (clear acrylic)", ["base_plate"]), ("Control strip, 20 deg slope", ["control_strip"]),
    ("Strip bracket", ["strip_bracket_1"]), ("Screen plate (angled)", ["screen_plate"]), ("Screen prop", ["screen_prop_2"]),
    ("Green button", ["btn_green"]), ("Red button", ["btn_red"]), ("Kill switch", ["kill_switch"]), ("Push to talk", ["btn_ptt"]),
    ("EN/ZH toggle", ["toggle_lang"]), ("LEDs: COORD, AGENT 1, AGENT 2, GUARD", ["led_coord", "led_agent1", "led_agent2", "led_guard"]),
    ("5 in HDMI screen", ["mini_screen"]), ("Raspberry Pi 5 + Active Cooler", ["pi5"]), ("Pi standoffs", ["pi5_standoffs"]),
    ("Perfboard on M3 standoffs", ["perfboard", "perf_standoffs"]), ("ULN2003", ["uln2003"]), ("GPIO ribbon breakout", ["gpio_breakout"]),
    ("Rubber feet", ["rubber_feet"]), ("MSI monitor (own stand)", ["monitor"]),
    ("GPIO ribbon", ["wire_gpio_ribbon"]), ("Button wires", ["wire_k"]), ("LED wires", ["wire_coord"]),
]
VIEW_NAMES = {
    "front": {"base_plate", "control_strip", "btn_green", "btn_red", "kill_switch", "btn_ptt", "toggle_lang", "led_coord", "led_agent1", "led_agent2",
              "led_guard", "monitor", "rubber_feet", "mini_screen", "screen_plate"},
    "top": {"base_plate", "control_strip", "strip_bracket_1", "screen_plate", "mini_screen", "pi5", "perfboard", "perf_standoffs", "gpio_breakout", "uln2003",
            "wire_gpio_ribbon", "wire_k", "wire_coord", "monitor", "kill_switch", "btn_green", "btn_red"},
}
LEGEND = [("G", "green"), ("R", "red"), ("K", "yellow"), ("PTT", "white"), ("LANG", "orange"), ("GND", "black"), ("COORD", "green"),
          ("AGENT 1", "white"), ("AGENT 2", "blue"), ("GUARD", "yellow"), ("5V", "red"), ("IN7", "grey")]


class Scene:
    def __init__(self, parts, size=P.RENDER_SIZE):
        self.parts = parts
        self.size = size

    def render(self, fname, view, panel_alpha=0.30, explode=False, labels=True, title="", hide=(), legend=True):
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
            off = EXPLODE.get(p["name"], (0, 0, 0)) if explode else (0, 0, 0)
            if p["category"] == "wire" and explode:
                so, eo = wire_offsets(p["wire"])
                pts = p["wire"]["pts"]
                cum = [0.0]
                for a, b in zip(pts, pts[1:]):
                    cum.append(cum[-1] + math.dist(a, b))
                tot = cum[-1] or 1.0
                pts2 = [tuple(q[i] + so[i] + (eo[i] - so[i]) * (c / tot) for i in range(3)) for q, c in zip(pts, cum)]
                shape = pt.tube(pts2, p["wire"]["r"])
                off = (0, 0, 0)
            else:
                shape = p["solid"]
            pd = _polydata(shape)
            tf = vtk.vtkTransform()
            tf.Translate(*off)
            m = vtk.vtkPolyDataMapper()
            m.SetInputData(pd)
            a = vtk.vtkActor()
            a.SetMapper(m)
            a.SetUserTransform(tf)
            r, g, b = p["colour"]
            a.GetProperty().SetColor(r, g, b)
            a.GetProperty().SetOpacity(panel_alpha if p["category"] == "panel" else 1.0)
            a.GetProperty().SetSpecular(0.35)
            a.GetProperty().SetSpecularPower(40)
            a.GetProperty().SetAmbient(0.25)
            a.GetProperty().SetDiffuse(0.8)
            if p["category"] == "panel":
                a.GetProperty().SetEdgeVisibility(0)
            ren.AddActor(a)
            bb = shape.BoundingBox()
            c = ((bb.xmin + bb.xmax) / 2 + off[0], (bb.ymin + bb.ymax) / 2 + off[1], (bb.zmin + bb.zmax) / 2 + off[2])
            if p["category"] == "wire":
                pp = (p["wire"]["pts"] if not explode else pts2)
                c = pp[len(pp) // 2]
            anchors[p["name"]] = (c, off)
            if p["category"] != "wire":
                for i, (lo, hi) in enumerate(((bb.xmin, bb.xmax), (bb.ymin, bb.ymax), (bb.zmin, bb.zmax))):
                    bounds[2 * i] = min(bounds[2 * i], lo + off[i])
                    bounds[2 * i + 1] = max(bounds[2 * i + 1], hi + off[i])

        cx, cy, cz = [(bounds[2 * i] + bounds[2 * i + 1]) / 2 for i in range(3)]
        diag = math.dist((bounds[0], bounds[2], bounds[4]), (bounds[1], bounds[3], bounds[5]))
        cam = ren.GetActiveCamera()
        cam.SetFocalPoint(cx, cy, cz)
        if view == "iso":
            d = (-0.55, -1.0, 0.62)
            n = math.sqrt(sum(x * x for x in d))
            cam.SetPosition(*(c + diag * 2.1 * x / n for c, x in zip((cx, cy, cz), d)))
            cam.SetViewUp(0, 0, 1)
            cam.SetViewAngle(24)
        else:
            dirs = {"front": ((0, -1, 0), (0, 0, 1)), "top": ((0, 0, 1), (0, 1, 0))}[view]
            cam.SetPosition(cx + dirs[0][0] * 2000, cy + dirs[0][1] * 2000, cz + dirs[0][2] * 2000)
            cam.SetViewUp(*dirs[1])
            cam.ParallelProjectionOn()
            ext = (bounds[1] - bounds[0], bounds[5] - bounds[4]) if view == "front" else (bounds[1] - bounds[0], bounds[3] - bounds[2])
            cam.SetParallelScale(max(ext[1] / 2, ext[0] / 2 / (w / h)) * 1.2)
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
        arr = numpy_support.vtk_to_numpy(wif.GetOutput().GetPointData().GetScalars()).reshape(h, w, 3)[::-1]
        im = Image.fromarray(arr.copy())
        _title(im, title)
        if labels:
            lab = [(t, ns) for (t, ns) in LABELS if view not in VIEW_NAMES or set(ns) <= VIEW_NAMES[view]]
            if not explode:
                for n_, ptw in PANEL_ANCHORS.get(view, {}).items():
                    if n_ in anchors and ptw is not None:
                        anchors[n_] = (ptw, anchors[n_][1])
            im = _draw_labels(im, _projector(ren, w, h), anchors, lab)
        if legend:
            _legend(im)
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, fname)
        im.save(path)
        return path


def _projector(ren, w, h):
    coord = vtk.vtkCoordinate()
    coord.SetCoordinateSystemToWorld()

    def f(pt_):
        coord.SetValue(*pt_)
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
    d.text((28, 66), f"SI Console Rev {P.REV}, open frame", fill=(90, 100, 110), font=_font(20))


def _legend(im):
    from parts import LED_RGB
    from wires import COLOURS
    d = ImageDraw.Draw(im)
    w, h = im.size
    f = _font(15)
    x0, y0 = 28, h - 84
    d.text((x0, y0 - 24), "Wire colours (wiring table)", fill=(20, 30, 40), font=_font(16))
    x = x0
    y = y0
    for i, (nm, col) in enumerate(LEGEND):
        rgb = tuple(int(255 * v) for v in COLOURS[col])
        d.ellipse([x, y + 3, x + 12, y + 15], fill=rgb, outline=(60, 60, 60))
        d.text((x + 17, y), nm, fill=(20, 30, 40), font=f)
        x += 17 + d.textlength(nm, font=f) + 22
        if i == 5:
            x, y = x0, y + 24


def _draw_labels(im, proj, anchors, label_set):
    w, h = im.size
    d = ImageDraw.Draw(im)
    font = _font(19)
    items = []
    for text, names in label_set:
        pts = [proj(anchors[n][0]) for n in names if n in anchors]
        if not pts:
            continue
        ax = sum(p[0] for p in pts) / len(pts)
        ay = sum(p[1] for p in pts) / len(pts)
        if 0 <= ax <= w and 0 <= ay <= h:
            items.append([text, ax, ay])
    mid = w / 2
    cols = {"L": [it for it in items if it[1] < mid], "R": [it for it in items if it[1] >= mid]}
    while len(cols["L"]) > len(cols["R"]) + 2:
        e = max(cols["L"], key=lambda it: it[1]); cols["L"].remove(e); cols["R"].append(e)
    while len(cols["R"]) > len(cols["L"]) + 2:
        e = min(cols["R"], key=lambda it: it[1]); cols["R"].remove(e); cols["L"].append(e)
    gap = 30
    for side, its in cols.items():
        its.sort(key=lambda it: it[2])
        ys = [max(100, it[2]) for it in its]
        for i in range(1, len(ys)):
            ys[i] = max(ys[i], ys[i - 1] + gap)
        shift = max(0, ys[-1] - (h - 110)) if ys else 0
        ys = [y - shift for y in ys]
        for i in range(len(ys) - 2, -1, -1):
            ys[i] = min(ys[i], ys[i + 1] - gap)
        for it, ly in zip(its, ys):
            text, ax, ay = it
            tw = d.textlength(text, font=font)
            if side == "L":
                lx = 24
                ex = lx + tw + 10
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
    files.append(sc.render(f"render_hero_{P.REV}.png", "iso", panel_alpha=0.22, title="SI Console, hero view"))
    files.append(sc.render(f"render_front_{P.REV}.png", "front", panel_alpha=0.22, title="Front view"))
    files.append(sc.render(f"render_top_{P.REV}.png", "top", panel_alpha=0.22, title="Top view"))
    files.append(sc.render(f"render_exploded_{P.REV}.png", "iso", panel_alpha=0.30, explode=True, title="Exploded view"))
    return files
