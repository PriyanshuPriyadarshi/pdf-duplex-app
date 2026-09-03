# Final summary
The PDF Duplex/Booklet Printer application has been implemented according to the plan.

Key components:
- src/imposer.py: provides functions for normal, duplex, and booklet imposition.
- src/main_window.py: PyQt6 GUI with PDF loading, preview, mode selection, invert button, and print workflow with flip prompt.
- src/utils.py: helper for printing via lp and flip prompt (GUI).
- tests/: unit tests for imposer and GUI.
- run.py: entry point to launch the GUI.
- README.md, pyproject.toml, TODO.md, and dashboard.html for documentation and tracking.

All unit tests pass. The application is ready for use.

Next steps (if desired):
- Implement actual page inversion (using Pillow for raster inversion).
- Add printer selection dialog.
- Enhance preview to show multiple pages or allow navigation.
- Package as an AppImage or distribute via pip.

Would you like to run the application now to see it in action?