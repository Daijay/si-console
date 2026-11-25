"""Cross-check every net on the SI Console HAT against code/si_console/gpio_map.py.

    python pcb/check_nets.py

Reads si_console_hat.kicad_pcb (and a path to another board as an optional
argument). Standard library only, KiCad is not needed. Exits 1 on any difference.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "code"))
from si_console import gpio_map as g  # noqa: E402

# BCM GPIO to physical header pin, standard Raspberry Pi 40 pin header.
PHYSICAL = {5: 29, 6: 31, 13: 33, 17: 11, 19: 35, 20: 38, 21: 40, 22: 15, 23: 16, 24: 18, 27: 13}
PIN_5V = (2, 4)
PIN_GND = (6, 9, 14, 20, 25, 30, 34, 39)

# LED name in gpio_map to (resistor, connector). Button LEDs to (connector, pin).
STATUS = {"COORD": ("R1", "J2"), "AGENT 1": ("R2", "J3"), "AGENT 2": ("R3", "J4"), "GUARD": ("R4", "J5")}
BUTTON_LED = {"green button": "J6", "red button": "J7"}
LABELS = {"J2": "COORD", "J3": "AGENT 1", "J4": "AGENT 2", "J5": "GUARD", "J6": "GREEN",
          "J7": "RED", "J8": "KILL", "J9": "PTT", "J10": "LANG"}


def sexpr(text):
    tokens = re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+', text)
    stack = [[]]
    for tok in tokens:
        if tok == "(":
            stack.append([])
        elif tok == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(tok[1:-1] if tok.startswith('"') else tok)
    return stack[0][0]


def children(node, tag):
    return [c for c in node if isinstance(c, list) and c and c[0] == tag]


def read_board(path):
    """Return ({net: {ref.pad}}, {ref: value}, {ref: footprint})."""
    board = sexpr(Path(path).read_text(encoding="utf-8"))
    nets, values, footprints = {}, {}, {}
    for fp in children(board, "footprint"):
        props = {p[1]: p[2] for p in children(fp, "property")}
        ref = props["Reference"]
        values[ref] = props["Value"]
        footprints[ref] = fp[1]
        for pad in children(fp, "pad"):
            net = children(pad, "net")
            if net:
                nets.setdefault(net[0][-1], set()).add(f"{ref}.{pad[1]}")
    return nets, values, footprints


def expected_nets():
    pi = lambda gpio: f"J1.{PHYSICAL[gpio]}"
    five = {f"J1.{p}" for p in PIN_5V} | {"U1.9"}
    gnd = {f"J1.{p}" for p in PIN_GND} | {"U1.8", "U1.7"}
    nets = []
    for channel, (in_pin, out_pin, gpio, name) in g.ULN2003_CHANNELS.items():
        assert in_pin == channel, "ULN2003 channel map changed"
        nets.append((f"GPIO{gpio} to IN{channel} ({name})", {pi(gpio), f"U1.{in_pin}"}))
        if name in STATUS:
            res, conn = STATUS[name]
            five.add(f"{res}.1")
            nets.append((f"{name} anode", {f"{res}.2", f"{conn}.1"}))
            nets.append((f"{name} cathode on OUT{channel}", {f"U1.{out_pin}", f"{conn}.2"}))
        else:
            conn = BUTTON_LED[name]
            five.add(f"{conn}.3")
            nets.append((f"{name} LED- on OUT{channel}", {f"U1.{out_pin}", f"{conn}.4"}))
    # Inputs. JP1 is bridged by copper as built, so GPIO17 reaches J6.1 through it.
    nets.append(("green button, Pi side of the jumpers", {pi(g.GREEN_BUTTON), "JP1.1", "JP2.1"}))
    nets.append(("green button, switch side", {"JP1.2", "J6.1", "J8.4"}))
    nets.append(("optional interlock", {"JP2.2", "J8.3"}))
    for name, gpio, conn in (("red button", g.RED_BUTTON, "J7"), ("kill switch", g.KILL_SWITCH, "J8"),
                             ("push to talk", g.PTT_BUTTON, "J9"), ("EN/ZH toggle", g.LANG_TOGGLE, "J10")):
        nets.append((name, {pi(gpio), f"{conn}.1"}))
    for conn in ("J6", "J7", "J8", "J9", "J10"):
        gnd.add(f"{conn}.2")
    nets.append(("5 V rail", five))
    nets.append(("ground", gnd))
    return nets


def check(path):
    errors = []
    # The physical pin numbers written in gpio_map.py must agree with the table above.
    source = Path(g.__file__).read_text(encoding="utf-8")
    pins = re.findall(r"^[A-Z0-9_]+ = (\d+)\s+# physical pin (\d+)", source, re.M)
    for gpio, phys in pins:
        if int(gpio) in PHYSICAL and PHYSICAL[int(gpio)] != int(phys):
            errors.append(f"gpio_map.py says GPIO{gpio} is pin {phys}, expected {PHYSICAL[int(gpio)]}")
    missing = set(PHYSICAL) - {int(a) for a, _ in pins}
    if missing:
        errors.append(f"no physical pin comment in gpio_map.py for GPIO {sorted(missing)}")

    nets, values, footprints = read_board(path)
    expected = expected_nets()
    real = {name: pads for name, pads in nets.items() if not name.startswith("unconnected-")}
    for what, pads in expected:
        hits = [n for n, p in real.items() if p == pads]
        if hits:
            print(f"ok    {what:42s} {hits[0]:12s} {' '.join(sorted(pads))}")
            del real[hits[0]]
        else:
            near = max(real.items(), key=lambda kv: len(kv[1] & pads), default=(None, set()))
            errors.append(f"{what}: expected {sorted(pads)}, closest net {near[0]} has {sorted(near[1])}")
    for name, pads in real.items():
        errors.append(f"unexpected net {name}: {sorted(pads)}")

    # Nothing else on the header may be wired. The two 3V3 pins share one unused net.
    for name, pads in nets.items():
        if name.startswith("unconnected-") and len(pads) > 1 and pads != {"J1.1", "J1.17"}:
            errors.append(f"unused net {name} joins {sorted(pads)}")
    for name, ohms in g.LED_RESISTORS_OHM.items():
        ref = STATUS[name][0]
        if values.get(ref) != str(ohms):
            errors.append(f"{ref} ({name}) is {values.get(ref)} ohm, gpio_map.py says {ohms}")
    for ref, label in LABELS.items():
        if values.get(ref) != label:
            errors.append(f"{ref} is labelled {values.get(ref)}, expected {label}")
    if "Bridged" not in footprints.get("JP1", ""):
        errors.append("JP1 must be the bridged (closed) solder jumper")
    if "_Open" not in footprints.get("JP2", ""):
        errors.append("JP2 must be the open solder jumper")
    return errors


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else HERE / "si_console_hat.kicad_pcb"
    problems = check(target)
    for p in problems:
        print("FAIL ", p)
    print(f"{len(expected_nets())} nets checked against gpio_map.py: " + ("FAIL" if problems else "PASS"))
    sys.exit(1 if problems else 0)
