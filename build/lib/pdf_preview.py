from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpinBox, QListView, QLabel
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtCore import Qt, QSize, QSizeF, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPixmap, QPainter, QImage
from typing import Optional


class PdfPreview(QWidget):
    """
    A custom widget for PDF preview with page navigation and optional thumbnail strip.
    """
    # Signal emitted when the current page changes (0-based index)
    currentPageChanged = pyqtSignal(int)

    def __init__(self, show_thumbnails: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._show_thumbnails = show_thumbnails
        self._pdf_doc: Optional[QPdfDocument] = None
        self._current_page: int = 0

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main view
        self.pdf_view = QPdfView(self)
        self.pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
        layout.addWidget(self.pdf_view, stretch=1)

        # Page navigation controls
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(QLabel("Page:"))
        self.page_spinbox = QSpinBox(self)
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)  # Will be updated when document is set
        self.page_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.page_spinbox)
        nav_layout.addStretch()
        layout.addLayout(nav_layout)

        # Thumbnail strip (optional)
        if self._show_thumbnails:
            self.thumbnail_list = QListView(self)
            self.thumbnail_list.setFixedHeight(90)
            self.thumbnail_list.setViewMode(QListView.ViewMode.IconMode)
            self.thumbnail_list.setIconSize(QSize(60, 80))
            self.thumbnail_list.setSpacing(2)
            self.thumbnail_list.setResizeMode(QListView.ResizeMode.Adjust)
            layout.addWidget(self.thumbnail_list)
        else:
            self.thumbnail_list = None

    def _connect_signals(self):
        navigator = self.pdf_view.pageNavigator()
        navigator.currentPageChanged.connect(self._on_view_page_changed)
        self.page_spinbox.valueChanged.connect(self._on_spinbox_value_changed)

        # Thumbnail click navigation
        if self.thumbnail_list:
            self.thumbnail_list.clicked.connect(self._on_thumbnail_clicked)

    def setDocument(self, doc: QPdfDocument):
        self._pdf_doc = doc
        self.pdf_view.setDocument(doc)
        
        # Connect page navigator signals
        navigator = self.pdf_view.pageNavigator()
        if navigator:
            navigator.currentPageChanged.connect(self._on_view_page_changed)

        if doc is not None:
            page_count = doc.pageCount()
            self.page_spinbox.setMaximum(page_count)
            # Set to first page if valid
            if page_count > 0:
                self.setPageNumber(0)
            else:
                self.setPageNumber(-1)  # Invalid
            self._generate_thumbnails()
        else:
            self.page_spinbox.setMaximum(1)
            self.page_spinbox.setValue(0)
            self.current_page = -1
            if self.thumbnail_list:
                self.thumbnail_list.model().removeRows(0, self.thumbnail_list.model().rowCount()) if self.thumbnail_list.model() else None

    def setPageNumber(self, page: int):
        """Set current page (0-based index)."""
        if self._pdf_doc is None:
            return
        page_count = self._pdf_doc.pageCount()
        if 0 <= page < page_count:
            self._current_page = page
            navigator = self.pdf_view.pageNavigator()
            if navigator:
                from PyQt6.QtCore import QPointF
                navigator.jump(page, QPointF(0, 0), 0.0)
            self.page_spinbox.blockSignals(True)
            self.page_spinbox.setValue(page + 1)  # Convert to 1-based for spinbox
            self.page_spinbox.blockSignals(False)
            self.currentPageChanged.emit(page)
        # If page is out of bounds, do nothing (or could clamp)

    def pageCount(self) -> int:
        return self._pdf_doc.pageCount() if self._pdf_doc else 0

    def currentPage(self) -> int:
        return self._current_page

    def _on_view_page_changed(self, page: int):
        """Called when QPdfView changes page (via user interaction)."""
        self._current_page = page
        self.page_spinbox.blockSignals(True)
        self.page_spinbox.setValue(page + 1)
        self.page_spinbox.blockSignals(False)
        if self.thumbnail_list:
            self.thumbnail_list.setCurrentIndex(self.thumbnail_list.model().index(page, 0))
        self.currentPageChanged.emit(page)

    def _on_spinbox_value_changed(self, value: int):
        """Called when user changes spinbox."""
        page = value - 1  # Convert to 0-based
        self.setPageNumber(page)

    def _generate_thumbnails(self):
        """Generate thumbnails for all pages and set up the thumbnail list view."""
        if not self._show_thumbnails or self._pdf_doc is None:
            return

        from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon

        page_count = self._pdf_doc.pageCount()
        model = QStandardItemModel()
        self.thumbnail_list.setModel(model)

        for i in range(page_count):
            # Render page to image (small size)
            image = self._pdf_doc.render(i, QSize(60, 80))
            if image.isNull():
                continue
            pixmap = QPixmap.fromImage(image)
            item = QStandardItem()
            item.setIcon(QIcon(pixmap))
            item.setEditable(False)
            model.appendRow(item)

        # Select current page thumbnail
        if page_count > 0:
            self.thumbnail_list.setCurrentIndex(model.index(self._current_page, 0))

    def _on_thumbnail_clicked(self, index):
        """Handle thumbnail click to navigate to page."""
        page = index.row()
        self.setPageNumber(page)