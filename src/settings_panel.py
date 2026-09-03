"""
src/settings_panel.py - Right-side inspector and control panel.
Houses PDF document loader/details, mode selection, duplex/booklet options, printer destination, and actions.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QPushButton,
    QGroupBox,
    QFrame,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal


class SettingsPanel(QWidget):
    """Right-hand inspector panel containing all print, document, and imposition controls."""
    open_pdf_clicked = pyqtSignal()
    mode_changed = pyqtSignal(str)
    options_changed = pyqtSignal(dict)
    print_clicked = pyqtSignal()
    export_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("settingsPanel")
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 0. Document & File Section
        doc_box = QGroupBox("DOCUMENT")
        doc_layout = QVBoxLayout(doc_box)
        doc_layout.setSpacing(6)
        doc_layout.setContentsMargins(8, 16, 8, 8)

        self.btn_open_pdf = QPushButton("\u25a4  Open PDF Document...")
        self.btn_open_pdf.setObjectName("primaryButton")
        self.btn_open_pdf.setFixedHeight(32)
        doc_layout.addWidget(self.btn_open_pdf)

        self.lbl_doc_name = QLabel("No document opened")
        self.lbl_doc_name.setWordWrap(True)
        self.lbl_doc_name.setFont(QFont("sans-serif", 11, QFont.Weight.Bold))
        doc_layout.addWidget(self.lbl_doc_name)

        self.lbl_doc_stats = QLabel("Drop a PDF anywhere or click Open")
        self.lbl_doc_stats.setObjectName("metaLabel")
        doc_layout.addWidget(self.lbl_doc_stats)

        layout.addWidget(doc_box)

        # 1. Print Mode Section
        mode_box = QGroupBox("PRINT MODE")
        mode_layout = QVBoxLayout(mode_box)
        mode_layout.setSpacing(4)
        mode_layout.setContentsMargins(8, 16, 8, 8)

        self.btn_group_mode = QButtonGroup(self)
        self.radio_normal = QRadioButton("Normal (1-Up Single-Sided)")
        self.radio_duplex = QRadioButton("Manual Duplex (2-Sided)")
        self.radio_booklet = QRadioButton("Booklet (Folded 2-Up)")
        self.radio_normal.setChecked(True)

        self.btn_group_mode.addButton(self.radio_normal, 0)
        self.btn_group_mode.addButton(self.radio_duplex, 1)
        self.btn_group_mode.addButton(self.radio_booklet, 2)

        mode_layout.addWidget(self.radio_normal)
        mode_layout.addWidget(self.radio_duplex)
        mode_layout.addWidget(self.radio_booklet)
        layout.addWidget(mode_box)

        # 2. Duplex / Booklet Options Section
        self.duplex_box = QGroupBox("DUPLEX & BINDING")
        duplex_layout = QVBoxLayout(self.duplex_box)
        duplex_layout.setSpacing(6)
        duplex_layout.setContentsMargins(8, 16, 8, 8)

        self.combo_flip = QComboBox()
        self.combo_flip.addItems(["Long-Edge (Standard Book)", "Short-Edge (Calendar / Pad)"])
        duplex_layout.addWidget(self.combo_flip)

        self.chk_reverse_backs = QCheckBox("Reverse Back Pages (Pass 2)")
        self.chk_reverse_backs.setToolTip(
            "Enable if your printer ejects pages face-up, so they end up in reverse order."
        )
        duplex_layout.addWidget(self.chk_reverse_backs)

        layout.addWidget(self.duplex_box)

        # 3. Printer & Output Section
        printer_box = QGroupBox("PRINTER")
        printer_layout = QVBoxLayout(printer_box)
        printer_layout.setSpacing(6)
        printer_layout.setContentsMargins(8, 16, 8, 8)

        self.combo_printer = QComboBox()
        self.combo_printer.addItem("Default System Printer")
        self.combo_printer.addItem("Save as PDF File")
        printer_layout.addWidget(self.combo_printer)

        self.combo_paper = QComboBox()
        self.combo_paper.addItems(["Auto (Match Document)", "A4 (210 x 297 mm)", "US Letter (8.5 x 11 in)"])
        printer_layout.addWidget(self.combo_paper)

        copies_layout = QHBoxLayout()
        copies_label = QLabel("Copies:")
        copies_label.setObjectName("metaLabel")
        copies_layout.addWidget(copies_label)
        self.spin_copies = QSpinBox()
        self.spin_copies.setRange(1, 99)
        self.spin_copies.setValue(1)
        copies_layout.addWidget(self.spin_copies)
        printer_layout.addLayout(copies_layout)

        layout.addWidget(printer_box)

        layout.addStretch()

        # 4. Action Buttons
        self.btn_print = QPushButton("\u2399  Print Document")
        self.btn_print.setObjectName("primaryButton")
        self.btn_print.setFixedHeight(34)

        self.btn_export = QPushButton("\u2913  Export Imposed PDF...")
        self.btn_export.setObjectName("secondaryButton")
        self.btn_export.setFixedHeight(30)

        layout.addWidget(self.btn_print)
        layout.addWidget(self.btn_export)

        # Hidden backward-compat combo for invert_colors (always Standard)
        self.combo_invert = QComboBox()
        self.combo_invert.addItems(["Standard (Original Colors)", "Invert Colors (Dark Mode / Negative)"])
        self.combo_invert.setVisible(False)

        self._on_mode_toggled()

    def _connect_signals(self):
        self.btn_open_pdf.clicked.connect(self.open_pdf_clicked)

        self.radio_normal.toggled.connect(self._on_mode_toggled)
        self.radio_duplex.toggled.connect(self._on_mode_toggled)
        self.radio_booklet.toggled.connect(self._on_mode_toggled)

        self.combo_flip.currentIndexChanged.connect(self._emit_options)
        self.chk_reverse_backs.toggled.connect(self._emit_options)
        self.combo_paper.currentIndexChanged.connect(self._emit_options)
        self.spin_copies.valueChanged.connect(self._emit_options)

        self.btn_print.clicked.connect(self.print_clicked)
        self.btn_export.clicked.connect(self.export_clicked)

    def set_document_info(self, filename: str, total_pages: int, size_str: str):
        self.lbl_doc_name.setText(filename)
        self.lbl_doc_stats.setText(f"{total_pages} pages \u2022 {size_str}")

    def _on_mode_toggled(self):
        mode = self.get_current_mode()
        self.duplex_box.setVisible(mode in ("Manual Duplex", "Booklet"))
        self.mode_changed.emit(mode)
        self._emit_options()

    def _emit_options(self):
        self.options_changed.emit(self.get_settings())

    def get_current_mode(self) -> str:
        if self.radio_duplex.isChecked():
            return "Manual Duplex"
        elif self.radio_booklet.isChecked():
            return "Booklet"
        return "Normal"

    def set_current_mode(self, mode: str):
        if mode == "Manual Duplex":
            self.radio_duplex.setChecked(True)
        elif mode == "Booklet":
            self.radio_booklet.setChecked(True)
        else:
            self.radio_normal.setChecked(True)

    def get_settings(self) -> dict:
        return {
            "mode": self.get_current_mode(),
            "flip_edge": "short" if "Short" in self.combo_flip.currentText() else "long",
            "reverse_backs": self.chk_reverse_backs.isChecked(),
            "invert_colors": False,
            "printer": self.combo_printer.currentText(),
            "paper_size": self.combo_paper.currentText(),
            "copies": self.spin_copies.value(),
        }

    def set_available_printers(self, printers: List[str]):
        current = self.combo_printer.currentText()
        self.combo_printer.clear()
        self.combo_printer.addItem("Default System Printer")
        for p in printers:
            self.combo_printer.addItem(p)
        self.combo_printer.addItem("Save as PDF File")

        idx = self.combo_printer.findText(current)
        if idx >= 0:
            self.combo_printer.setCurrentIndex(idx)
