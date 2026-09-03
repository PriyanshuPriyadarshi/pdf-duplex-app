# PDF Duplex/Booklet Printer

A Python/PyQt6 GUI application for manual duplex and booklet printing on Linux.

## Features

- Load a PDF and preview the first page.
- Choose printing mode: Normal, Manual Duplex, or Booklet.
- Optional page inversion (placeholder).
- Print workflow:
  - For Normal mode: sends the PDF directly to the printer.
  - For Manual Duplex and Booklet modes:
    1. Prints the first side (all front pages in correct order).
    2. Prompts the user to flip the stack and reinsert.
    3. Prints the second side (all back pages).
- Uses the system's CUPS `lp` command for printing.
- Preview uses PyQt6.QtPdf for high-quality, vector-based rendering.

## Installation

### Option 1: pip (from source)

```bash
# Clone the repository
git clone <repository-url>
cd pdf-duplex-app

# Create a virtual environment and install
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

This installs the `pdf-duplex-app` command globally in your virtual environment.

### Option 2: pipx (isolated install)

```bash
pipx install git+https://github.com/your-username/pdf-duplex-app.git
```

### Option 3: AppImage (portable, no dependencies)

1. Download the latest `PDFDuplexPrinter-*.AppImage` from [Releases](https://github.com/your-username/pdf-duplex-app/releases)
2. Make it executable and run:
```bash
chmod +x PDFDuplexPrinter-*.AppImage
./PDFDuplexPrinter-*.AppImage
```

### Option 4: Flatpak (sandboxed)

```bash
# Add Flathub if not already added
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install from Flathub (when published)
flatpak install flathub com.example.pdfduplexapp

# Or install from local build
flatpak install --user pdf-duplex-app.flatpak
```

### System Dependencies (required for all methods)

- CUPS printing system (`cups` package)
- `lp` command available in PATH
- Qt6 libraries (usually pulled in by PyQt6)

On Fedora:
```bash
sudo dnf install cups qt6-qtbase
```

On Ubuntu/Debian:
```bash
sudo apt install cups libqt6core6 libqt6gui6 libqt6widgets6 libqt6pdf6
```

On Arch:
```bash
sudo pacman -S cups qt6-base qt6-pdf
```

## Usage

### From virtual environment
```bash
source venv/bin/activate
pdf-duplex-app
# or
python run.py
```

### Installed via pipx or system pip
```bash
pdf-duplex-app
```

### AppImage
```bash
./PDFDuplexPrinter-*.AppImage
```

### Flatpak
```bash
flatpak run com.example.pdfduplexapp
```

### GUI Overview

1. **Open PDF** — Click "Open PDF" to load a file. First page renders in the preview area.
2. **Select Printer** — Choose from detected CUPS printers (dropdown).
3. **Choose Mode**:
   - **Normal** — Print as-is, all pages in order.
   - **Manual Duplex** — Prints odd pages first, prompts to flip stack, then prints even pages in reverse.
   - **Booklet** — Imposes 2 pages per sheet (half-width), prints in booklet order for folding.
4. **Options**:
   - **Invert pages** — (Placeholder) Check to invert page order on second side.
5. **Print** — Starts the print workflow. For duplex/booklet modes, a dialog will prompt you to flip and reinsert paper.

## Theme Settings

The application respects the system Qt theme. To customize:

### Force Light/Dark Mode
```bash
# Light
QT_STYLE_OVERRIDE=fusion QT_QUICK_CONTROLS_STYLE=fusion pdf-duplex-app

# Dark (using qt6ct or Kvantum)
export QT_QPA_PLATFORMTHEME=qt6ct
pdf-duplex-app
```

### Using qt6ct (recommended for Linux)
```bash
sudo dnf install qt6ct  # or apt install qt6ct
qt6ct  # Configure theme, fonts, icon theme
export QT_QPA_PLATFORMTHEME=qt6ct
pdf-duplex-app
```

### Using Kvantum
```bash
sudo dnf install kvantum-qt6
kvantummanager  # Pick a theme
export QT_STYLE_OVERRIDE=kvantum
pdf-duplex-app
```

### High DPI / Fractional Scaling
```bash
export QT_ENABLE_HIGHDPI_SCALING=1
export QT_SCALE_FACTOR=1.5  # or QT_AUTO_SCREEN_SCALE_FACTOR=1
pdf-duplex-app
```

## Development Setup

### Prerequisites
- Python 3.11+
- uv (recommended) or pip + venv
- CUPS development headers (for printing tests)

```bash
# Fedora
sudo dnf install python3.11 python3.11-venv cups-devel qt6-qtbase-devel

# Ubuntu/Debian
sudo apt install python3.11 python3.11-venv libcups2-dev qt6-base-dev

# Arch
sudo pacman -S python cups qt6-base
```

### Quick Start
```bash
git clone <repository-url>
cd pdf-duplex-app

# Using uv (fastest)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or using pip
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Development Dependencies
```toml
# In pyproject.toml under [project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-qt>=4.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
    "pre-commit>=3.0",
]
```

### Running Tests
```bash
pytest -v
pytest --cov=src --cov-report=term-missing
```

### Code Quality
```bash
ruff check .
ruff format .
mypy .
pre-commit run --all-files
```

### Building AppImage
```bash
# Requires linuxdeploy and linuxdeploy-plugin-qt
pip install -e ".[appimage]"
python -m build_appimage
```

### Building Flatpak
```bash
flatpak-builder --user --install --force-clean build-dir com.example.pdfduplexapp.yml
```

## Testing

Run the unit tests:
```bash
source venv/bin/activate
pytest
```

With coverage:
```bash
pytest --cov=. --cov-report=html
```

## Notes

- Manual duplex and booklet imposition assume long-edge flip (flip over like a book).
- The booklet imposition places two pages per sheet, scaled to half width, ready for duplex printing.
- Page inversion is not yet implemented (stretch goal).
- For the best experience, ensure your printer is configured in CUPS and the `lp` command works.

## License