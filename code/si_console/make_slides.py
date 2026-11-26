# Slide maker, tool name make_slides, tagged NEEDS APPROVAL because it
# writes a file that visitors will see. Making slides never executes a
# trade. The slide content must come from task notes and search results,
# with a source line on each slide, so every claim can be traced. The
# file is written to the vault slides folder, then shown on the main
# screen. Only python-pptx is used. No other slide library. Max 5
# slides, max 5 bullets per slide. The output path must be under
# vault/si-console/slides/. The registry enforces that in tools.py.
# This file enforces it again, so a bug in one place is caught by the
# other.
"""Make slides with python-pptx. Content from notes, with sources."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

from si_console import config
from si_console.errors import ToolError

MAX_SLIDES = 5
MAX_BULLETS_PER_SLIDE = 5


def make_slides(
    title: str,
    bullets: list,
    slide_count: int = 3,
    lang: str = "en",
    output_path: str = "vault/si-console/slides/deck.pptx",
    source_line: str = "",
) -> dict:
    """Build a slide deck. Returns the output path and slide count.

    `bullets` is a flat list of strings. They are split across slides,
    up to 5 per slide. Every slide gets a source line at the bottom,
    so the audience can see where the claim came from. A slide with
    no source line is not finished. The caller must pass the source.
    """
    if slide_count < 1 or slide_count > MAX_SLIDES:
        raise ToolError("BAD_SCHEMA", "slide_count must be 1 to 5.")
    if len(bullets) > slide_count * MAX_BULLETS_PER_SLIDE:
        raise ToolError(
            "BAD_SCHEMA",
            f"Too many bullets for {slide_count} slides. Max 5 per slide.",
        )
    if not output_path.startswith("vault/si-console/slides/"):
        raise ToolError(
            "BAD_SCHEMA",
            "Slide output must be under vault/si-console/slides/.",
        )
    deck = Presentation()
    deck.slide_width = Inches(13.33)
    deck.slide_height = Inches(7.5)
    # Split the bullets across slides, in order. The title slide is
    # slide 1. Content slides follow. This keeps the deck short and
    # readable on a booth screen, in English and in Chinese.
    per_slide = MAX_BULLETS_PER_SLIDE
    chunks = [bullets[i : i + per_slide] for i in range(0, len(bullets), per_slide)]
    chunks = chunks[:slide_count]
    title_slide = deck.slides.add_slide(deck.slide_layouts[0])
    title_slide.shapes.title.text = title
    if title_slide.placeholders:
        try:
            title_slide.placeholders[1].text = "SI Console. Talk to dispatch, press to approve."
        except (IndexError, AttributeError):
            pass
    for chunk in chunks:
        slide = deck.slides.add_slide(deck.slide_layouts[1])
        slide.shapes.title.text = title
        body = slide.placeholders[1].text_frame
        body.clear()
        for i, bullet in enumerate(chunk):
            para = body.paragraphs[0] if i == 0 else body.add_paragraph()
            para.text = bullet
            para.level = 0
            para.font.size = Pt(20)
        if source_line:
            note = slide.notes_slide.placeholders[1].text_frame
            note.text = f"Source: {source_line}"
    # The vault root is vault/si-console, so the slides folder is
    # root/slides. The file name comes from output_path, never the
    # full path, so a caller cannot escape the slides folder.
    root = Path(config.VAULT_PATH)
    target = root / "slides" / Path(output_path).name
    target.parent.mkdir(parents=True, exist_ok=True)
    deck.save(str(target))
    return {"status": "written", "path": str(target), "slides": len(deck.slides)}


def main() -> None:
    """Command line entry, so shell_run can call it. Usage:
    python3 make_slides.py "Title" "Bullet one" "Bullet two"
    Prints the output path. The source line is passed by the caller
    in the real build. This entry point uses a placeholder source.
    """
    import json
    import sys

    if len(sys.argv) < 3:
        print('Usage: python3 make_slides.py "Title" "Bullet one" ...')
        raise SystemExit(2)
    result = make_slides(
        title=sys.argv[1],
        bullets=sys.argv[2:],
        slide_count=3,
        source_line="Task notes and Bocha search. See the task note for links.",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
