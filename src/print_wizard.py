"""
src/print_wizard.py - Interactive step-by-step print wizard dialog.
Guides the user through printing Pass 1 (Fronts), flipping the paper stack, and printing Pass 2 (Backs).
"""

from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFrame,
    QMessageBox,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from src import imposer
from src import utils


class PrintWizardDialog(QDialog):
    """
    Step-by-step modal wizard for manual duplex & booklet printing.
    """

    def __init__(
        self,
        pdf_path: str,
        settings: Dict,
        parent: Optional[QDialog] = None,
    ):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.settings = settings
        self.mode = settings.get("mode", "Normal")
        self.reverse_backs = settings.get("reverse_backs", False)
        self.invert = settings.get("invert_colors", False)
        self.printer = settings.get("printer")
        self.copies = settings.get("copies", 1)

        self.pass1_bytes: Optional[bytes] = None
        self.pass2_bytes: Optional[bytes] = None

        self.setWindowTitle(f"Print Wizard - {self.mode}")
        self.setFixedSize(520, 360)
        self.setModal(True)

        self._setup_ui()
        self._prepare_jobs()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Title & Step Banner
        self.lbl_title = QLabel("Printing Setup")
        self.lbl_title.setFont(QFont("sans-serif", 14, QFont.Weight.Bold))
        self.layout.addWidget(self.lbl_title)

        self.lbl_step = QLabel("Step 1 of 2")
        self.lbl_step.setObjectName("pillBadge")
        self.layout.addWidget(self.lbl_step)

        # Instruction Card Container
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background-color: #212126;
                border: 1px solid #36363d;
                border-radius: 0px;
                padding: 12px;
            }
        """)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setSpacing(10)

        self.lbl_instructions = QLabel("Preparing print streams...")
        self.lbl_instructions.setWordWrap(True)
        self.lbl_instructions.setFont(QFont("sans-serif", 11))
        self.card_layout.addWidget(self.lbl_instructions)

        self.layout.addWidget(self.card)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.layout.addWidget(self.progress_bar)

        self.layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.btn_action = QPushButton("Start Printing")
        self.btn_action.setObjectName("primaryButton")
        self.btn_action.setFixedHeight(34)
        self.btn_action.clicked.connect(self._handle_action)
        btn_layout.addWidget(self.btn_action)

        self.layout.addLayout(btn_layout)

    def _prepare_jobs(self):
        try:
            if self.mode == "Normal":
                self.pass1_bytes = imposer.impose_normal(self.pdf_path, self.invert)
                self.lbl_step.setText("Single-Sided Print")
                self.lbl_title.setText("Print Document")
                self.lbl_instructions.setText(
                    f"Ready to print document to: <b>{self.printer}</b>.<br><br>"
                    f"Click <b>Start Printing</b> to send the job to the printer."
                )
                self.btn_action.setText("Print Now")

            elif self.mode == "Manual Duplex":
                self.pass1_bytes, self.pass2_bytes = imposer.get_duplex_passes(
                    self.pdf_path, self.reverse_backs, self.invert
                )
                self._show_step_1()

            elif self.mode == "Booklet":
                self.pass1_bytes, self.pass2_bytes = imposer.get_booklet_passes(
                    self.pdf_path, self.reverse_backs, self.invert
                )
                self._show_step_1()

        except Exception as e:
            QMessageBox.critical(self, "Imposition Error", f"Failed to prepare PDF:\n{e}")
            self.reject()

    def _show_step_1(self):
        self.current_step = 1
        self.lbl_step.setText("Step 1 of 2: Front Sides")
        self.lbl_title.setText("Print Front Sides (Pass 1)")
        self.progress_bar.setValue(25)
        self.lbl_instructions.setText(
            f"<b>Pass 1 is ready:</b><br>"
            f"This will print all front-side pages to <b>{self.printer}</b>.<br><br>"
            f"Make sure your printer has blank paper, then click <b>Print Front Sides</b>."
        )
        self.btn_action.setText("Print Front Sides (Pass 1)")

    def _show_step_2(self):
        self.current_step = 2
        self.lbl_step.setText("Step 2 of 2: Flip Stack")
        self.lbl_title.setText("Flip Paper Stack")
        self.progress_bar.setValue(65)

        flip_text = self.settings.get("flip_edge", "long").capitalize()

        self.lbl_instructions.setText(
            f"<b>Front sides printed successfully!</b><br><br>"
            f"1. 📥 Take the printed paper stack from the output tray.<br>"
            f"2. 🔄 <b>Flip the entire stack</b> along the <b>{flip_text} Edge</b>.<br>"
            f"3. 📄 Reinsert the stack back into the feed tray.<br><br>"
            f"When ready, click <b>Print Back Sides</b>."
        )
        self.btn_action.setText("Print Back Sides (Pass 2)")

    def _show_step_complete(self):
        self.current_step = 3
        self.lbl_step.setText("Complete")
        self.lbl_title.setText("Print Job Sent!")
        self.progress_bar.setValue(100)
        self.lbl_instructions.setText(
            "<b>All pages have been dispatched to the printer spooler!</b><br><br>"
            "Once the second pass completes, fold your sheets along the spine."
        )
        self.btn_action.setText("Done")
        self.btn_cancel.setVisible(False)

    def _handle_action(self):
        if self.mode == "Normal":
            try:
                utils.print_pdf_bytes(self.pass1_bytes, self.printer, self.copies)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Print Error", str(e))

        elif self.current_step == 1:
            try:
                utils.print_pdf_bytes(self.pass1_bytes, self.printer, self.copies)
                self._show_step_2()
            except Exception as e:
                QMessageBox.critical(self, "Print Error", str(e))

        elif self.current_step == 2:
            try:
                utils.print_pdf_bytes(self.pass2_bytes, self.printer, self.copies)
                self._show_step_complete()
            except Exception as e:
                QMessageBox.critical(self, "Print Error", str(e))

        elif self.current_step == 3:
            self.accept()
