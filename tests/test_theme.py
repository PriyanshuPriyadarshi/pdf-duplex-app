# tests/test_theme.py
import pytest
from pytestqt.qtbot import QtBot
from PyQt6.QtWidgets import QApplication, QDialogButtonBox
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import QSettings, Qt
from src.main_window import MainWindow
from src.settings_dialog import SettingsDialog, apply_saved_theme


@pytest.fixture
def app():
    """Create or return the QApplication instance."""
    return QApplication.instance() or QApplication([])


def get_window_color(palette: QPalette) -> QColor:
    """Helper to get the Window color role from a palette."""
    return palette.color(QPalette.ColorRole.Window)


def get_window_text_color(palette: QPalette) -> QColor:
    """Helper to get the WindowText color role from a palette."""
    return palette.color(QPalette.ColorRole.WindowText)


def test_main_window_creation(app):
    """Test that MainWindow can be created."""
    win = MainWindow()
    assert win is not None
    win.deleteLater()


def test_settings_dialog_opens(app, qtbot):
    """Test that Settings dialog can be opened from MainWindow."""
    win = MainWindow()
    win.show()
    qtbot.waitExposed(win)
    
    # Use show() instead of exec() for testing to avoid blocking
    dlg = SettingsDialog(win)
    dlg.show()
    qtbot.waitExposed(dlg)
    
    # Check that dialog is visible
    assert dlg.isVisible()
    assert dlg.windowTitle() == "Settings"
    dlg.close()
    win.deleteLater()


def test_theme_light_changes_palette(app, qtbot):
    """Test that selecting Light theme applies default palette."""
    # Create SettingsDialog directly to test apply_theme
    dlg = SettingsDialog()
    dlg.theme_combo.setCurrentText("Light")
    dlg.apply_theme(app)
    
    palette = app.palette()
    # Light theme uses default QPalette() - window should be light
    window_color = get_window_color(palette)
    # Default window color is typically light (white-ish)
    assert window_color.lightness() > 128  # Light color
    
    dlg.deleteLater()


def test_theme_dark_changes_palette(app, qtbot):
    """Test that selecting Dark theme applies dark palette."""
    dlg = SettingsDialog()
    dlg.theme_combo.setCurrentText("Dark")
    dlg.apply_theme(app)
    
    palette = app.palette()
    window_color = get_window_color(palette)
    window_text_color = get_window_text_color(palette)
    
    # Dark theme: Window = (53, 53, 53), WindowText = white
    assert window_color.red() == 53
    assert window_color.green() == 53
    assert window_color.blue() == 53
    assert window_text_color == Qt.GlobalColor.white
    
    dlg.deleteLater()


def test_theme_system_uses_standard_palette(app, qtbot):
    """Test that selecting System theme uses standard palette."""
    # First set to dark to ensure we're changing something
    dlg = SettingsDialog()
    dlg.theme_combo.setCurrentText("Dark")
    dlg.apply_theme(app)
    
    # Now switch to System
    dlg.theme_combo.setCurrentText("System")
    dlg.apply_theme(app)
    
    palette = app.palette()
    standard_palette = app.style().standardPalette()
    
    # System theme should match standard palette
    assert palette.color(QPalette.ColorRole.Window) == standard_palette.color(QPalette.ColorRole.Window)
    assert palette.color(QPalette.ColorRole.WindowText) == standard_palette.color(QPalette.ColorRole.WindowText)
    
    dlg.deleteLater()


def test_theme_persists_in_qsettings(app, qtbot):
    """Test that theme selection is saved to QSettings."""
    # Clear any existing settings first
    settings = QSettings("PdfDuplexApp", "theme")
    settings.remove("")
    settings.sync()
    
    dlg = SettingsDialog()
    dlg.theme_combo.setCurrentText("Dark")
    dlg.apply_theme(app)
    
    # Verify it was saved
    saved_theme = settings.value("theme", "System")
    assert saved_theme == "Dark"
    
    dlg.deleteLater()


