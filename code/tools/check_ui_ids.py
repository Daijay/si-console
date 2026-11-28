"""Check that every string id the UI snapshot can emit exists in
strings.json, in both languages. Run from code/: python tools/check_ui_ids.py
A missing id would paint a raw key on the kiosk, which is fail-loud here.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

strings = json.loads(
    (Path(__file__).resolve().parent.parent / "dashboard" / "strings.json").read_text(
        encoding="utf-8"
    )
)
src = Path(__file__).resolve().parent.parent / "si_console" / "ui_snapshot.py"
text = src.read_text(encoding="utf-8")
ids = set(re.findall(r"ui_w_[a-z_]+", text))
ids |= set(re.findall(r"ui_reason_[A-Z_]+", text))
missing = sorted(i for i in ids if i not in strings["en"] or i not in strings["zh"])
print(f"checked {len(ids)} ids; missing: {missing}")
raise SystemExit(1 if missing else 0)
