"""
src/theme.py - Modern 2026 Zed-inspired theme engine for PyQt6.
Provides Dark and Light palettes, QSS stylesheets, and theme management.
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

SETTINGS_KEY = "AppTheme"

# Design Tokens - Custom Dark Theme
# bg: #28282E, container bg: #212126, text: #EEEEEE, secondary text: #636363, accent: #E64B3D
DARK_STYLE = """
/* Global Window & Typography */
QMainWindow, QDialog, QWidget {
    background-color: #28282E;
    color: #EEEEEE;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* Panels & Surfaces (Container BG) */
QWidget#sidebarPanel, QWidget#settingsPanel, QWidget#previewContainer {
    background-color: #212126;
}

QSplitter::handle {
    background-color: #36363d;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #E64B3D;
}

/* Toolbars & Headers */
QWidget#topHeader {
    background-color: #28282E;
    border-bottom: 1px solid #36363d;
    padding: 6px 12px;
}

/* Buttons */
QPushButton {
    background-color: #2e2e35;
    color: #EEEEEE;
    border: 1px solid #40404a;
    border-radius: 0px;
    padding: 6px 14px;
    font-weight: 500;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #383842;
    border-color: #555562;
}
QPushButton:pressed {
    background-color: #25252c;
}
QPushButton:disabled {
    background-color: #212126;
    color: #636363;
    border-color: #2e2e35;
}

/* Accent Buttons */
QPushButton#primaryButton {
    background-color: #E64B3D;
    color: #ffffff;
    border: 1px solid #cf3c2f;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background-color: #ec5e52;
    border-color: #E64B3D;
}
QPushButton#primaryButton:pressed {
    background-color: #c9392c;
}

QPushButton#secondaryButton {
    background-color: #28282E;
    color: #E64B3D;
    border: 1px solid #E64B3D;
}
QPushButton#secondaryButton:hover {
    background-color: #382424;
    border-color: #ec5e52;
}

/* Mode Pill Radio Buttons */
QRadioButton {
    color: #EEEEEE;
    spacing: 8px;
    padding: 6px 10px;
    border-radius: 0px;
}
QRadioButton:hover {
    background-color: #2e2e35;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid #636363;
    background-color: #212126;
}
QRadioButton::indicator:checked {
    background-color: #E64B3D;
    border-color: #E64B3D;
}

/* Checkboxes */
QCheckBox {
    color: #EEEEEE;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 0px;
    border: 1px solid #40404a;
    background-color: #212126;
}
QCheckBox::indicator:checked {
    background-color: #E64B3D;
    border-color: #E64B3D;
    image: none;
}
QCheckBox::indicator:hover {
    border-color: #636363;
}

/* Inputs & Comboboxes */
QComboBox, QSpinBox, QLineEdit {
    background-color: #212126;
    color: #EEEEEE;
    border: 1px solid #36363d;
    border-radius: 0px;
    padding: 5px 10px;
    min-height: 20px;
}
QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
    border-color: #636363;
}
QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
    border-color: #E64B3D;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #212126;
    color: #EEEEEE;
    border: 1px solid #40404a;
    selection-background-color: #E64B3D;
    selection-color: #ffffff;
    border-radius: 0px;
    padding: 4px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background-color: transparent;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #36363d;
    min-height: 24px;
    border-radius: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #636363;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    border: none;
}

QScrollBar:horizontal {
    border: none;
    background-color: transparent;
    height: 8px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background-color: #36363d;
    min-width: 24px;
    border-radius: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #636363;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    border: none;
}

/* Badges, Cards & Headers */
QLabel#sectionTitle {
    font-size: 11px;
    font-weight: 700;
    color: #636363;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 10px;
    margin-bottom: 4px;
}

QLabel#pillBadge {
    background-color: #382424;
    color: #E64B3D;
    border: 1px solid #E64B3D;
    border-radius: 0px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#metaLabel {
    color: #636363;
    font-size: 12px;
}

/* Floating Zoom Capsule */
QWidget#floatingZoomBar {
    background-color: #212126f0;
    border: 1px solid #40404a;
    border-radius: 0px;
}
QWidget#floatingZoomBar QPushButton {
    background-color: #28282E;
    color: #EEEEEE;
    border: 1px solid #40404a;
    border-radius: 0px;
    padding: 3px 10px;
    min-height: 18px;
    font-size: 11px;
}
QWidget#floatingZoomBar QPushButton:hover {
    background-color: #E64B3D;
    color: #ffffff;
    border-color: #E64B3D;
}

/* Progress Bar */
QProgressBar {
    background-color: #28282E;
    border: 1px solid #36363d;
    border-radius: 0px;
    text-align: center;
    color: #EEEEEE;
}
QProgressBar::chunk {
    background-color: #E64B3D;
    border-radius: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #212126;
    color: #636363;
    border-top: 1px solid #28282E;
    font-size: 11px;
}

/* Group Box */
QGroupBox {
    border: 1px solid #36363d;
    border-radius: 0px;
    margin-top: 14px;
    padding: 12px;
    background-color: #212126;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: #E64B3D;
    font-weight: 600;
    font-size: 11px;
}

