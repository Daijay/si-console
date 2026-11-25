# SI Console screen mockups

Static pages with fake data. Not connected to the console. Design notes: [`docs/UI_SPEC.md`](../../../docs/UI_SPEC.md).

- `index.html`: links to every state. `mini.html` and `monitor.html` also take `?state=<id>&lang=zh&still`.
- On any state page: `L` switches language, left and right arrows change state.
- `directions/`: the three direction studies (`?view=idle|approval|monitor`).
- After editing `../strings.json` or `js/fixtures.js`: `python tools/build.py`.
- After adding new characters: `python tools/fonts.py <folder with source TTFs>` (needs `fonttools` and `brotli`).

Fonts are subsets under the SIL Open Font License 1.1; license texts are in `fonts/`.
