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
    QGroupBox, QScrollArea,
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
    open_settings_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("settingsPanel")
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget(scroll)
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 0. Document & File Section
        doc_box = QGroupBox("DOCUMENT")
        doc_layout = QVBoxLayout(doc_box)
        doc_layout.setSpacing(6)
        doc_layout.setContentsMargins(8, 16, 8, 8)

        self.btn_open_pdf = QPushButton("▤  Open PDF Document...")
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

        # Page Numbers
        self.group_page_num = QGroupBox("PAGE NUMBERS")
        page_num_layout = QVBoxLayout(self.group_page_num)
        page_num_layout.setContentsMargins(8, 16, 8, 8)
        page_num_layout.setSpacing(10)

        self.check_page_numbers = QCheckBox("Add Page Numbers to PDF")
        self.check_page_numbers.setChecked(False)
        self.check_page_numbers.stateChanged.connect(lambda: self.settings_changed.emit() if hasattr(self, "settings_changed") else self.options_changed.emit(self.get_settings()))
        page_num_layout.addWidget(self.check_page_numbers)

        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position:"))
        self.combo_page_num_pos = QComboBox()
        self.combo_page_num_pos.addItems([
            "Bottom Right", "Bottom Center", "Bottom Left",
            "Top Right", "Top Center", "Top Left"
        ])
        self.combo_page_num_pos.currentIndexChanged.connect(lambda: self.settings_changed.emit() if hasattr(self, "settings_changed") else self.options_changed.emit(self.get_settings()))
        pos_layout.addWidget(self.combo_page_num_pos)
        page_num_layout.addLayout(pos_layout)
        
        layout.addWidget(self.group_page_num)

        # 2. Printer Selection Section
        printer_box = QGroupBox("PRINTER")
        printer_layout = QVBoxLayout(printer_box)
        printer_layout.setContentsMargins(8, 16, 8, 8)
        printer_layout.setSpacing(6)

        self.combo_printer = QComboBox()
        self.combo_printer.setMinimumHeight(28)
        printer_layout.addWidget(QLabel("Destination:"))
        printer_layout.addWidget(self.combo_printer)

        layout.addWidget(printer_box)

        layout.addStretch()

        # 4. Action Buttons (Simplified)
        self.btn_open_normal = QPushButton("⧉  Open in PDF Viewer")
        self.btn_open_normal.setObjectName("primaryButton")
        self.btn_open_normal.setFixedHeight(34)
        
        self.btn_open_fronts = QPushButton("⓵  1. Open Front Pages")
        self.btn_open_fronts.setObjectName("primaryButton")
        self.btn_open_fronts.setFixedHeight(34)
        
        from src.widgets import FlipAnimationWidget
        self.anim_widget = FlipAnimationWidget("long")
        self.anim_widget.setVisible(False)
        
        self.btn_open_backs = QPushButton("⓶  2. Open Back Pages")
        self.btn_open_backs.setObjectName("primaryButton")
        self.btn_open_backs.setFixedHeight(34)
        self.btn_open_backs.setVisible(False)

        layout.addWidget(self.btn_open_normal)
        layout.addWidget(self.btn_open_fronts)
        
        anim_layout = QHBoxLayout()
        anim_layout.addStretch()
        anim_layout.addWidget(self.anim_widget)
        anim_layout.addStretch()
        layout.addLayout(anim_layout)
        
        layout.addWidget(self.btn_open_backs)

        # Hidden backward-compat combo for invert_colors (always Standard)
        self.combo_invert = QComboBox()
        self.combo_invert.addItems(["Standard", "Invert"])
        self.combo_invert.setVisible(False)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        self._on_mode_toggled()

    def _connect_signals(self):
        self.btn_open_pdf.clicked.connect(self.open_pdf_clicked)

        self.radio_normal.toggled.connect(self._on_mode_toggled)
        self.radio_duplex.toggled.connect(self._on_mode_toggled)
        self.radio_booklet.toggled.connect(self._on_mode_toggled)

    def set_document_info(self, filename: str, total_pages: int, size_str: str):
        self.lbl_doc_name.setText(filename)
        self.lbl_doc_stats.setText(f"{total_pages} pages • {size_str}")

    def _on_mode_toggled(self):
        mode = self.get_current_mode()
        
        is_duplex = mode in ("Manual Duplex", "Booklet")
        self.btn_open_normal.setVisible(not is_duplex)
        self.btn_open_fronts.setVisible(is_duplex)
        # Only show backs & animation if fronts was clicked (we will handle that externally, but reset here)
        self.anim_widget.setVisible(False)
        self.btn_open_backs.setVisible(False)
        
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
        if not hasattr(self, "check_page_numbers"):
            return {
                "mode": "Normal",
                "flip_edge": "long",
                "reverse_backs": False,
                "invert_colors": False,
                "print_page_numbers": False,
                "page_number_pos": "Bottom Right"
            }

        return {
            "mode": self.get_current_mode(),
            "flip_edge": "long",
            "reverse_backs": False,
            "invert_colors": False,
            "print_page_numbers": self.check_page_numbers.isChecked(),
            "page_number_pos": self.combo_page_num_pos.currentText(),
        }

    def set_available_printers(self, printers: List[str]):
        """Set the list of available printers in the printer combo box."""
        self.combo_printer.clear()
        if printers:
            self.combo_printer.addItems(printers)
        else:
            self.combo_printer.addItem("No printers found")