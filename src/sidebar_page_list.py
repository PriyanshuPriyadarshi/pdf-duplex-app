"""
src/sidebar_page_list.py - Mode-reactive left sidebar thumbnail list.
Shows:
- Normal Mode: 1 page per card.
- Duplex Mode: 2 pages side-by-side [Front | Back] per card.
- Booklet Mode: 4 pages (2 on Front, 2 on Back) arranged like a real-world printed sheet signature.

Features multi-selection (click, Shift+Click, Ctrl+Click), per-page inversion with
visual indicator badges, page number watermarks, and a pinned bottom action bar.
"""

from typing import List, Optional, Set
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QImage
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtPdf import QPdfDocument


class ThumbnailCard(QFrame):
    """Interactive card displaying a physical sheet thumbnail and metadata."""
    clicked_with_modifiers = pyqtSignal(int, bool, bool, bool)  # index, is_back, shift, ctrl

    def __init__(
        self,
        sheet_idx: int,
        is_back: bool,
        title: str,
        subtitle: str,
        page_numbers: str,
        pixmap: Optional[QPixmap] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.sheet_idx = sheet_idx
        self.is_back = is_back
        self.is_selected = False
        self._is_inverted = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._setup_ui(title, subtitle, page_numbers, pixmap)
        self.update_style()

    def _setup_ui(self, title: str, subtitle: str, page_numbers: str, pixmap: Optional[QPixmap]):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Header with Title + Invert Badge + Pill Tag
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)

        # Invert status badge
        self.invert_badge = QLabel("\u25cb")  # ○
        self.invert_badge.setFixedWidth(18)
        self.invert_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.invert_badge.setStyleSheet("color: #636363; font-size: 12px;")
        self.invert_badge.setToolTip("Original colors")
        header_layout.addWidget(self.invert_badge)

        header_layout.addStretch()

        self.tag_label = QLabel(subtitle)
        self.tag_label.setObjectName("pillBadge")
        header_layout.addWidget(self.tag_label)

        layout.addLayout(header_layout)

        # Thumbnail Container
        self.thumb_label = QLabel()
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet(
            "background-color: #212126; border-radius: 0px; border: 1px solid #36363d;"
        )

        if pixmap and not pixmap.isNull():
            self.thumb_label.setPixmap(pixmap)
            self.thumb_label.setFixedHeight(pixmap.height() + 8)
        else:
            self.thumb_label.setText("No Preview")
            self.thumb_label.setFixedHeight(110)

        layout.addWidget(self.thumb_label)

        # Page number info label
        self.page_info_label = QLabel(page_numbers)
        self.page_info_label.setStyleSheet("color: #636363; font-size: 10px;")
        layout.addWidget(self.page_info_label)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()

    def set_inverted(self, inverted: bool):
        self._is_inverted = inverted
        if inverted:
            self.invert_badge.setText("\u25d0")  # ◐
            self.invert_badge.setStyleSheet(
                "color: #10b981; font-size: 14px; font-weight: bold;"
            )
            self.invert_badge.setToolTip("Inverted (Ink Saver)")
        else:
            self.invert_badge.setText("\u25cb")  # ○
            self.invert_badge.setStyleSheet("color: #636363; font-size: 12px;")
            self.invert_badge.setToolTip("Original colors")

    @property
    def is_inverted(self) -> bool:
        return self._is_inverted

    def update_thumbnail(self, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            self.thumb_label.setPixmap(pixmap)
            self.thumb_label.setFixedHeight(pixmap.height() + 8)

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #382424;
                    border: 2px solid #E64B3D;
                    border-radius: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #212126;
                    border: 1px solid #36363d;
                    border-radius: 0px;
                }
                QFrame:hover {
                    background-color: #28282E;
                    border: 1px solid #636363;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            mods = event.modifiers()
            shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
            ctrl = bool(
                mods & Qt.KeyboardModifier.ControlModifier
                or mods & Qt.KeyboardModifier.MetaModifier
            )
            self.clicked_with_modifiers.emit(self.sheet_idx, self.is_back, shift, ctrl)
        super().mousePressEvent(event)


class SidebarPageList(QWidget):
    """
    Left sidebar showing a vertically scrollable list of sheets/pages.
    - Normal: 1 page per card.
    - Manual Duplex: 2 pages side-by-side per sheet [Front | Back].
    - Booklet: 4 pages (2 Front + 2 Back) per sheet.

    Supports multi-selection, per-page inversion, and page number watermarks.
    """
    card_selected = pyqtSignal(int, bool)  # sheet_idx, is_back
    inversion_changed = pyqtSignal(set)  # set of inverted 0-based page indices

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("sidebarPanel")
        self.setMinimumWidth(230)

        self._doc: Optional[QPdfDocument] = None
        self._mode = "Normal"  # Normal, Manual Duplex, Booklet
        self._cards: List[ThumbnailCard] = []
        self._selected_indices: List[int] = []  # indices into self._cards
        self._last_clicked_index: int = -1
        self._inverted_pages: Set[int] = set()  # 0-based PDF page indices

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 6)
        main_layout.setSpacing(6)

        # Header
        header_layout = QHBoxLayout()
        header_title = QLabel("SHEETS & PAGES")
        header_title.setObjectName("sectionTitle")
        header_layout.addWidget(header_title)

        header_layout.addStretch()

        self.count_badge = QLabel("0 Pages")
        self.count_badge.setObjectName("pillBadge")
        header_layout.addWidget(self.count_badge)

        main_layout.addLayout(header_layout)

        # Scroll Area for Cards
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 4, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll_area)

        # ── Bottom Action Bar (pinned below scroll area) ──
        self.bottom_bar = QWidget()
        self.bottom_bar.setObjectName("bottomBar")
        bar_layout = QVBoxLayout(self.bottom_bar)
        bar_layout.setContentsMargins(0, 6, 0, 0)
        bar_layout.setSpacing(4)

        # Row 1: Select All + selection count
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.btn_select_all = QPushButton("\u2611 Select All")
        self.btn_select_all.setFixedHeight(26)
        self.btn_select_all.clicked.connect(self._toggle_select_all)
        row1.addWidget(self.btn_select_all)

        self.lbl_selection_count = QLabel("0 selected")
        self.lbl_selection_count.setObjectName("metaLabel")
        row1.addWidget(self.lbl_selection_count)
        row1.addStretch()

        bar_layout.addLayout(row1)

        # Row 2: Invert / Ink Saver button
        self.btn_invert = QPushButton("\u25d0  Invert / Ink Saver")
        self.btn_invert.setObjectName("secondaryButton")
        self.btn_invert.setFixedHeight(30)
        self.btn_invert.clicked.connect(self._toggle_invert_selected)
        bar_layout.addWidget(self.btn_invert)

        main_layout.addWidget(self.bottom_bar)
        
        # Enable keyboard focus for shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts (Ctrl+A for Select All, Ctrl+I for Invert)."""
        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.ControlModifier or mods & Qt.KeyboardModifier.MetaModifier:
            if event.key() == Qt.Key.Key_A:
                self._selected_indices = list(range(len(self._cards)))
                self._apply_selection_visuals()
                self._update_selection_count()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_I:
                self._toggle_invert_selected()
                event.accept()
                return
        super().keyPressEvent(event)

    def set_document(self, doc: Optional[QPdfDocument]):
        self._doc = doc
        self._inverted_pages.clear()
        self.rebuild_list()

    def set_mode(self, mode: str):
        if self._mode != mode:
            self._mode = mode
            self.rebuild_list()

    def get_inverted_pages(self) -> Set[int]:
        return set(self._inverted_pages)

    def clear_cards(self):
        for card in self._cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        self._selected_indices.clear()
        self._last_clicked_index = -1

    def rebuild_list(self):
        self.clear_cards()

        if not self._doc or self._doc.pageCount() == 0:
            self.count_badge.setText("0 Pages")
            self._update_selection_count()
            return

        page_count = self._doc.pageCount()

        if self._mode == "Normal":
            self.count_badge.setText(f"{page_count} Pages")
            self._build_normal_cards(page_count)
        elif self._mode == "Manual Duplex":
            import math
            sheets = math.ceil(page_count / 2)
            self.count_badge.setText(f"{sheets} Sheets ({page_count} Pgs)")
            self._build_duplex_cards(page_count)
        elif self._mode == "Booklet":
            import math
            sheets = math.ceil(page_count / 4)
            self.count_badge.setText(f"{sheets} Sheets ({page_count} Pgs)")
            self._build_booklet_cards(page_count)

        # Auto-select first card
        if self._cards:
            self._select_single(0)

    # ── Multi-Selection Logic ──

    def _on_card_clicked_with_modifiers(
        self, sheet_idx: int, is_back: bool, shift: bool, ctrl: bool
    ):
        # Find the card index in self._cards
        card_index = -1
        for i, card in enumerate(self._cards):
            if card.sheet_idx == sheet_idx and card.is_back == is_back:
                card_index = i
                break
        if card_index < 0:
            return

        if shift and self._last_clicked_index >= 0:
            # Range selection
            lo = min(self._last_clicked_index, card_index)
            hi = max(self._last_clicked_index, card_index)
            self._selected_indices = list(range(lo, hi + 1))
        elif ctrl:
            # Toggle selection
            if card_index in self._selected_indices:
                self._selected_indices.remove(card_index)
            else:
                self._selected_indices.append(card_index)
            self._last_clicked_index = card_index
        else:
            # Single select
            self._select_single(card_index)
            # Navigate center preview
            self.card_selected.emit(sheet_idx, is_back)
            return

        # Update visual state
        self._apply_selection_visuals()
        self._update_selection_count()

    def _select_single(self, card_index: int):
        self._selected_indices = [card_index]
        self._last_clicked_index = card_index
        self._apply_selection_visuals()
        self._update_selection_count()
        # Navigate center preview
        card = self._cards[card_index]
        self.card_selected.emit(card.sheet_idx, card.is_back)

    def _apply_selection_visuals(self):
        selected_set = set(self._selected_indices)
        for i, card in enumerate(self._cards):
            card.set_selected(i in selected_set)

    def _update_selection_count(self):
        n = len(self._selected_indices)
        self.lbl_selection_count.setText(f"{n} selected")

    def _toggle_select_all(self):
        if len(self._selected_indices) == len(self._cards):
            # Deselect all
            self._selected_indices.clear()
        else:
            # Select all
            self._selected_indices = list(range(len(self._cards)))
        self._apply_selection_visuals()
        self._update_selection_count()

    # ── Inversion Logic ──

    def _get_page_indices_for_card(self, card_index: int) -> List[int]:
        """Return the 0-based PDF page indices associated with a card."""
        if not self._doc:
            return []
        page_count = self._doc.pageCount()

        if self._mode == "Normal":
            pg = self._cards[card_index].sheet_idx
            return [pg] if pg < page_count else []

        elif self._mode == "Manual Duplex":
            s = self._cards[card_index].sheet_idx
            pages = []
            f_pg = s * 2
            b_pg = s * 2 + 1
            if f_pg < page_count:
                pages.append(f_pg)
            if b_pg < page_count:
                pages.append(b_pg)
            return pages

        elif self._mode == "Booklet":
            import math
            s = self._cards[card_index].sheet_idx
            sheets = math.ceil(page_count / 4)
            total_booklet = sheets * 4
            lf = total_booklet - 1 - 2 * s
            rf = 2 * s
            lb = 2 * s + 1
            rb = total_booklet - 2 - 2 * s
            pages = []
            for p in [lf, rf, lb, rb]:
                if 0 <= p < page_count:
                    pages.append(p)
            return pages

        return []

    def _toggle_invert_selected(self):
        if not self._doc or not self._selected_indices:
            return

        # Collect all page indices from selected cards
        all_pages: Set[int] = set()
        for ci in self._selected_indices:
            all_pages.update(self._get_page_indices_for_card(ci))

        # Determine toggle direction: if ALL selected pages are already inverted, un-invert
        if all_pages and all_pages.issubset(self._inverted_pages):
            self._inverted_pages -= all_pages
        else:
            self._inverted_pages |= all_pages

        # Update card visuals and thumbnails
        for ci in self._selected_indices:
            card = self._cards[ci]
            card_pages = self._get_page_indices_for_card(ci)
            is_inv = bool(card_pages) and all(
                p in self._inverted_pages for p in card_pages
            )
            card.set_inverted(is_inv)
            self._re_render_card_thumbnail(ci)

        self.inversion_changed.emit(set(self._inverted_pages))

    def _re_render_card_thumbnail(self, card_index: int):
        """Re-render a single card's thumbnail, applying inversion if needed."""
        if not self._doc:
            return
        page_count = self._doc.pageCount()
        card = self._cards[card_index]

        if self._mode == "Normal":
            pg = card.sheet_idx
            if 0 <= pg < page_count:
                pix = self._render_single_thumb(pg)
                card.update_thumbnail(pix)

        elif self._mode == "Manual Duplex":
            s = card.sheet_idx
            f_pg = s * 2
            b_pg = s * 2 + 1 if (s * 2 + 1) < page_count else None
            pix = self._render_duplex_dual_thumb(f_pg, b_pg)
            card.update_thumbnail(pix)

        elif self._mode == "Booklet":
            import math
            s = card.sheet_idx
            sheets = math.ceil(page_count / 4)
            total_booklet = sheets * 4
            lf = total_booklet - 1 - 2 * s
            rf = 2 * s
            lb = 2 * s + 1
            rb = total_booklet - 2 - 2 * s

            def val_or_none(p):
                return p if p < page_count else None

            pix = self._render_booklet_4up_thumb(
                val_or_none(lf), val_or_none(rf), val_or_none(lb), val_or_none(rb)
            )
            card.update_thumbnail(pix)

    # ── Card Builders ──

    def _build_normal_cards(self, page_count: int):
        for i in range(page_count):
            thumb = self._render_single_thumb(i)
            is_inv = i in self._inverted_pages
            card = ThumbnailCard(
                sheet_idx=i,
                is_back=False,
                title=f"Page {i + 1}",
                subtitle="1-Up",
                page_numbers=f"PDF Page {i + 1}",
                pixmap=thumb,
            )
            if is_inv:
                card.set_inverted(True)
            card.clicked_with_modifiers.connect(self._on_card_clicked_with_modifiers)
            self._cards.append(card)
            self.cards_layout.insertWidget(len(self._cards) - 1, card)

    def _build_duplex_cards(self, page_count: int):
        import math
        sheets = math.ceil(page_count / 2)
        for s in range(sheets):
            f_pg = s * 2
            b_pg = s * 2 + 1 if (s * 2 + 1) < page_count else None

            thumb = self._render_duplex_dual_thumb(f_pg, b_pg)
            f_str = f"P{f_pg + 1}"
            b_str = f"P{b_pg + 1}" if b_pg is not None else "Blank"

            pages_str = f"Front: PDF P{f_pg + 1}"
            if b_pg is not None:
                pages_str += f"  |  Back: PDF P{b_pg + 1}"
            else:
                pages_str += "  |  Back: Blank"

            card_pages = [f_pg]
            if b_pg is not None:
                card_pages.append(b_pg)
            is_inv = all(p in self._inverted_pages for p in card_pages)

            card = ThumbnailCard(
                sheet_idx=s,
                is_back=False,
                title=f"Sheet {s + 1}",
                subtitle=f"{f_str} \u2022 {b_str}",
                page_numbers=pages_str,
                pixmap=thumb,
            )
            if is_inv:
                card.set_inverted(True)
            card.clicked_with_modifiers.connect(self._on_card_clicked_with_modifiers)
            self._cards.append(card)
            self.cards_layout.insertWidget(len(self._cards) - 1, card)

    def _build_booklet_cards(self, page_count: int):
        import math
        sheets = math.ceil(page_count / 4)
        total_booklet_pages = sheets * 4

        for s in range(sheets):
            lf = total_booklet_pages - 1 - 2 * s
            rf = 2 * s
            lb = 2 * s + 1
            rb = total_booklet_pages - 2 - 2 * s

            def val_or_none(p):
                return p if p < page_count else None

            lf_idx = val_or_none(lf)
            rf_idx = val_or_none(rf)
            lb_idx = val_or_none(lb)
            rb_idx = val_or_none(rb)

            thumb = self._render_booklet_4up_thumb(lf_idx, rf_idx, lb_idx, rb_idx)

            page_parts = []
            for label, idx in [("LF", lf_idx), ("RF", rf_idx), ("LB", lb_idx), ("RB", rb_idx)]:
                page_parts.append(f"{label}:P{idx + 1}" if idx is not None else f"{label}:--")
            pages_str = "  ".join(page_parts)

            # Check inversion for all non-None pages
            card_pages = [p for p in [lf_idx, rf_idx, lb_idx, rb_idx] if p is not None]
            is_inv = bool(card_pages) and all(p in self._inverted_pages for p in card_pages)

            card = ThumbnailCard(
                sheet_idx=s,
                is_back=False,
                title=f"Sheet {s + 1}",
                subtitle="4 Pages",
                page_numbers=pages_str,
                pixmap=thumb,
            )
            if is_inv:
                card.set_inverted(True)
            card.clicked_with_modifiers.connect(self._on_card_clicked_with_modifiers)
            self._cards.append(card)
            self.cards_layout.insertWidget(len(self._cards) - 1, card)

    # ── Rendering Helpers ──

    def _draw_page_thumbnail(
        self,
        painter: QPainter,
        page_num: Optional[int],
        x: int,
        y: int,
        max_w: int,
        max_h: int,
        blank_text: str = "Blank",
    ):
        """
        Draw a physical paper page with solid white background and crisp contrast.
        If the page is in _inverted_pages, invert its pixels (black paper, white text).
        Draws a page number watermark badge in the bottom-right corner.
        """
        if page_num is not None and self._doc and 0 <= page_num < self._doc.pageCount():
            page_size = self._doc.pagePointSize(page_num)
            pw = page_size.width() if page_size.width() > 0 else 1.0
            ph = page_size.height() if page_size.height() > 0 else 1.0

            scale = min(max_w / pw, max_h / ph)
            target_w = max(1, int(pw * scale))
            target_h = max(1, int(ph * scale))

            px = x + (max_w - target_w) // 2
            py = y + (max_h - target_h) // 2

            # 1. Solid pure white paper sheet
            painter.fillRect(px, py, target_w, target_h, QColor("#ffffff"))

            # 2. Render page onto white paper
            img = self._doc.render(page_num, QSize(target_w, target_h))

            # 3. Invert if this page is in the inverted set
            if page_num in self._inverted_pages:
                img.invertPixels(QImage.InvertMode.InvertRgb)
                # Re-fill paper with black for inverted look
                painter.fillRect(px, py, target_w, target_h, QColor("#000000"))

            painter.drawImage(px, py, img)

            # 4. Subtle crisp paper border
            painter.setPen(QColor("#d4d4d8"))
            painter.drawRect(px, py, target_w - 1, target_h - 1)

            # 5. Page number watermark badge (bottom-right corner)
            badge_text = str(page_num + 1)
            badge_font = QFont("sans-serif", 6, QFont.Weight.Bold)
            painter.setFont(badge_font)

            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(badge_text) + 6
            text_h = fm.height() + 2
            badge_x = px + target_w - text_w - 2
            badge_y = py + target_h - text_h - 2

            painter.fillRect(badge_x, badge_y, text_w, text_h, QColor(0, 0, 0, 150))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(
                badge_x, badge_y, text_w, text_h,
                Qt.AlignmentFlag.AlignCenter, badge_text,
            )
        else:
            # Blank physical paper sheet
            painter.fillRect(x, y, max_w, max_h, QColor("#ffffff"))
            painter.setPen(QColor("#d4d4d8"))
            painter.drawRect(x, y, max_w - 1, max_h - 1)
            painter.setPen(QColor("#636363"))
            painter.setFont(QFont("sans-serif", 7))
            painter.drawText(
                x, y, max_w, max_h, Qt.AlignmentFlag.AlignCenter, blank_text
            )

    def _render_single_thumb(self, page_num: int) -> QPixmap:
        """Render 1 page thumbnail with solid white paper background."""
        if not self._doc or page_num < 0 or page_num >= self._doc.pageCount():
            return QPixmap()

        w, h = 180, 110
        pix = QPixmap(w, h)
        pix.fill(QColor("#212126"))

        painter = QPainter(pix)
        self._draw_page_thumbnail(painter, page_num, 8, 6, w - 16, h - 12)
        painter.end()
        return pix

    def _render_duplex_dual_thumb(
        self, front_page: int, back_page: Optional[int]
    ) -> QPixmap:
        """Render 2 pages side-by-side: Front (left) and Back (right)."""
        w, h = 180, 110
        pix = QPixmap(w, h)
        pix.fill(QColor("#212126"))

        painter = QPainter(pix)
        half_w = (w - 16) // 2
        thumb_h = h - 22

        # Draw Front Page (Left)
        painter.setFont(QFont("sans-serif", 8, QFont.Weight.Bold))
        painter.setPen(QColor("#E64B3D"))
        painter.drawText(6, 12, "FRONT")
        self._draw_page_thumbnail(painter, front_page, 6, 16, half_w, thumb_h)

        # Center separator
        painter.setPen(QPen(QColor("#40404a"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(w // 2, 4, w // 2, h - 4)

        # Draw Back Page (Right)
        painter.setFont(QFont("sans-serif", 8, QFont.Weight.Bold))
        painter.setPen(QColor("#636363"))
        painter.drawText(w // 2 + 6, 12, "BACK")
        self._draw_page_thumbnail(
            painter, back_page, w // 2 + 6, 16, half_w, thumb_h
        )

        painter.end()
        return pix

    def _render_booklet_4up_thumb(
        self,
        lf: Optional[int],
        rf: Optional[int],
        lb: Optional[int],
        rb: Optional[int],
    ) -> QPixmap:
        """
        Render 4 pages arranged like a real-world booklet sheet signature:
        - Top half: Front side [Left Front | Right Front]
        - Bottom half: Back side [Left Back | Right Back]
        """
        w, h = 180, 140
        pix = QPixmap(w, h)
        pix.fill(QColor("#212126"))

        painter = QPainter(pix)
        half_w = (w - 16) // 2
        row_h = 50

        # 1. TOP ROW: FRONT SIDE [LF | RF]
        painter.setFont(QFont("sans-serif", 7, QFont.Weight.Bold))
        painter.setPen(QColor("#E64B3D"))
        painter.drawText(6, 11, "FRONT SIDE")

        # Left Front
        self._draw_page_thumbnail(painter, lf, 6, 14, half_w, row_h)

        # Spine Fold Line (Front)
        painter.setPen(QPen(QColor("#E64B3D"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(w // 2, 14, w // 2, 14 + row_h)

        # Right Front
        self._draw_page_thumbnail(painter, rf, w // 2 + 4, 14, half_w, row_h)

        # 2. HORIZONTAL SHEET DIVIDER
        painter.setPen(QPen(QColor("#36363d"), 1))
        painter.drawLine(4, 70, w - 4, 70)

        # 3. BOTTOM ROW: BACK SIDE [LB | RB]
        painter.setFont(QFont("sans-serif", 7, QFont.Weight.Bold))
        painter.setPen(QColor("#636363"))
        painter.drawText(6, 81, "BACK SIDE")

        # Left Back
        self._draw_page_thumbnail(painter, lb, 6, 84, half_w, row_h)

        # Spine Fold Line (Back)
        painter.setPen(QPen(QColor("#E64B3D"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(w // 2, 84, w // 2, 84 + row_h)

        # Right Back
        self._draw_page_thumbnail(painter, rb, w // 2 + 4, 84, half_w, row_h)

        painter.end()
        return pix
