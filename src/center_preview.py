"""
src/center_preview.py - Center print preview area
Shows high-resolution preview of the exact sheet to be printed.
Features:
- Normal: single page preview
- Manual Duplex: both Front and Back side-by-side
- Booklet: all 4 pages in a 2x2 grid (Front side top, Back side bottom)
- Fixed bottom navigation bar with prev/next and zoom controls
- Per-page inversion support
"""

import math
from typing import Optional, Set
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QPen
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtPdf import QPdfDocument


class CenterPreview(QWidget):
    """
    Center viewport showing what will be physically printed on the selected sheet/side.
    Features a fixed bottom navigation bar and floating sheet info pill.
    """
    sheet_navigated = pyqtSignal(int, bool)  # sheet_idx, is_back

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("previewContainer")

        self._doc: Optional[QPdfDocument] = None
        self._mode = "Normal"
        self._current_sheet = 0
        self._current_is_back = False
        self._zoom_factor = 1.0  # 1.0 = 100%
        self._fit_mode = "page"  # "page", "width", "custom"
        self._inverted_pages: Set[int] = set()
        self._total_sheets = 0
        self._presentation_mode = False

        self._setup_ui()
        self._setup_bottom_bar()
        self._setup_floating_info()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scrollable Viewport Area filling 100% of panel
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #28282E;")

        # Content Widget inside ScrollArea
        self.viewport_widget = QWidget()
        self.viewport_layout = QVBoxLayout(self.viewport_widget)
        self.viewport_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viewport_layout.setContentsMargins(30, 30, 30, 30)

        # Paper Canvas Label
        self.paper_label = QLabel()
        self.paper_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.paper_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border-radius: 0px;
                border: 1px solid #36363D;
            }
        """)
        self.viewport_layout.addWidget(self.paper_label)

        # Empty State
        self.empty_label = QLabel("\u25a4 Open a PDF to preview print layout")
        self.empty_label.setFont(QFont("sans-serif", 13))
        self.empty_label.setStyleSheet("color: #888890; padding: 40px;")
        self.viewport_layout.addWidget(self.empty_label)

        self.scroll_area.setWidget(self.viewport_widget)
        main_layout.addWidget(self.scroll_area)

    def _setup_bottom_bar(self):
        """Fixed bottom navigation bar with prev/next + zoom controls."""
        self.bottom_bar = QWidget()
        self.bottom_bar.setObjectName("bottomBar")
        self.bottom_bar.setFixedHeight(38)

        bar_layout = QHBoxLayout(self.bottom_bar)
        bar_layout.setContentsMargins(8, 4, 8, 4)
        bar_layout.setSpacing(4)

        # Navigation: Prev / Page Info / Next
        self.btn_prev = QPushButton("\u25c0")  # ◀
        self.btn_prev.setFixedSize(30, 26)
        self.btn_prev.setToolTip("Previous Sheet")
        self.btn_prev.clicked.connect(self._go_prev_sheet)
        bar_layout.addWidget(self.btn_prev)

        self.lbl_sheet_nav = QLabel("Page 1 of 1")
        self.lbl_sheet_nav.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sheet_nav.setMinimumWidth(100)
        bar_layout.addWidget(self.lbl_sheet_nav)

        self.btn_next = QPushButton("\u25b6")  # ▶
        self.btn_next.setFixedSize(30, 26)
        self.btn_next.setToolTip("Next Sheet")
        self.btn_next.clicked.connect(self._go_next_sheet)
        bar_layout.addWidget(self.btn_next)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #36363D;")
        bar_layout.addWidget(sep)

        # Zoom: Out / Level / In
        self.btn_zoom_out = QPushButton("\u2296")  # ⊖
        self.btn_zoom_out.setFixedSize(30, 26)
        self.btn_zoom_out.setToolTip("Zoom Out")
        self.btn_zoom_out.clicked.connect(self._zoom_out)
        bar_layout.addWidget(self.btn_zoom_out)

        self.lbl_zoom = QLabel("Fit")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setFixedWidth(42)
        bar_layout.addWidget(self.lbl_zoom)

        self.btn_zoom_in = QPushButton("\u2295")  # ⊕
        self.btn_zoom_in.setFixedSize(30, 26)
        self.btn_zoom_in.setToolTip("Zoom In")
        self.btn_zoom_in.clicked.connect(self._zoom_in)
        bar_layout.addWidget(self.btn_zoom_in)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #36363D;")
        bar_layout.addWidget(sep2)

        # Fit controls
        self.btn_fit_page = QPushButton("\u2922")  # ⤢
        self.btn_fit_page.setFixedSize(30, 26)
        self.btn_fit_page.setToolTip("Fit Page")
        self.btn_fit_page.clicked.connect(self._fit_page)
        bar_layout.addWidget(self.btn_fit_page)

        self.btn_fit_width = QPushButton("\u2194")  # ↔
        self.btn_fit_width.setFixedSize(30, 26)
        self.btn_fit_width.setToolTip("Fit Width")
        self.btn_fit_width.clicked.connect(self._fit_width)
        bar_layout.addWidget(self.btn_fit_width)

        bar_layout.addStretch()

        # Add bottom bar to main layout
        self.layout().addWidget(self.bottom_bar)

    def _setup_floating_info(self):
        """Floating Sheet Info Badge (Top-Left overlay)."""
        self.floating_info_pill = QLabel("No Document Loaded", self)
        self.floating_info_pill.setObjectName("pillBadge")
        self.floating_info_pill.setFont(QFont("sans-serif", 11, QFont.Weight.DemiBold))
        self.floating_info_pill.setStyleSheet("""
            QLabel {
                background-color: #212126f0;
                color: #E64B3D;
                border: 1px solid #36363D;
                border-radius: 0px;
                padding: 6px 14px;
            }
        """)
        self.floating_info_pill.adjustSize()
        self.floating_info_pill.raise_()

        # Backward compatibility aliases
        self.info_banner = self.floating_info_pill
        self.pass_tag = QLabel(self)
        self.pass_tag.setVisible(False)

        # Keep reference to old floating_zoom_bar for compat (hidden)
        self.floating_zoom_bar = QWidget(self)
        self.floating_zoom_bar.setVisible(False)

    # ── Public API ──

    def set_document(self, doc: Optional[QPdfDocument]):
        self._doc = doc
        self._current_sheet = 0
        self._current_is_back = False
        self.update_preview()

    def set_mode(self, mode: str):
        self._mode = mode
        self._current_sheet = 0
        self._current_is_back = False
        self.update_preview()

    def set_presentation_mode(self, enabled: bool):
        if self._presentation_mode != enabled:
            self._presentation_mode = enabled
            self.update_preview()

    def set_sheet(self, sheet_idx: int, is_back: bool):
        self._current_sheet = sheet_idx
        self._current_is_back = is_back
        self.update_preview()

    def set_inverted_pages(self, pages: Set[int]):
        self._inverted_pages = set(pages)
        self.update_preview()

    # ── Navigation ──

    def _go_prev_sheet(self):
        if self._current_sheet > 0:
            self._current_sheet -= 1
            self.update_preview()
            self.sheet_navigated.emit(self._current_sheet, False)

    def _go_next_sheet(self):
        if self._current_sheet < self._total_sheets - 1:
            self._current_sheet += 1
            self.update_preview()
            self.sheet_navigated.emit(self._current_sheet, False)

    # ── Zoom ──

    def _zoom_in(self):
        self._fit_mode = "custom"
        self._zoom_factor = min(self._zoom_factor * 1.25, 4.0)
        self.lbl_zoom.setText(f"{int(self._zoom_factor * 100)}%")
        self.update_preview()

    def _zoom_out(self):
        self._fit_mode = "custom"
        self._zoom_factor = max(self._zoom_factor / 1.25, 0.25)
        self.lbl_zoom.setText(f"{int(self._zoom_factor * 100)}%")
        self.update_preview()

    def _fit_page(self):
        self._fit_mode = "page"
        self._zoom_factor = 1.0
        self.lbl_zoom.setText("Fit")
        self.update_preview()

    def _fit_width(self):
        self._fit_mode = "width"
        self._zoom_factor = 1.0
        self.lbl_zoom.setText("Fit W")
        self.update_preview()

    # ── Events ──

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import Qt
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._panning = True
                self._last_mouse_pos = event.globalPosition().toPoint()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                return True
        elif event.type() == QEvent.Type.MouseMove:
            if getattr(self, '_panning', False) and self._last_mouse_pos:
                delta = event.globalPosition().toPoint() - self._last_mouse_pos
                self._last_mouse_pos = event.globalPosition().toPoint()
                
                h_bar = self.scroll_area.horizontalScrollBar()
                v_bar = self.scroll_area.verticalScrollBar()
                
                h_bar.setValue(h_bar.value() - delta.x())
                v_bar.setValue(v_bar.value() - delta.y())
                return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton and getattr(self, '_panning', False):
                self._panning = False
                self.unsetCursor()
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_floating_widgets()
        if self._fit_mode in ("page", "width"):
            self.update_preview()
            
    def wheelEvent(self, event):
        """Handle Ctrl+Scroll for zooming."""
        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.ControlModifier or mods & Qt.KeyboardModifier.MetaModifier:
            # Scroll up -> zoom in, Scroll down -> zoom out
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def _reposition_floating_widgets(self):
        # Position Floating Info Pill at top left
        self.floating_info_pill.adjustSize()
        pw = self.floating_info_pill.width()
        ph = self.floating_info_pill.height()
        self.floating_info_pill.setGeometry(16, 16, pw, ph)
        self.floating_info_pill.raise_()

    # ── Update Navigation Label & Buttons ──

    def _update_nav_controls(self):
        if self._mode == "Normal":
            label = f"Page {self._current_sheet + 1} of {self._total_sheets}"
        else:
            label = f"Sheet {self._current_sheet + 1} of {self._total_sheets}"
        self.lbl_sheet_nav.setText(label)
        self.btn_prev.setEnabled(self._current_sheet > 0)
        self.btn_next.setEnabled(self._current_sheet < self._total_sheets - 1)

    # ── Rendering ──

    def update_preview(self):
        if not self._doc or self._doc.pageCount() == 0:
            self.empty_label.setVisible(True)
            self.paper_label.setVisible(False)
            self.floating_info_pill.setText("No Document Loaded")
            self._total_sheets = 0
            self._update_nav_controls()
            self._reposition_floating_widgets()
            return

        self.empty_label.setVisible(False)
        self.paper_label.setVisible(True)

        page_count = self._doc.pageCount()
        viewport_w = max(self.scroll_area.viewport().width() - 60, 200)
        viewport_h = max(self.scroll_area.viewport().height() - 60, 200)

        if self._mode == "Normal":
            self._total_sheets = page_count
            pg = min(self._current_sheet, page_count - 1)
            self._current_sheet = pg
            self.floating_info_pill.setText(
                f"Page {pg + 1} of {page_count} \u2022 1-Up"
            )
            self._render_normal_sheet(pg, viewport_w, viewport_h)

        elif self._mode == "Manual Duplex":
            sheets = math.ceil(page_count / 2)
            self._total_sheets = sheets
            s = min(self._current_sheet, sheets - 1)
            self._current_sheet = s

            f_pg = s * 2
            b_pg = s * 2 + 1

            f_str = f"P{f_pg + 1}" if f_pg < page_count else "Blank"
            b_str = f"P{b_pg + 1}" if b_pg < page_count else "Blank"

            self.floating_info_pill.setText(
                f"Sheet {s + 1} of {sheets} \u2022 [Front: {f_str} | Back: {b_str}]"
            )
            self._render_duplex_sheet(
                f_pg if f_pg < page_count else None,
                b_pg if b_pg < page_count else None,
                viewport_w,
                viewport_h,
            )

        elif self._mode == "Booklet":
            sheets = math.ceil(page_count / 4)
            self._total_sheets = sheets
            s = min(self._current_sheet, sheets - 1)
            self._current_sheet = s
            total_booklet_pages = sheets * 4

            lf = total_booklet_pages - 1 - 2 * s
            rf = 2 * s
            lb = 2 * s + 1
            rb = total_booklet_pages - 2 - 2 * s

            def pg_str(p):
                return f"P{p + 1}" if p < page_count else "--"

            if self._presentation_mode:
                self.floating_info_pill.setText(
                    f"Sheet {s + 1} of {sheets} • Pres. Booklet • "
                    f"Front: [Top: {pg_str(lf)} | Bot: {pg_str(rf)}]  "
                    f"Back: [Top: {pg_str(lb)} | Bot: {pg_str(rb)}]"
                )
                self._render_presentation_booklet_sheet(
                    lf if lf < page_count else None,
                    rf if rf < page_count else None,
                    lb if lb < page_count else None,
                    rb if rb < page_count else None,
                    viewport_w,
                    viewport_h,
                )
            else:
                self.floating_info_pill.setText(
                    f"Sheet {s + 1} of {sheets} \u2022 "
                    f"Front: [{pg_str(lf)}|{pg_str(rf)}]  "
                    f"Back: [{pg_str(lb)}|{pg_str(rb)}]"
                )
                self._render_booklet_full_sheet(
                    lf if lf < page_count else None,
                    rf if rf < page_count else None,
                    lb if lb < page_count else None,
                    rb if rb < page_count else None,
                    viewport_w,
                    viewport_h,
                )

        self._update_nav_controls()
        self._reposition_floating_widgets()

    def _render_page_image(self, page_idx: int, width: int, height: int) -> QImage:
        """Render a page at the given size, applying inversion if needed.
        Always fills white paper background before rendering."""
        img = self._doc.render(page_idx, QSize(width, height))
        if page_idx in self._inverted_pages:
            img.invertPixels(QImage.InvertMode.InvertRgb)
        return img

    def _render_normal_sheet(self, page_idx: int, max_w: int, max_h: int):
        """Render a single portrait or landscape page scaled to viewport."""
        doc_page_size = self._doc.pagePointSize(page_idx)
        pw, ph = doc_page_size.width(), doc_page_size.height()
        if pw <= 0 or ph <= 0:
            pw, ph = 595, 842

        # Compute display size based on fit_mode or zoom
        if self._fit_mode == "page":
            scale = min(max_w / pw, max_h / ph)
        elif self._fit_mode == "width":
            scale = max_w / pw
        else:
            scale = min(max_w / pw, max_h / ph) * self._zoom_factor

        target_w = int(pw * scale)
        target_h = int(ph * scale)

        # Create composite with white paper background
        composite = QPixmap(target_w, target_h)
        composite.fill(QColor("#ffffff"))

        painter = QPainter(composite)
        img = self._render_page_image(page_idx, target_w, target_h)

        if page_idx in self._inverted_pages:
            # Fill black for inverted pages
            painter.fillRect(0, 0, target_w, target_h, QColor("#000000"))

        painter.drawImage(0, 0, img)
        painter.end()

        self.paper_label.setPixmap(composite)
        self.paper_label.setFixedSize(target_w, target_h)

    def _render_blank_page(
        self, painter: QPainter, x: int, y: int, w: int, h: int, text: str = "[ Blank ]"
    ):
        """Draw a blank page placeholder at the given position."""
        painter.fillRect(x, y, w, h, QColor("#ffffff"))
        painter.setPen(QColor("#d4d4d8"))
        painter.drawRect(x, y, w - 1, h - 1)
        painter.setPen(QColor("#a1a1aa"))
        painter.setFont(QFont("sans-serif", 11))
        painter.drawText(x, y, w, h, Qt.AlignmentFlag.AlignCenter, text)

    def _render_page_in_composite(
        self,
        painter: QPainter,
        page_idx: Optional[int],
        x: int,
        y: int,
        w: int,
        h: int,
    ):
        """Render a page (or blank placeholder) into a composite at given position."""
        if page_idx is not None and 0 <= page_idx < self._doc.pageCount():
            # White paper background
            if page_idx in self._inverted_pages:
                painter.fillRect(x, y, w, h, QColor("#000000"))
            else:
                painter.fillRect(x, y, w, h, QColor("#ffffff"))

            img = self._render_page_image(page_idx, w, h)
            painter.drawImage(x, y, img)

            # Paper border
            painter.setPen(QColor("#d4d4d8"))
            painter.drawRect(x, y, w - 1, h - 1)
        else:
            self._render_blank_page(painter, x, y, w, h)

    def _render_duplex_sheet(
        self,
        front_page: Optional[int],
        back_page: Optional[int],
        max_w: int,
        max_h: int,
    ):
        """Render Front and Back pages side-by-side on a single composite canvas."""
        # Use landscape-ish aspect ratio (2:1.4)
        sheet_w = 842
        sheet_h = 595

        if self._fit_mode == "page":
            scale = min(max_w / sheet_w, max_h / sheet_h)
        elif self._fit_mode == "width":
            scale = max_w / sheet_w
        else:
            scale = min(max_w / sheet_w, max_h / sheet_h) * self._zoom_factor

        target_w = int(sheet_w * scale)
        target_h = int(sheet_h * scale)

        composite = QPixmap(target_w, target_h)
        composite.fill(QColor("#28282E"))

        painter = QPainter(composite)
        half_w = target_w // 2
        page_margin = 6
        label_h = 18

        # "FRONT" label
        painter.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        painter.setPen(QColor("#E64B3D"))
        painter.drawText(page_margin, 14, "FRONT")

        # "BACK" label
        painter.setPen(QColor("#888890"))
        painter.drawText(half_w + page_margin, 14, "BACK")

        page_y = label_h + 4
        page_h = target_h - page_y - page_margin

        # Render Front page (left half)
        self._render_page_in_composite(
            painter, front_page,
            page_margin, page_y,
            half_w - page_margin * 2, page_h,
        )

        # Center divider
        pen = QPen(QColor("#36363D"))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(half_w, page_margin, half_w, target_h - page_margin)

        # Render Back page (right half)
        self._render_page_in_composite(
            painter, back_page,
            half_w + page_margin, page_y,
            half_w - page_margin * 2, page_h,
        )

        painter.end()

        self.paper_label.setPixmap(composite)
        self.paper_label.setFixedSize(target_w, target_h)

    def _render_booklet_full_sheet(
        self,
        lf: Optional[int],
        rf: Optional[int],
        lb: Optional[int],
        rb: Optional[int],
        max_w: int,
        max_h: int,
    ):
        """Render all 4 booklet pages in a 2x2 grid.
        Top row: Front side [LF | RF] with spine fold
        Bottom row: Back side [LB | RB] with spine fold
        Horizontal divider between rows."""
        # Get actual page size for exact aspect ratio scaling
        page_size = self._doc.pagePointSize(0) if self._doc.pageCount() > 0 else None
        if page_size and page_size.width() > 0 and page_size.height() > 0:
            pw, ph = page_size.width(), page_size.height()
            sheet_w = pw * 2
            sheet_h = ph * 2
        else:
            sheet_w = 842
            sheet_h = 1190  # 595 * 2

        if self._fit_mode == "page":
            scale = min(max_w / sheet_w, max_h / sheet_h)
        elif self._fit_mode == "width":
            scale = max_w / sheet_w
        else:
            scale = min(max_w / sheet_w, max_h / sheet_h) * self._zoom_factor

        target_w = int(sheet_w * scale)
        target_h = int(sheet_h * scale)

        composite = QPixmap(target_w, target_h)
        composite.fill(QColor("#28282E"))

        painter = QPainter(composite)
        half_w = target_w // 2
        half_h = target_h // 2
        margin = 6
        label_h = 18

        # ── TOP ROW: FRONT SIDE ──
        painter.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        painter.setPen(QColor("#E64B3D"))
        painter.drawText(margin, 14, "FRONT SIDE")

        page_y_top = label_h + 4
        page_h_top = half_h - page_y_top - margin

        # Left Front
        self._render_page_in_composite(
            painter, lf,
            margin, page_y_top,
            half_w - margin * 2, page_h_top,
        )

        # Spine fold line (front)
        pen = QPen(QColor("#E64B3D"))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(half_w, page_y_top, half_w, page_y_top + page_h_top)

        # Right Front
        self._render_page_in_composite(
            painter, rf,
            half_w + margin, page_y_top,
            half_w - margin * 2, page_h_top,
        )

        # ── HORIZONTAL FLIP DIVIDER ──
        painter.setPen(QPen(QColor("#888890"), 1, Qt.PenStyle.DashDotLine))
        painter.drawLine(margin, half_h, target_w - margin, half_h)
        painter.setFont(QFont("sans-serif", 8))
        painter.setPen(QColor("#888890"))
        flip_text = "\u2191 flip \u2193"
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(flip_text)
        painter.fillRect(
            (target_w - tw) // 2 - 4, half_h - 8, tw + 8, 16,
            QColor("#28282E"),
        )
        painter.drawText(
            (target_w - tw) // 2, half_h + 4, flip_text,
        )

        # ── BOTTOM ROW: BACK SIDE ──
        painter.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        painter.setPen(QColor("#888890"))
        painter.drawText(margin, half_h + 14, "BACK SIDE")

        page_y_bot = half_h + label_h + 4
        page_h_bot = target_h - page_y_bot - margin

        # Left Back
        self._render_page_in_composite(
            painter, lb,
            margin, page_y_bot,
            half_w - margin * 2, page_h_bot,
        )

        # Spine fold line (back)
        painter.setPen(pen)
        painter.drawLine(half_w, page_y_bot, half_w, page_y_bot + page_h_bot)

        # Right Back
        self._render_page_in_composite(
            painter, rb,
            half_w + margin, page_y_bot,
            half_w - margin * 2, page_h_bot,
        )

        painter.end()

        self.paper_label.setPixmap(composite)
        self.paper_label.setFixedSize(target_w, target_h)

    def _render_presentation_booklet_sheet(
        self,
        lf: Optional[int],
        rf: Optional[int],
        lb: Optional[int],
        rb: Optional[int],
        max_w: int,
        max_h: int,
    ):
        """Render presentation booklet sheets (Front and Back) side by side.
        Left half: FRONT SIDE with Top slide (LF) and Bottom slide (RF).
        Right half: BACK SIDE with Top slide (LB) and Bottom slide (RB).
        Each side is a Portrait sheet with horizontal spine fold across the middle.
        """
        page_size = self._doc.pagePointSize(0) if self._doc.pageCount() > 0 else None
        if page_size and page_size.width() > 0 and page_size.height() > 0:
            pw, ph = page_size.width(), page_size.height()
            single_w = pw
            single_h = max(pw * 1.4142, ph * 2.0) if pw >= ph else ph * 2.0
        else:
            single_w = 595
            single_h = 842

        # Two portrait sheets side-by-side
        canvas_w = single_w * 2
        canvas_h = single_h

        if self._fit_mode == "page":
            scale = min(max_w / canvas_w, max_h / canvas_h)
        elif self._fit_mode == "width":
            scale = max_w / canvas_w
        else:
            scale = min(max_w / canvas_w, max_h / canvas_h) * self._zoom_factor

        target_w = int(canvas_w * scale)
        target_h = int(canvas_h * scale)

        composite = QPixmap(target_w, target_h)
        composite.fill(QColor("#28282E"))

        painter = QPainter(composite)
        half_w = target_w // 2
        half_h = target_h // 2
        margin = 6
        label_h = 18

        # ── LEFT HALF: FRONT SIDE (Portrait: Top LF / Bottom RF) ──
        painter.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        painter.setPen(QColor("#E64B3D"))
        painter.drawText(margin, 14, "FRONT SIDE (T/B)")

        page_y_top = label_h + 4
        page_h_slot = half_h - page_y_top - margin

        # Top Front (LF)
        self._render_page_in_composite(
            painter, lf,
            margin, page_y_top,
            half_w - margin * 2, page_h_slot,
        )

        # Horizontal spine fold line (Front)
        pen = QPen(QColor("#E64B3D"))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(margin, half_h, half_w - margin, half_h)

        # Bottom Front (RF)
        page_y_bot = half_h + label_h + 4
        page_h_bot = target_h - page_y_bot - margin
        self._render_page_in_composite(
            painter, rf,
            margin, page_y_bot,
            half_w - margin * 2, page_h_bot,
        )

        # ── VERTICAL DIVIDER BETWEEN FRONT AND BACK SHEETS ──
        pen_div = QPen(QColor("#888890"), 1, Qt.PenStyle.DashDotLine)
        painter.setPen(pen_div)
        painter.drawLine(half_w, margin, half_w, target_h - margin)

        # ── RIGHT HALF: BACK SIDE (Portrait: Top LB / Bottom RB) ──
        painter.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        painter.setPen(QColor("#888890"))
        painter.drawText(half_w + margin, 14, "BACK SIDE (T/B)")

        # Top Back (LB)
        self._render_page_in_composite(
            painter, lb,
            half_w + margin, page_y_top,
            half_w - margin * 2, page_h_slot,
        )

        # Horizontal spine fold line (Back)
        painter.setPen(pen)
        painter.drawLine(half_w + margin, half_h, target_w - margin, half_h)

        # Bottom Back (RB)
        self._render_page_in_composite(
            painter, rb,
            half_w + margin, page_y_bot,
            half_w - margin * 2, page_h_bot,
        )

        painter.end()

        self.paper_label.setPixmap(composite)
        self.paper_label.setFixedSize(target_w, target_h)

    def _render_blank_sheet(self, max_w: int, max_h: int):
        target_w = int(max_w * 0.7)
        target_h = int(max_h * 0.9)
        pix = QPixmap(target_w, target_h)
        pix.fill(QColor("#ffffff"))

        painter = QPainter(pix)
        painter.setPen(QColor("#a1a1aa"))
        painter.setFont(QFont("sans-serif", 14))
        painter.drawText(
            pix.rect(), Qt.AlignmentFlag.AlignCenter, "[ Blank Page ]"
        )
        painter.end()

        self.paper_label.setPixmap(pix)
        self.paper_label.setFixedSize(target_w, target_h)
