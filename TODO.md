# TODO List for PDF Duplex/Booklet Printer

## Completed
- [x] Project setup (venv, deps: PyQt6, pypdf, reportlab, pytest, pytest-qt)
- [x] Imposer module: normal mode (byte-for-byte copy)
- [x] Imposer module: duplex mode (page reordering for manual duplex)
- [x] Imposer module: booklet mode (basic imposition with scaling and positioning)
- [x] Unit tests for imposer (normal, duplex, booklet page count)
- [x] GUI main window skeleton (toolbar, preview area, status bar)
- [x] PDF loading and basic rendering (first page preview)
- [x] Placeholder for invert button and print button

## In Progress
- [ ] GUI: Integrate imposer modes with print button
- [ ] GUI: Implement print workflow with flip-prompt for duplex/booklet
- [ ] GUI: Implement page inversion (stretch goal)
- [ ] GUI: Improve preview to show multiple pages or allow navigation
- [ ] GUI: Add printer selection dialog (optional)
- [ ] Utility: Implement print_pdf using lp (CUPS)
- [ ] Utility: Implement flip_prompt (GUI message box)
- [ ] Testing: Add GUI tests for print workflow (using qtbot)
- [ ] Documentation: README.md with usage instructions
- [ ] Packaging: pyproject.toml and desktop launcher

## Future / Stretch Goals
- [ ] Support for custom paper sizes (based on input PDF)
- [ ] Option to choose binding orientation (short-edge vs long-edge flip)
- [ ] Embed native print dialog via QtPrintSupport (optional)
- [ ] Advanced inversion (vector or raster with Pillow)
- [ ] Drag-and-drop PDF loading
- [ ] Remember last opened directory
- [ ] Keyboard shortcuts

## Notes
- The imposer module uses pypdf for page manipulation.
- The GUI uses PyQt6.QtPdf for PDF rendering (vector-based preview).
- Printing is delegated to the system's `lp` command (CUPS).
- For duplex/booklet, the imposer returns a PDF ready for duplex printing (user flips after first side).