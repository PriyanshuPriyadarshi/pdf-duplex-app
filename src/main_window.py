"""
src/main_window.py - Modern 2026 three-panel main window for PDF Manual Duplex & Booklet Studio.
Features pure edge-to-edge layout, right-hand control & document panel, and default Zed Dark theme.
"""

import sys
import os
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QStatusBar,
    QMessageBox,
    QSplitter,
)
from PyQt6.QtGui import QFont, QAction, QKeySequence, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt
from PyQt6.QtPdf import QPdfDocument

from src.theme import apply_theme, load_saved_theme
from src.sidebar_page_list import SidebarPageList
from src.center_preview import CenterPreview
from src.settings_panel import SettingsPanel
from src import imposer
from src import utils


class _ModeComboAdapter:
    """Adapter allowing legacy code and tests to interact with mode_combo.currentText()"""
    def __init__(self, settings_panel):
        self._panel = settings_panel

    def currentText(self) -> str:
        return self._panel.get_current_mode()

    def setCurrentText(self, text: str):
        self._panel.set_current_mode(text)


class MainWindow(QMainWindow):
    """Main window organizing the 2026 three-panel workstation layout."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Duplex & Booklet Studio")
        self.resize(1200, 780)
        self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)

        self.pdf_doc = QPdfDocument(self)
        self.current_file_path = ""
        self.current_pdf_bytes: bytes = b""
        self.total_pages = 0
        self.selected_page_indices = None
        self.current_theme = "dark"

        self._setup_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._refresh_printers()

        # Compatibility adapter for mode selection
        self.mode_combo = _ModeComboAdapter(self.settings_panel)

    def print_document(self):
        """Compatibility method for direct programmatic printing and test execution."""
        if not self.current_file_path or self.total_pages == 0:
            return

        mode = self.settings_panel.get_current_mode()
        inverted_pages = self.sidebar.get_inverted_pages()
        invert = inverted_pages if inverted_pages else False
        if mode == "Normal":
            pdf_bytes = imposer.impose_normal(self.current_file_path, invert=invert)
            print_pdf(pdf_bytes, is_duplex=False)
        else:
            if mode == "Manual Duplex":
                p1, p2 = imposer.get_duplex_passes(self.current_file_path, invert=invert)
            else:
                p1, p2 = imposer.get_booklet_passes(self.current_file_path, invert=invert)

            print_pdf(p1, is_duplex=False)
            if show_flip_prompt(self):
                print_pdf(p2, is_duplex=False)

    def handle_print(self):
        """Handle print action from menu or keyboard shortcut."""
        self.print_document()

    def print_pdf(self, pdf_bytes: bytes, is_duplex: bool = False) -> None:
        """Print the given PDF bytes using the system's lp command.
        This function is provided for backward compatibility with tests.
        """
        from src import utils
        utils.print_pdf(pdf_bytes, is_duplex)

    def show_flip_prompt(self, parent=None) -> bool:
        """Show a message box asking the user to flip the stack and reinsert.
        Returns True if user clicked OK, False if cancelled.
        This function is provided for backward compatibility with tests.
        """
        from src import utils
        return utils.show_flip_prompt(parent)

    def _setup_ui(self):
        # 1. Main Three-Panel Layout via QSplitter (spans full window height)
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)

        # Left: Sidebar Page List
        self.sidebar = SidebarPageList(self)
        self.splitter.addWidget(self.sidebar)

        # Center: Interactive Print Preview with floating controls
        self.center_preview = CenterPreview(self)
        self.splitter.addWidget(self.center_preview)

        # Right: Settings & Document Inspector Panel
        self.settings_panel = SettingsPanel(self)
        self.splitter.addWidget(self.settings_panel)

        # Proportions: 240px, flexible center, 310px
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        self.splitter.setSizes([240, 680, 310])

        self.setCentralWidget(self.splitter)

        # Compatibility aliases for legacy buttons
        self.btn_open = self.settings_panel.btn_open_pdf
        self.lbl_file_info = self.settings_panel.lbl_doc_stats
        self.btn_theme_toggle = QPushButton(self)
        self.btn_theme_toggle.setVisible(False)

        # 2. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready • Drag and drop a PDF file or open from the right panel")

    def _connect_signals(self):
        self.settings_panel.open_pdf_clicked.connect(self.open_file_dialog)

        # Left Sidebar card click -> Updates Center Preview
        self.sidebar.card_selected.connect(self.center_preview.set_sheet)

        # Left Sidebar inversion -> Updates Center Preview
        self.sidebar.inversion_changed.connect(self.center_preview.set_inverted_pages)

        # Center Preview navigation -> Highlights sidebar card
        self.center_preview.sheet_navigated.connect(self._on_preview_navigated)

        # Right Settings Panel mode change -> Updates both Sidebar and Center Preview
        self.settings_panel.mode_changed.connect(self._on_mode_changed)
        self.settings_panel.options_changed.connect(self._on_options_changed)

        # Action Buttons
        self.settings_panel.btn_open_normal.clicked.connect(self.handle_open_normal)
        self.settings_panel.btn_open_fronts.clicked.connect(self.handle_open_fronts)
        self.settings_panel.btn_open_backs.clicked.connect(self.handle_open_backs)
        self.sidebar.page_range_changed.connect(self.handle_page_range_changed)

    def _setup_shortcuts(self):
        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file_dialog)
        self.addAction(open_action)

        print_action = QAction("Print", self)
        print_action.setShortcut(QKeySequence("Ctrl+P"))
        print_action.triggered.connect(self.handle_print)
        self.addAction(print_action)

        theme_action = QAction("Toggle Theme", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.triggered.connect(self.toggle_theme)
        self.addAction(theme_action)

    def _refresh_printers(self):
        printers = utils.get_available_printers()
        self.settings_panel.set_available_printers(printers)

    def toggle_theme(self):
        # Default is Dark mode
        app = QApplication.instance()
        self.current_theme = "dark"
        apply_theme(app, "dark")

    def open_settings_dialog(self):
        """Open the settings dialog."""
        from src.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        dlg.exec()

    def handle_page_range_changed(self, range_str: str):
        """Handle page range changes from the sidebar."""
        if not self.pdf_doc or self.total_pages == 0:
            return

        from src import utils
        if not range_str.strip():
            self.selected_page_indices = None
            self.status_bar.showMessage(f"All {self.total_pages} pages included")
        else:
            try:
                self.selected_page_indices = utils.parse_page_range(range_str, self.total_pages)
                count = len(self.selected_page_indices)
                self.status_bar.showMessage(f"Custom range selected: {count} of {self.total_pages} pages")
            except Exception:
                self.selected_page_indices = None

    def _get_effective_pdf_path(self) -> tuple[str, bool]:
        """Return path to PDF to impose, and a boolean indicating if it is a temporary sliced file."""
        if not self.selected_page_indices or len(self.selected_page_indices) == self.total_pages:
            return self.current_file_path, False

        from pypdf import PdfReader, PdfWriter
        import tempfile
        try:
            reader = PdfReader(self.current_file_path)
            writer = PdfWriter()
            for idx in self.selected_page_indices:
                if 0 <= idx < len(reader.pages):
                    writer.add_page(reader.pages[idx])

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            writer.write(tmp)
            tmp.close()
            return tmp.name, True
        except Exception:
            return self.current_file_path, False

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF Document", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.load_pdf(file_path)

    def load_pdf(self, path: str):
        if not os.path.isfile(path):
            QMessageBox.warning(self, "Error", f"File not found: {path}")
            return

        self.pdf_doc.load(path)
        self.total_pages = self.pdf_doc.pageCount()
        self.current_file_path = path
        try:
            with open(path, "rb") as f:
                self.current_pdf_bytes = f.read()
        except OSError:
            self.current_pdf_bytes = b""

        filename = os.path.basename(path)
        size_kb = os.path.getsize(path) / 1024
        size_str = f"{size_kb / 1024:.1f} MB" if size_kb >= 1024 else f"{size_kb:.0f} KB"

        # Update right panel document information
        self.settings_panel.set_document_info(filename, self.total_pages, size_str)
        self.status_bar.showMessage(f"Loaded: {filename} ({self.total_pages} pages)")

        # Push document to components
        self.sidebar.set_document(self.pdf_doc)
        self.center_preview.set_document(self.pdf_doc)

    def _on_mode_changed(self, mode: str):
        self.sidebar.set_mode(mode)
        self.center_preview.set_mode(mode)
        self.status_bar.showMessage(f"Mode switched to: {mode}")

    def _on_options_changed(self, options: dict):
        self.center_preview.update_preview()

    def _on_preview_navigated(self, sheet_idx: int, is_back: bool):
        """When user navigates via center preview bottom bar, highlight the sidebar card."""
        # Update sidebar selection to match
        for i, card in enumerate(self.sidebar._cards):
            if card.sheet_idx == sheet_idx:
                self.sidebar._select_single(i)
                # Scroll to the card
                self.sidebar.scroll_area.ensureWidgetVisible(card)
                break
    def handle_open_normal(self):
        if not self.current_file_path or not self.current_pdf_bytes: return
        self._open_in_viewer("imposed_normal.pdf", self._generate_normal_bytes())

    def handle_open_fronts(self):
        if not self.current_file_path or not self.current_pdf_bytes: return
        pass1, _ = self._generate_split_bytes()
        self._open_in_viewer("imposed_fronts.pdf", pass1)
        
        # Show animation and back button
        self.settings_panel.anim_widget.setVisible(True)
        self.settings_panel.btn_open_backs.setVisible(True)

    def handle_open_backs(self):
        if not self.current_file_path or not self.current_pdf_bytes: return
        _, pass2 = self._generate_split_bytes()
        self._open_in_viewer("imposed_backs.pdf", pass2)

    def _open_in_viewer(self, filename: str, pdf_bytes: bytes):
        import tempfile, os, shutil, subprocess
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        
        tmp_dir = tempfile.gettempdir()
        file_path = os.path.join(tmp_dir, filename)
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
            
        # Prioritize dedicated Linux PDF viewers to prevent recursive self-opening
        for viewer in ["papers", "evince", "okular", "atril", "qpdfview", "xreader", "zathura"]:
            viewer_bin = shutil.which(viewer)
            if viewer_bin:
                try:
                    subprocess.Popen([viewer_bin, file_path], start_new_session=True)
                    return
                except Exception:
                    pass

        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def _generate_normal_bytes(self) -> bytes:
        from src import imposer
        settings = self.settings_panel.get_settings()
        inverted_pages = self.sidebar.get_inverted_pages()
        if self.selected_page_indices and len(self.selected_page_indices) != self.total_pages:
            invert = {i for i, orig_idx in enumerate(self.selected_page_indices) if orig_idx in inverted_pages}
        else:
            invert = inverted_pages if inverted_pages else False
        pdf_path, is_temp = self._get_effective_pdf_path()
        try:
            return imposer.impose_normal(
                pdf_path,
                invert=invert,
                print_page_numbers=settings.get("print_page_numbers", False),
                page_number_pos=settings.get("page_number_pos", "Bottom Right"),
            )
        finally:
            if is_temp:
                try:
                    os.unlink(pdf_path)
                except OSError:
                    pass

    def _generate_split_bytes(self) -> tuple[bytes, bytes]:
        from src import imposer
        settings = self.settings_panel.get_settings()
        mode = settings.get("mode", "Normal")
        inverted_pages = self.sidebar.get_inverted_pages()
        if self.selected_page_indices and len(self.selected_page_indices) != self.total_pages:
            invert = {i for i, orig_idx in enumerate(self.selected_page_indices) if orig_idx in inverted_pages}
        else:
            invert = inverted_pages if inverted_pages else False
        pdf_path, is_temp = self._get_effective_pdf_path()
        try:
            if mode == "Booklet":
                pass1, pass2 = imposer.get_booklet_passes(
                    pdf_path, reverse_backs=False, invert=invert
                )
            else:
                pass1, pass2 = imposer.get_duplex_passes(
                    pdf_path, reverse_backs=False, invert=invert
                )

            if settings.get("print_page_numbers", False):
                pos = settings.get("page_number_pos", "Bottom Right")
                pass1 = imposer._stamp_page_numbers(pass1, pos)
                pass2 = imposer._stamp_page_numbers(pass2, pos)

            return pass1, pass2
        finally:
            if is_temp:
                try:
                    os.unlink(pdf_path)
                except OSError:
                    pass

    def handle_export(self):
        if not self.current_file_path or self.total_pages == 0:
            QMessageBox.warning(self, "No Document", "Please open a PDF file before exporting.")
            return

        settings = self.settings_panel.get_settings()
        mode = settings["mode"]

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Imposed PDF ({mode})",
            f"imposed_{os.path.basename(self.current_file_path)}",
            "PDF Files (*.pdf)",
        )
        if not save_path:
            return

        try:
            # UI Feedback
            if hasattr(self.settings_panel, "btn_export"):
                self.settings_panel.btn_export.setEnabled(False)
                self.settings_panel.btn_export.setText("⌛ Generating...")
            self.status_bar.showMessage("Generating imposed PDF (this may take a moment)...")
            QApplication.processEvents()

            # Get per-page inversion set from sidebar
            inverted_pages = self.sidebar.get_inverted_pages()
            if self.selected_page_indices and len(self.selected_page_indices) != self.total_pages:
                invert = {i for i, orig_idx in enumerate(self.selected_page_indices) if orig_idx in inverted_pages}
            else:
                invert = inverted_pages if inverted_pages else False

            print_page_numbers = settings.get("print_page_numbers", False)
            page_number_pos = settings.get("page_number_pos", "Bottom Right")

            pdf_path, is_temp = self._get_effective_pdf_path()
            try:
                if mode == "Booklet":
                    pdf_bytes = imposer.impose_booklet(
                        pdf_path,
                        invert=invert,
                        print_page_numbers=print_page_numbers,
                        page_number_pos=page_number_pos,
                    )
                elif mode == "Manual Duplex":
                    pdf_bytes = imposer.impose_duplex_combined(
                        pdf_path,
                        invert=invert,
                        print_page_numbers=print_page_numbers,
                        page_number_pos=page_number_pos,
                    )
                else:
                    pdf_bytes = imposer.impose_normal(
                        pdf_path,
                        invert=invert,
                        print_page_numbers=print_page_numbers,
                        page_number_pos=page_number_pos,
                    )
            finally:
                if is_temp:
                    try:
                        os.unlink(pdf_path)
                    except OSError:
                        pass

            with open(save_path, "wb") as f:
                f.write(pdf_bytes)

            self.status_bar.showMessage(f"Exported successfully to: {os.path.basename(save_path)}")
            QMessageBox.information(
                self, "Export Complete", f"Imposed PDF successfully saved to:\n{save_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{e}")
            self.status_bar.showMessage("Export failed.")
        finally:
            if hasattr(self.settings_panel, "btn_export"):
                self.settings_panel.btn_export.setEnabled(True)
                self.settings_panel.btn_export.setText("\u2913  Export Imposed PDF...")

    # Drag and Drop Support
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith(".pdf") for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".pdf"):
                self.load_pdf(file_path)
                break


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Duplex & Booklet Studio")
    
    # Set global modern typography
    font = QFont("Inter", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)
    
    load_saved_theme(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# Module-level functions for backward compatibility with tests
def print_pdf(pdf_bytes: bytes, is_duplex: bool = False) -> None:
    """Module-level print function for test patching compatibility."""
    from src import utils
    utils.print_pdf(pdf_bytes, is_duplex)


def show_flip_prompt(parent=None) -> bool:
    """Module-level flip prompt function for test patching compatibility."""
    from src import utils
    return utils.show_flip_prompt(parent)