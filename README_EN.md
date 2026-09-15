# FigTreeKit Studio

> Desktop app · Visual parameter tuning · Live preview · Reproducible script export

FigTreeKit Studio is the visual front-end for [`figtreekit`](https://pypi.org/project/figtreekit/). It provides a graphical interface for parameter tuning, live PNG preview, equivalent CLI commands, and JSON configuration export, enabling non-programming biologists and reviewers to quickly style phylogenetic trees while preserving full reproducibility.

[🇨🇳 中文](README.md) · 🇬🇧 English

**v0.1.0 — First open-source release**
- 🖥️ **Standalone desktop app**: runs in a native window (pywebview), no browser required
- 🌐 **Bilingual UI (Chinese / English)**: one-click switch (top-right `EN / 中文`), auto-remembered, defaults to system language on first launch
- 🌿 **SVG vector logo**: minimalist black/white/grey phylogenetic tree (`static/logo.svg`), also used as the app icon
- ♿ **Accessibility**: WCAG AA contrast, `aria-live` status announcements, keyboard focus management
- 🔒 **Security hardening**: path-traversal protection, CSP security headers, request body size limit

**Design principles**: thin front-end (zero business logic in the front-end) + unchanged core (reuses figtreekit directly) + reproducibility first (what you see in the GUI = what you get from the command line).

---

## Installation

```bash
pip install figtreekit-studio
```

**Runtime dependencies**:
- Python 3.11+
- Java 8+ (JRE/JDK, for rendering)
- `figtreekit` 1.1.2+ (installed automatically)
- `pywebview` 5.0+ (installed automatically, provides the native desktop window)

Verified on macOS; Windows/Linux should be compatible in principle (the UI layer avoids native controls).

> ⚠️ This project is in the Alpha stage (v0.1.0); APIs and UI may change across versions.

---

## Launch

```bash
figtreekit-studio                    # native desktop window (default, no browser)
figtreekit-studio --browser          # open in the system browser instead
figtreekit-studio --no-window        # start the server only, no UI
figtreekit-studio --port 9000 --browser
python -m figtreekit_studio          # equivalent entry point
```

The macOS app bundle (`FigTreeKit Studio.app`) is double-click to launch — also a native window, no browser or command line required.

---

## Language switching

The **`EN` / `中文`** button at the top-right switches all UI text (form labels, buttons, hints, error messages) at any time. The choice is written to `localStorage` and persists on next launch; the first launch auto-selects based on the system language.

---

## First render

1. Paste Newick/Nexus tree text on the left form (or upload a `.tre/.nwk/.nex` file).
2. Adjust layout, appearance, taxonomy, scale axis, and other parameters.
3. Click "⚡ Generate preview + export script".
4. The rendered preview appears on the right in real time.
5. The equivalent CLI command and JSON config are shown at the bottom-right, one-click copy.

> On first use, if Java is unavailable or the JAR is missing, the UI gives clear guidance (in the interface language). Click the "环境检测" (Environment check) button at the top-right to verify.

---

## Export = reproduce

The CLI commands exported by Studio are exactly what the generator actually executes (sharing a single source of truth, `params.to_cli_args`):

```bash
python -m figtreekit input.tre -o output.nex --force \
  --layout polar --tip-labels-hide --auto-color phylum \
  --scale-axis-show \
  --background-color #FAFAFA --branch-width 2.0 \
  && java -jar figtree_patched.jar -graphic PNG -width 1600 -height 1000 output.nex output.png
```

Corresponding JSON config (directly consumable by `figtreekit --config`):

```json
{
  "layout.layoutType": "POLAR",
  "tipLabels.isShown": false,
  "appearance.backgroundColour": "#FAFAFA",
  "appearance.branchLineWidth": 2.0,
  "scaleAxis.isShown": true
}
```

> **JSON config capability boundary**: automatic coloring (`--auto-color`) and taxonomic collapsing (`--collapse-rank` / `--collapse-style`) are figtreekit clade operations — independent switches in the CLI, with no corresponding simple keys in the config schema. Therefore **the JSON config does not include these three items**; only the CLI command can fully reproduce results that include coloring/collapsing. For full reproducibility, always rely on the exported CLI command.

---

## Features

### Current version (v0.1.0)
- ✅ Desktop app: native window, no browser dependency (pywebview / WKWebView)
- ✅ Bilingual UI, one-click switch with memory
- ✅ SVG vector logo (minimalist black/white/grey) + matching app icon
- ✅ Tree input: paste Newick/Nexus text or upload a file
- ✅ Layout: rectilinear / polar / radial
- ✅ Tip label show/hide + radial alignment
- ✅ Appearance: background color, foreground color, branch line width, font/family/size/style/label color
- ✅ Automatic coloring by taxonomic rank (`--auto-color`)
- ✅ Collapsing by taxonomic rank (`--collapse-rank` + cartoon/collapse styles)
- ✅ Scale axis + scale bar
- ✅ Node/branch label show/hide and properties
- ✅ Polar parameters (angle range / root angle)
- ✅ Rectangular tree curvature
- ✅ Legend show/hide and position
- ✅ Live PNG/SVG/PDF/JPEG preview
- ✅ Export equivalent CLI command + JSON config
- ✅ Console entry `figtreekit-studio`

### P1 (planned)
- Clade-level manual highlight/coloring
- Taxonomy mapping file upload to drive coloring/collapsing (UI marked "planned" and disabled)
- Preset themes

### P2 (planned)
- Batch mode
- History/sessions
- Input validation feedback

---

## Architecture

```
Desktop window (pywebview native window, optional --browser fallback)
    │ HTTP (JSON, localhost loopback only)
    ▼
FigTreeKit Studio backend (Python)
  ┌──────────┐  ┌───────────┐  ┌──────────┐
  │ params   │  │ generator │  │ renderer │
  │ (schema) │  │ (→.nex)   │  │ (→png)   │
  └──────────┘  └───────────┘  └──────────┘
                     │               │
                     ▼               ▼
               figtreekit      figtree_patched.jar
               (CLI/API)       (java -jar)
```

All generation/rendering logic reuses figtreekit; Studio itself contains no business logic. When frozen into a bundle (.app), the generator automatically switches to running figtreekit CLI in-process.

---

## Project structure

```
figtreekit_studio/
├── __init__.py
├── __main__.py             # python -m figtreekit_studio
├── cli.py                  # console entry (desktop window / --browser / --no-window)
├── desktop.py              # pywebview native desktop window
├── server.py               # HTTP server (127.0.0.1 only)
├── core/
│   ├── params.py           # parameter schema + UI↔figtreekit mapping
│   ├── generator.py        # parameters → figtreekit → .nex (in-process when frozen)
│   ├── renderer.py         # .nex → png/pdf/svg
│   └── exporter.py         # parameters → CLI command + JSON config
├── static/
│   ├── index.html          # tuning form + preview + export area (i18n-ready)
│   ├── app.js              # fetch API + render logic + bilingual dictionary
│   ├── style.css
│   └── logo.svg            # minimalist SVG logo
└── data/
    └── figtree_patched.jar # bundled with the package
assets/
└── icon.icns               # macOS app icon generated from logo.svg
```

---

## Building the macOS .app

```bash
# 1) Build environment (Python 3.12 + PyInstaller + pywebview + figtreekit)
uv venv --python 3.12 .venv-build
uv pip install --python .venv-build/bin/python pyinstaller pywebview "figtreekit>=1.1.2"

# 2) Package
.venv-build/bin/pyinstaller "FigTreeKit Studio.spec" --noconfirm --clean

# 3) Smoke test (full generation chain in the frozen environment)
"./dist/FigTreeKit Studio.app/Contents/MacOS/FigTreeKit Studio" --smoke-test
```

Output: `dist/FigTreeKit Studio.app` (with icon.icns, static, JAR). Alternative: `python setup_py2app.py py2app`.

---

## Testing

```bash
cd FigTreeKit-Studio-项目代码
pip install pytest
python -m pytest tests/ -v
```

| Layer | Content |
|------|------|
| Unit | `params.to_cli_args` / `to_config_dict` mapping correct |
| Unit | exporter and generator share the same mapping (no drift) |
| Unit | renderer JAR missing/timeout error handling |
| Static | logo.svg / i18n dictionary / page data-i18n completeness |
| E2E | start server → POST Newick → return valid PNG base64 |

---

## License

GPL-2.0-or-later (same as figtreekit). See [LICENSE](LICENSE).

The bundled `figtree_patched.jar` is derived from FigTree v1.4.4 (GPL-2.0-or-later) and includes iText (AGPL-3.0).

---

## Contributing

Issues and Pull Requests are welcome. Please ensure:
- Run `python -m pytest tests/ -v` before submitting and all tests pass
- Follow the existing code style (Python: `from __future__ import annotations`; JS: vanilla, no build step)
- Do not modify the single source of truth design of `params.to_cli_args`

---

## Citation

FigTreeKit Studio is built on top of [`figtreekit`](https://pypi.org/project/figtreekit/). If you use FigTreeKit (or its visual front-end FigTreeKit Studio) in your research, please cite it:

> Zeng Z. (2026). *FigTreeKit: A Python toolkit for programmatic FigTree styling, taxonomy-aware clade auditing, and phylogenetic tree rendering*. https://doi.org/10.64898/2026.08.27.747475

- **PyPI**: https://pypi.org/project/figtreekit/
- **Source code**: https://github.com/ZengZichao/FigTreeKit
- **DOI**: https://doi.org/10.64898/2026.08.27.747475

BibTeX:

```bibtex
@software{figtreekit2026,
  author = {Zeng, Zichao},
  title = {FigTreeKit: A Python toolkit for programmatic FigTree styling, taxonomy-aware clade auditing, and phylogenetic tree rendering},
  year = {2026},
  url = {https://github.com/ZengZichao/FigTreeKit},
  doi = {10.64898/2026.08.27.747475}
}
```
