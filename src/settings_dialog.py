"""
src/settings_dialog.py - Global application settings modal.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QDialogButtonBox
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QPalette, QColor


class SettingsDialog(QDialog):
    """Dialog for application settings: theme selection."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(300, 120)

        self.settings = QSettings("PdfDuplexApp", "theme")

        layout = QVBoxLayout(self)

        # Theme selector
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        # Load saved theme
        saved = self.settings.value("theme", "System")
        index = self.theme_combo.findText(saved)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_theme(self) -> str:
        """Return the currently selected theme string."""
        return self.theme_combo.currentText()

    def apply_theme(self, app):
        """Apply the selected theme to the given QApplication."""
        theme = self.get_selected_theme()
        if theme == "Light":
            app.setPalette(QPalette())
        elif theme == "Dark":
            dark = QPalette()
            dark.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            dark.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            dark.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            dark.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            dark.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            dark.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            dark.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            dark.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            app.setPalette(dark)
        else:  # System
            app.setPalette(app.style().standardPalette())

        # Persist
        self.settings.setValue("theme", theme)


def apply_saved_theme(app):
    """Apply the theme saved in QSettings at startup."""
    settings = QSettings("PdfDuplexApp", "theme")
    saved = settings.value("theme", "System")
    # Create a temporary dialog to reuse its apply_theme logic
    dlg = SettingsDialog()
    dlg.theme_combo.setCurrentText(saved)
    dlg.apply_theme(app)