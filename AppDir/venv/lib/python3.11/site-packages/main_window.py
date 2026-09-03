# src/main_window.py
import sys
import os
import tempfile
from typing import List

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QFileDialog,
    QStatusBar,
    QMessageBox,
)
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt, QSize, QBuffer, QIODevice, QSizeF
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from src.pdf_preview import PdfPreview

from src import imposer
from src.utils import print_pdf, show_flip_prompt
from src.settings_dialog import SettingsDialog, apply_saved_theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Duplex/Booklet Printer")
        self.resize(800, 600)

        # PDF document
        self.pdf_doc = QPdfDocument(self)
        self.current_file_path = ""

        # UI setup
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        self.open_button = QPushButton("Open PDF...")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Normal", "Manual Duplex", "Booklet"])
        self.invert_button = QPushButton("Invert Pages")
        self.print_button = QPushButton("Print")
        self.settings_button = QPushButton("Settings")
        toolbar_layout.addWidget(self.open_button)
        toolbar_layout.addWidget(QLabel("Mode:"))
        toolbar_layout.addWidget(self.mode_combo)
        toolbar_layout.addWidget(self.invert_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.settings_button)
        toolbar_layout.addWidget(self.print_button)
        layout.addLayout(toolbar_layout)

        # Preview area using PdfPreview
        self.pdf_preview = PdfPreview(show_thumbnails=True)
        layout.addWidget(self.pdf_preview, stretch=1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _connect_signals(self):
        self.open_button.clicked.connect(self.open_pdf)
        self.mode_combo.currentIndexChanged.connect(self.update_preview)
        self.invert_button.clicked.connect(self.invert_selected_pages)
        self.print_button.clicked.connect(self.print_document)
        self.settings_button.clicked.connect(self.open_settings)

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            dlg.apply_theme(QApplication.instance())

    def open_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)"
        )
        if file_name:
            self.load_pdf(file_name)

    def load_pdf(self, path: str):
        self.pdf_doc.load(path)
        self.pdf_preview.setDocument(self.pdf_doc)
        self.total_pages = self.pdf_doc.pageCount()
        self.current_page = 0
        self.current_file_path = path
        self.status_bar.showMessage(f"Loaded: {os.path.basename(path)} ({self.total_pages} pages)")
        self.update_preview()

    def update_preview(self):
        mode_text = self.mode_combo.currentText()
        if mode_text == "Booklet" and self.current_file_path:
            # Show booklet imposed preview
            self._show_booklet_preview()
        else:
            # Normal preview
            self.pdf_preview.setDocument(self.pdf_doc)
            self.pdf_preview.pdf_view.update()

    def _show_booklet_preview(self):
        """Generate booklet imposed PDF and show it in preview."""
        try:
            imposed_bytes = imposer.impose_booklet(self.current_file_path)
            # Write to temp file and load into a new QPdfDocument
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(imposed_bytes)
                tmp_path = tmp.name
            booklet_doc = QPdfDocument(self)
            booklet_doc.load(tmp_path)
            self.pdf_preview.setDocument(booklet_doc)
            # Clean up temp file after the document is loaded
            # Use a single-shot timer to delete the file after a short delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self._cleanup_temp_file(tmp_path))
        except Exception as e:
            QMessageBox.warning(self, "Booklet Preview Error", f"Could not generate booklet preview: {e}")
            # Fallback to normal preview
            self.pdf_preview.setDocument(self.pdf_doc)

    def _cleanup_temp_file(self, path: str):
        """Delete a temporary file."""
        try:
            os.unlink(path)
        except OSError:
            pass  # Ignore if already deleted or inaccessible

    def invert_selected_pages(self):
        # Placeholder: invert all pages for now
        QMessageBox.information(self, "Invert", "Invert functionality not yet implemented.")
        self.status_bar.showMessage("Invert not implemented")

    def print_document(self):
        if self.total_pages == 0:
            QMessageBox.warning(self, "No PDF", "Please open a PDF first.")
            return
        mode_text = self.mode_combo.currentText()
        # Get imposed PDF bytes
        if mode_text == "Normal":
            imposed_bytes = imposer.impose_normal(self.current_file_path)
            self._print_job(imposed_bytes, is_duplex=False)
        elif mode_text == "Manual Duplex":
            imposed_bytes = imposer.impose_duplex(self.current_file_path)
            self._print_duplex_job(imposed_bytes)
        elif mode_text == "Booklet":
            imposed_bytes = imposer.impose_booklet(self.current_file_path)
            self._print_duplex_job(imposed_bytes)
        else:
            QMessageBox.warning(self, "Error", "Unknown mode")

    def _print_job(self, pdf_bytes: bytes, is_duplex: bool):
        try:
            print_pdf(pdf_bytes, is_duplex=is_duplex)
            self.status_bar.showMessage("Print job sent to printer.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))

    def _print_duplex_job(self, pdf_bytes: bytes):
        # For duplex we need to print first side, then ask to flip, then print second side.
        # Our impose_duplex and impose_booklet already produce a PDF where printing the whole
        # document once prints all front sides (in the correct order). After flipping the stack
        # and printing the same PDF again, we get the back sides.
        # So we print the PDF, prompt to flip, then print again.
        try:
            # First side
            print_pdf(pdf_bytes, is_duplex=False)  # we don't ask printer to duplex; we will flip manually
            self.status_bar.showMessage("First side printed. Please flip the stack and reinsert.")
            if not show_flip_prompt(self):
                self.status_bar.showMessage("Print job cancelled after first side.")
                return
            # Second side
            print_pdf(pdf_bytes, is_duplex=False)
            self.status_bar.showMessage("Second side printed. Job complete.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))


def main():
    app = QApplication(sys.argv)
    # Apply saved theme at startup
    apply_saved_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()