/* Bottom Navigation Bar */
QWidget#bottomBar {
    background-color: #212126;
    border-top: 1px solid #36363d;
    padding: 4px 8px;
}
QWidget#bottomBar QPushButton {
    background-color: #2e2e35;
    color: #EEEEEE;
    border: 1px solid #40404a;
    border-radius: 0px;
    padding: 4px 10px;
    min-height: 22px;
    font-size: 12px;
}
QWidget#bottomBar QPushButton:hover {
    background-color: #383842;
    border-color: #555562;
}
QWidget#bottomBar QPushButton:disabled {
    color: #636363;
    background-color: #212126;
    border-color: #2e2e35;
}
QWidget#bottomBar QLabel {
    color: #636363;
    font-size: 11px;
}
"""

# Design Tokens - Zed Light
LIGHT_STYLE = """
/* Global Window & Typography */
QMainWindow, QDialog, QWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* Panels & Surfaces */
QWidget#sidebarPanel, QWidget#settingsPanel, QWidget#previewContainer {
    background-color: #ffffff;
}

QSplitter::handle {
    background-color: #e2e8f0;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #0284c7;
}

/* Toolbars & Headers */
QWidget#topHeader {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 6px 12px;
}

/* Buttons */
QPushButton {
    background-color: #f1f5f9;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 0px;
    padding: 6px 14px;
    font-weight: 500;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #e2e8f0;
    border-color: #94a3b8;
}
QPushButton:pressed {
    background-color: #cbd5e1;
}
QPushButton:disabled {
    background-color: #f8fafc;
    color: #94a3b8;
    border-color: #e2e8f0;
}

/* Accent Buttons */
QPushButton#primaryButton {
    background-color: #0284c7;
    color: #ffffff;
    border: 1px solid #0369a1;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background-color: #0369a1;
    border-color: #075985;
}
QPushButton#primaryButton:pressed {
    background-color: #0c4a6e;
}

QPushButton#secondaryButton {
    background-color: #f0f9ff;
    color: #0284c7;
    border: 1px solid #bae6fd;
}
QPushButton#secondaryButton:hover {
    background-color: #e0f2fe;
    border-color: #0284c7;
}

/* Mode Pill Radio Buttons */
QRadioButton {
    color: #334155;
    spacing: 8px;
    padding: 6px 10px;
    border-radius: 0px;
}
QRadioButton:hover {
    background-color: #f1f5f9;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid #94a3b8;
    background-color: #ffffff;
}
QRadioButton::indicator:checked {
    background-color: #0284c7;
    border-color: #0284c7;
}

/* Checkboxes */
QCheckBox {
    color: #334155;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 0px;
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #0284c7;
}
QCheckBox::indicator:hover {
    border-color: #64748b;
}

/* Inputs & Comboboxes */
QComboBox, QSpinBox, QLineEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 0px;
    padding: 5px 10px;
    min-height: 20px;
}
QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
    border-color: #94a3b8;
}
QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
    border-color: #0284c7;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    border-radius: 0px;
    padding: 4px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background-color: transparent;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    min-height: 24px;
    border-radius: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #94a3b8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    border: none;
}

QScrollBar:horizontal {
    border: none;
    background-color: transparent;
    height: 8px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background-color: #cbd5e1;
    min-width: 24px;
    border-radius: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #94a3b8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    border: none;
}

/* Badges, Cards & Headers */
QLabel#sectionTitle {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 10px;
    margin-bottom: 4px;
}

QLabel#pillBadge {
    background-color: #e0f2fe;
    color: #0369a1;
    border: 1px solid #bae6fd;
    border-radius: 0px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#metaLabel {
    color: #64748b;
    font-size: 12px;
}

/* Status Bar */
QStatusBar {
    background-color: #f1f5f9;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    font-size: 11px;
}

/* Group Box */
QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 0px;
    margin-top: 14px;
    padding: 12px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: #0369a1;
    font-weight: 600;
    font-size: 11px;
}
"""


def get_theme_stylesheet(theme_name: str) -> str:
    """Return the QSS stylesheet for dark or light."""
    if theme_name.lower() == "light":
        return LIGHT_STYLE
    return DARK_STYLE


def apply_theme(app: QApplication, theme_name: str):
    """Apply the chosen theme to the entire application and persist in QSettings."""
    theme_name = theme_name.lower()
    if theme_name not in ("dark", "light"):
        theme_name = "dark"
    
    app.setStyleSheet(get_theme_stylesheet(theme_name))
    
    settings = QSettings("PdfDuplexApp", "ModernTheme")
    settings.setValue(SETTINGS_KEY, theme_name)


def load_saved_theme(app: QApplication) -> str:
    """Load and apply saved theme on startup (defaults to dark)."""
    settings = QSettings("PdfDuplexApp", "ModernTheme")
    saved = settings.value(SETTINGS_KEY, "dark")
    apply_theme(app, saved)
    return saved
