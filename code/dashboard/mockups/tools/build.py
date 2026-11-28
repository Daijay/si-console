"""Generate js/strings.js, one static page per state, and the gallery.

Usage: python build.py     (standard library only)
Run it after editing ../strings.json or js/fixtures.js. The generated
strings.js lets the pages open straight from disk, where fetch() is
blocked. The live dashboard should fetch strings.json instead.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCREENS = {"mini": (800, 480), "monitor": (1920, 1080)}

strings = json.loads((HERE.parent / "strings.json").read_text(encoding="utf-8"))
table = {lang: strings[lang] for lang in ("en", "zh")}
assert set(table["en"]) == set(table["zh"]), "en and zh keys differ"


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


write(HERE / "js" / "strings.js",
      "/* Generated from ../../strings.json by tools/build.py. */\n"
      "window.STRINGS = " + json.dumps(table, ensure_ascii=False, indent=1) + ";\n")

fixtures = (HERE / "js" / "fixtures.js").read_text(encoding="utf-8")
block = fixtures[fixtures.index("window.STATES = {"):]
states = [a or b for a, b in re.findall(r'^    (?:"([a-z0-9-]+)"|([a-z0-9]+)): ', block, re.M)]
used = set(re.findall(r'"(ui_[A-Za-z0-9_]+)"', "".join(
    p.read_text(encoding="utf-8") for p in (HERE / "js").glob("*.js") if p.name != "strings.js")))
missing = sorted(k for k in used if not k.endswith("_") and k not in table["en"])
assert not missing, f"strings.json is missing {missing}"

for old in (HERE / "states").glob("*.html"):
    old.unlink()
for screen in SCREENS:
    for state in [None] + states:
        up = "" if state is None else "../"
        data = f' data-state="{state}"' if state else ""
        name = state or "ready"
        page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={SCREENS[screen][0]}">
<meta name="theme-color" content="#0e1013">
<title>SI Console {screen}: {name}</title>
<link rel="stylesheet" href="{up}theme/tokens.css">
<link rel="stylesheet" href="{up}theme/{screen}.css">
</head>
<body{data}>
<div id="screen"></div>
<script src="{up}js/strings.js"></script>
<script src="{up}js/fixtures.js"></script>
<script src="{up}js/common.js"></script>
<script src="{up}js/{screen}.js"></script>
{"" if state else '<script src="js/live.js"></script>'}
</body>
</html>
"""
        target = HERE / f"{screen}.html" if state is None else HERE / "states" / f"{screen}-{state}.html"
        write(target, page)

rows = "\n".join(
    f'<tr><th scope="row">{s}</th>' + "".join(
        f'<td><a href="states/{screen}-{s}.html">{screen} EN</a></td>'
        f'<td><a href="states/{screen}-{s}.html?lang=zh">{screen} 中文</a></td>'
        for screen in SCREENS) + "</tr>"
    for s in states)
write(HERE / "index.html", f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>SI Console mockups</title>
<link rel="stylesheet" href="theme/tokens.css">
<style>body{{overflow:auto;cursor:auto;padding:32px;font-size:18px}}table{{border-collapse:collapse;margin-top:16px}}
th,td{{text-align:left;padding:6px 18px;border-bottom:1px solid var(--line)}}a{{color:var(--ink)}}a:focus-visible{{outline:3px solid var(--ember)}}</style></head>
<body><h1>SI Console screen states</h1>
<p>Static mockups with fake data. On any state page, L switches language and the arrow keys step through states.</p>
<table>
{rows}
</table></body></html>
""")
write(HERE / "states.json", json.dumps(states) + "\n")
print(len(states), "states,", len(states) * len(SCREENS), "state pages,", len(table["en"]), "strings per language")
