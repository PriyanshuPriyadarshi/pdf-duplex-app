# 🖨️ PDF Duplex & Booklet Studio

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52.svg?logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-Linux-FCC624.svg?logo=linux&logoColor=black)](https://kernel.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![CUPS Ready](https://img.shields.io/badge/Printing-CUPS-007acc.svg)](https://www.cups.org/)

A modern, high-performance Linux desktop workstation designed for **manual duplex printing** (printing double-sided on single-sided home and office printers) and **folded booklet creation** with zero aspect-ratio distortion, per-page ink saver inversion, and direct system PDF integration.

---

## 📸 Overview & Modern Architecture

Built with a responsive **three-panel layout** and a default **Zed Dark aesthetic** (`#28282E` background, `#212126` containers, `#E64B3D` accent):

1. **Left Panel (Sheets & Pages Sidebar)**:
   - Visual card list adapting dynamically to the active mode:
     - **Normal Mode**: 1-up page list with page numbers and thumbnails.
     - **Manual Duplex Mode**: 2-up sheets displaying Front and Back side-by-side (`P1 • P2`, `P3 • P4`).
     - **Booklet Mode**: 4-page signature cards (`[LF | RF]` Front and `[LB | RB]` Back) reflecting real physical paper sheets.
   - Multi-selection via mouse click, `Shift + Click` (range select), `Ctrl + Click` (toggle select), and `Ctrl + A` (select all).
   - Per-page or per-sheet **Invert / Ink Saver** toggle (`Ctrl + I` or button).
   - Page range filter (`All Pages` or custom ranges like `1-5, 8-10`).
2. **Center Panel (Interactive Canvas)**:
   - Crisp rendering with white paper simulation and dark borders.
   - Real-time zoom controls (`Fit to Page`, `Fit to Width`, custom zoom `25%` to `400%`).
   - Bottom navigation bar with previous/next sheet controls and quick-jump indicators.
3. **Right Panel (Inspector & Actions)**:
   - Drag-and-drop document loader with file metadata (page count, file size).
   - Mode switcher: **Normal (1-Up Single-Sided)**, **Manual Duplex (2-Sided)**, and **Booklet (Folded 2-Up)**.
   - Automatic **Page Number Stamping** with 6 positioning presets.
   - Printer destination selector detecting local CUPS printers.
   - 2-Step interactive workflow buttons: **Open Front Pages** ➔ **Visual Flip Prompt** ➔ **Open Back Pages**.

---

## ⚡ Quick Install & Run (No Root / Sudo Required)

### 1. One-Line Install to `$HOME` (Recommended)

Installs the app into `~/.local/share/pdf-duplex-app`, creates a command-line launcher at `~/.local/bin/pdf-duplex-app`, and registers it in your desktop application launcher menu (GNOME, KDE, etc.):

```bash
curl -fsSL https://raw.githubusercontent.com/PriyanshuPriyadarshi/pdf-duplex-app/main/install.sh | bash
```

Once installed, simply launch it from your application menu or run:
```bash
pdf-duplex-app
```

### 2. One-Line Uninstall

To cleanly remove the application, its launcher, icons, and desktop shortcuts:

```bash
curl -fsSL https://raw.githubusercontent.com/PriyanshuPriyadarshi/pdf-duplex-app/main/uninstall.sh | bash
```

*(Or via the install script with `--uninstall`:)*
```bash
curl -fsSL https://raw.githubusercontent.com/PriyanshuPriyadarshi/pdf-duplex-app/main/install.sh | bash -s -- --uninstall
```

---

## 🚀 Run Instantly Without Installing (Like `npx`)

If you use [Astral's `uv`](https://github.com/astral-sh/uv), you can run the app immediately in a temporary environment without manual installation:

```bash
uvx --from git+https://github.com/PriyanshuPriyadarshi/pdf-duplex-app.git pdf-duplex-app
```

Or install it permanently into your user tools:
```bash
uv tool install git+https://github.com/PriyanshuPriyadarshi/pdf-duplex-app.git
```

### Via `pipx`

```bash
pipx install git+https://github.com/PriyanshuPriyadarshi/pdf-duplex-app.git
```

---

## 🌟 Key Features & How It Works

### 1. Manual Duplex (2-Sided Printing on Standard Printers)
Most affordable home and office printers only print single-sided. Printing double-sided manually is notoriously error-prone:
- **Pass 1 (Fronts)**: Automatically extracts all odd pages (`1, 3, 5, 7...`). Click **"⓵ 1. Open Front Pages"** to print the entire front stack in one batch.
- **Flip & Reinsert**: A visual guide prompts you to take the printed stack, flip it, and place it back into the paper tray.
- **Pass 2 (Backs)**: Click **"⓶ 2. Open Back Pages"** to print all even pages (`2, 4, 6, 8...`) onto the opposite side of each sheet in matching order.

### 2. Booklet Mode (Folded 2-Up Signatures)
Converts standard portrait documents into saddle-stitched folded booklets:
- Pages are scaled proportionally and placed 2-up on landscape sheets.
- Proper signature imposition:
  - **Sheet 1 Front**: Last Page + Page 1
  - **Sheet 1 Back**: Page 2 + Second-to-last Page
- Once printed via the 2-step duplex pass, stack the sheets together, fold down the spine, and staple.

### 3. Per-Page Invert / Ink Saver
- Select any pages or sheets in the sidebar and click **Invert / Ink Saver** (or press `Ctrl + I`).
- Inverts color values (black background, white text/graphics), perfect for printing inverted dark diagrams, code listings, or ink-saving schemes.
- **High Fidelity**: Only targeted pages undergo high-resolution raster inversion; non-targeted pages remain untouched vector PDF pages with selectable text and small file size.

### 4. Page Number Stamping
- Automatically calculates and stamps formatted page numbers onto output sheets.
- Choose from 6 positions: Bottom Right, Bottom Center, Bottom Left, Top Right, Top Center, Top Left.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + O` | Open PDF Document |
| `Ctrl + P` | Print Document |
| `Ctrl + A` | Select all sheets/pages |
| `Ctrl + I` | Toggle Invert / Ink Saver on selected items |
| `F` | Fit sheet to window |
| `W` | Fit sheet to width |
| `+` / `-` | Zoom in / Zoom out |

---

## 💻 Manual Clone & Development

### Prerequisites
- Python 3.10+
- CUPS printing system (`cups` package on Linux)
- `uv` (recommended) or standard `python3 -m venv`

```bash
# 1. Clone repository
git clone https://github.com/PriyanshuPriyadarshi/pdf-duplex-app.git
cd pdf-duplex-app

# 2. Set up virtual environment
uv venv
source .venv/bin/activate

# 3. Install in editable mode
uv pip install -e .

# 4. Run application
python run.py
```

### Running Test Suite

All algorithms and UI interactions are covered by unit tests:

```bash
pytest -v
```

---

## 📁 Project Structure

```text
pdf-duplex-app/
├── src/
│   ├── main_window.py          # Three-panel workstation layout & workflow controller
│   ├── center_preview.py       # Interactive canvas with zooming & sheet navigation
│   ├── sidebar_page_list.py    # Mode-reactive thumbnail list with multi-selection
│   ├── settings_panel.py       # Document details, print mode, & action triggers
│   ├── imposer.py              # Mathematical imposition engine & pass splitting
│   ├── theme.py                # Modern Zed Dark palette & Qt styling
│   ├── utils.py                # CUPS printer integration & page range parser
│   └── widgets.py              # Flip prompt animation & UI components
├── assets/
│   └── pdf-duplex-app.svg      # High-resolution vector application icon
├── tests/                      # Full test suite (GUI, imposer, preview, themes)
├── install.sh                  # One-line user installer & uninstaller script
├── uninstall.sh                # Dedicated uninstaller script
├── pyproject.toml              # Modern PEP 621 package specification
└── run.py                      # Application launcher entry point
```

---

## 📄 License

This project is open-source software licensed under the **[GNU General Public License v3.0 (GPL-3.0)](LICENSE)**.