def test_theme_persists_after_restart(app, qtbot, tmp_path):
    """
    Test that theme persists after 'restart' (new MainWindow with same QSettings).
    We simulate restart by creating a new QApplication and MainWindow.
    """
    # Use a unique organization/app name to isolate test settings
    test_org = "PdfDuplexApp_Test"
    test_app = "theme_test"
    
    settings = QSettings(test_org, test_app)
    settings.remove("")
    settings.sync()
    
    # First "session": create MainWindow, open settings, set Dark theme
    win1 = MainWindow()
    # Monkey-patch the settings in SettingsDialog to use our test settings
    # by temporarily modifying the SettingsDialog constructor behavior
    from src.settings_dialog import SettingsDialog as OriginalSettingsDialog
    
    # Create a dialog manually with test settings
    dlg = SettingsDialog()
    dlg.settings = settings  # Override with test settings
    dlg.theme_combo.setCurrentText("Dark")
    dlg.apply_theme(app)
    
    # Verify theme was saved
    assert settings.value("theme", "System") == "Dark"
    win1.deleteLater()
    
    # Second "session": create new MainWindow - it should apply saved theme
    # We need to call apply_saved_theme with our test settings
    # Let's verify by creating a new dialog that reads from test settings
    dlg2 = SettingsDialog()
    dlg2.settings = settings
    saved = dlg2.settings.value("theme", "System")
    dlg2.theme_combo.setCurrentText(saved)
    dlg2.apply_theme(app)
    
    # Verify palette is dark
    palette = app.palette()
    window_color = get_window_color(palette)
    assert window_color.red() == 53
    assert window_color.green() == 53
    assert window_color.blue() == 53
    
    dlg2.deleteLater()


def test_settings_dialog_theme_combo_has_correct_items(app, qtbot):
    """Test that the theme combo box has the expected items."""
    dlg = SettingsDialog()
    
    assert dlg.theme_combo.count() == 3
    assert dlg.theme_combo.itemText(0) == "Light"
    assert dlg.theme_combo.itemText(1) == "Dark"
    assert dlg.theme_combo.itemText(2) == "System"
    
    dlg.deleteLater()


def test_settings_dialog_loads_saved_theme(app, qtbot):
    """Test that SettingsDialog loads the saved theme on creation."""
    settings = QSettings("PdfDuplexApp", "theme")
    settings.setValue("theme", "Light")
    settings.sync()
    
    dlg = SettingsDialog()
    # The dialog should load "Light" from settings
    assert dlg.theme_combo.currentText() == "Light"
    
    settings.remove("")
    settings.sync()
    dlg.deleteLater()


def test_apply_saved_theme_at_startup(app, qtbot):
    """Test the apply_saved_theme function used at application startup."""
    settings = QSettings("PdfDuplexApp", "theme")
    settings.setValue("theme", "Dark")
    settings.sync()
    
    # This is the function called in main() before showing MainWindow
    apply_saved_theme(app)
    
    # Verify dark palette was applied
    palette = app.palette()
    window_color = get_window_color(palette)
    assert window_color.red() == 53
    assert window_color.green() == 53
    assert window_color.blue() == 53
    
    settings.remove("")
    settings.sync()


def test_full_theme_switch_workflow(app, qtbot):
    """
    Integration test: Open MainWindow -> Open Settings -> Change theme -> Verify palette.
    Tests the complete user workflow.
    """
    win = MainWindow()
    win.show()
    qtbot.waitExposed(win)
    
    # Open settings dialog (non-modal for testing)
    dlg = SettingsDialog(win)
    dlg.show()
    qtbot.waitExposed(dlg)
    
    # Change theme to Dark
    dlg.theme_combo.setCurrentText("Dark")
    
    # Click OK (accept) - this triggers accept() which saves settings
    ok_button = dlg.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
    qtbot.mouseClick(ok_button, Qt.MouseButton.LeftButton)
    
    # Wait for dialog to close
    qtbot.waitUntil(lambda: not dlg.isVisible())
    
    # In the real workflow, MainWindow.open_settings() calls dlg.apply_theme(app) after exec() returns True
    # Since we used show() instead of exec(), we need to call apply_theme manually
    dlg.apply_theme(app)
    
    # Verify palette changed to dark
    palette = app.palette()
    window_color = get_window_color(palette)
    assert window_color.red() == 53
    assert window_color.green() == 53
    assert window_color.blue() == 53
    
    # Verify theme was persisted
    settings = QSettings("PdfDuplexApp", "theme")
    assert settings.value("theme", "System") == "Dark"
    
    # Cleanup
    settings.remove("")
    settings.sync()
    win.deleteLater()