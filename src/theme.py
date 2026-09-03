"""
src/theme.py - Antigravity Dark Theme and Stylesheets
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

SETTINGS_KEY = "modern_theme_selection"

# Global font family for all elements
FONT_FAMILY = "'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif"

# Design Tokens - Antigravity Dark Pro
DARK_STYLE = f"""
/* Global Window & Typography */
QMainWindow, QDialog, QWidget {{
    background-color: #28282E;
    color: #EEEEEE;
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}

/* Panels & Surfaces */
QWidget#sidebarPanel, QWidget#settingsPanel, QWidget#previewContainer {{
    background-color: #212126;
}}

QSplitter::handle {{
    background-color: #36363D;
    width: 2px;
    height: 2px;
}}
QSplitter::handle:hover {{
    background-color: #4A4A52;
}}

/* Toolbars & Headers */
QWidget#topHeader {{
    background-color: #212126;
    border-bottom: 1px solid #36363D;
    padding: 6px 12px;
}}

/* Buttons */
QPushButton {{
    background-color: #2C2C34;
    color: #EEEEEE;
    border: 1px solid #36363D;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    min-height: 18px;
}}
QPushButton:hover {{
    background-color: #36363D;
    border-color: #555562;
}}
QPushButton:pressed {{
    background-color: #1E1E24;
}}
QPushButton:disabled {{
    background-color: #212126;
    color: #636363;
    border-color: #2C2C34;
}}

/* Accent Buttons (Minimal Use) */
QPushButton#primaryButton {{
    background-color: #E64B3D;
    color: #FFFFFF;
    border: 1px solid #E64B3D;
    font-weight: 600;
}}
QPushButton#primaryButton:hover {{
    background-color: #D34033;
    border-color: #D34033;
}}
QPushButton#primaryButton:pressed {{
    background-color: #B5362B;
}}

QPushButton#secondaryButton {{
    background-color: #2C2C34;
    color: #EEEEEE;
    border: 1px solid #36363D;
}}
QPushButton#secondaryButton:hover {{
    background-color: #36363D;
    border-color: #555562;
}}

/* Mode Pill Radio Buttons */
QRadioButton {{
    color: #EEEEEE;
    spacing: 8px;
    padding: 6px 10px;
    border-radius: 6px;
}}
QRadioButton:hover {{
    background-color: #2C2C34;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid #636363;
    background-color: #28282E;
}}
QRadioButton::indicator:checked {{
    background-color: #E64B3D;
    border-color: #E64B3D;
}}

/* Checkboxes */
QCheckBox {{
    color: #EEEEEE;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #636363;
    background-color: #28282E;
}}
QCheckBox::indicator:checked {{
    background-color: #E64B3D;
    border-color: #E64B3D;
}}
QCheckBox::indicator:hover {{
    border-color: #EEEEEE;
}}

/* Inputs & Comboboxes */
QComboBox, QSpinBox, QLineEdit {{
    background-color: #212126;
    color: #EEEEEE;
    border: 1px solid #36363D;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 20px;
}}
QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{
    border-color: #636363;
}}
QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
    border-color: #E64B3D;
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: #212126;
    color: #EEEEEE;
    border: 1px solid #36363D;
    selection-background-color: #36363D;
    selection-color: #EEEEEE;
    border-radius: 6px;
    padding: 4px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background-color: transparent;
    width: 8px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background-color: #36363D;
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: #636363;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    border: none;
}}

QScrollBar:horizontal {{
    border: none;
    background-color: transparent;
    height: 8px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background-color: #36363D;
    min-width: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: #636363;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
    border: none;
}}

/* Badges, Cards & Headers */
QLabel#sectionTitle {{
    font-size: 11px;
    font-weight: 700;
    color: #636363;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 10px;
    margin-bottom: 4px;
}}

QLabel#pillBadge {{
    background-color: #2C2C34;
    color: #EEEEEE;
    border: 1px solid #36363D;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QLabel#metaLabel {{
    color: #888890;
    font-size: 12px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: #212126;
    border: 1px solid #36363D;
    border-radius: 6px;
    text-align: center;
    color: #EEEEEE;
}}
QProgressBar::chunk {{
    background-color: #E64B3D;
    border-radius: 4px;
}}

/* Status Bar */
QStatusBar {{
    background-color: #212126;
    color: #888890;
    border-top: 1px solid #36363D;
    font-size: 11px;
}}

/* Group Box */
QGroupBox {{
    border: 1px solid #36363D;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px;
    background-color: #212126;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: #EEEEEE;
    font-weight: 600;
    font-size: 11px;
}}

/* Bottom Navigation Bar */
QWidget#bottomBar {{
    background-color: #212126;
    border-top: 1px solid #36363D;
    padding: 4px 8px;
}}
QWidget#bottomBar QPushButton {{
    background-color: #2C2C34;
    color: #EEEEEE;
    border: 1px solid #36363D;
    border-radius: 6px;
    padding: 4px 10px;
    min-height: 22px;
    font-size: 12px;
}}
QWidget#bottomBar QPushButton:hover {{
    background-color: #36363D;
    border-color: #555562;
}}
QWidget#bottomBar QPushButton:disabled {{
    color: #636363;
    background-color: #212126;
    border-color: #2C2C34;
}}
QWidget#bottomBar QLabel {{
    color: #888890;
    font-size: 11px;
}}
"""

LIGHT_STYLE = DARK_STYLE  # Fallback just in case

def get_theme_stylesheet(theme_name: str) -> str:
    return DARK_STYLE

def apply_theme(app: QApplication, theme_name: str):
    app.setStyleSheet(get_theme_stylesheet("dark"))
    settings = QSettings("PdfDuplexApp", "ModernTheme")
    settings.setValue(SETTINGS_KEY, "dark")

def load_saved_theme(app: QApplication) -> str:
    settings = QSettings("PdfDuplexApp", "ModernTheme")
    saved = settings.value(SETTINGS_KEY, "dark")
    apply_theme(app, saved)
    return saved
