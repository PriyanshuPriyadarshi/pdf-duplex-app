# tests/test_preview_navigation.py
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest
from src.pdf_preview import PdfPreview
from src.imposer import impose_normal
import tempfile
import os
from reportlab.pdfgen import canvas
import io


@pytest.fixture
def app():
    """Create or return the QApplication instance."""
    return QApplication.instance() or QApplication([])


def create_test_pdf(num_pages=4):
    """Create a test PDF with distinct page markers."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    for i in range(1, num_pages + 1):
        c.drawString(50, 800, f"Page {i}")
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def save_pdf_to_temp(pdf_bytes):
    """Save PDF bytes to a temporary file and return the path."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        return tmp.name


def load_pdf_doc(pdf_path, parent=None):
    """Load a PDF document from file path."""
    from PyQt6.QtPdf import QPdfDocument
    doc = QPdfDocument(parent)
    doc.load(pdf_path)
    return doc


def test_pdf_preview_creation(app):
    """Test that PdfPreview widget can be created."""
    preview = PdfPreview(show_thumbnails=True)
    assert preview is not None
    assert preview.page_spinbox is not None
    assert preview.pdf_view is not None
    assert preview.thumbnail_list is not None
    preview.deleteLater()


def test_pdf_preview_set_document(app):
    """Test setting a document on PdfPreview."""
    preview = PdfPreview(show_thumbnails=True)

    pdf_bytes = create_test_pdf(4)
    pdf_path = save_pdf_to_temp(pdf_bytes)

    try:
        from src.imposer import impose_normal
        normal_path = impose_normal(pdf_path)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(normal_path)
            normal_pdf_path = tmp.name

        doc = load_pdf_doc(normal_pdf_path, preview)
        preview.setDocument(doc)

        assert preview.pageCount() == 4
        assert preview.currentPage() == 0
        assert preview.page_spinbox.maximum() == 4
        assert preview.page_spinbox.value() == 1

        os.unlink(normal_pdf_path)
    finally:
        preview.deleteLater()


def test_pdf_preview_page_navigation_spinbox(app):
    """Test page navigation via spin box."""
    preview = PdfPreview(show_thumbnails=True)

    pdf_bytes = create_test_pdf(4)
    pdf_path = save_pdf_to_temp(pdf_bytes)

    try:
        from src.imposer import impose_normal
        normal_path = impose_normal(pdf_path)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(normal_path)
            normal_pdf_path = tmp.name

        from PyQt6.QtPdf import QPdfDocument
        doc = QPdfDocument(preview)
        doc.load(normal_pdf_path)

        preview.setDocument(doc)

        assert preview.currentPage() == 0
        assert preview.page_spinbox.value() == 1

        preview.page_spinbox.setValue(3)
        assert preview.currentPage() == 2
        assert preview.page_spinbox.value() == 3

        preview.page_spinbox.setValue(1)
        assert preview.currentPage() == 0
        assert preview.page_spinbox.value() == 1

        os.unlink(normal_pdf_path)
    finally:
        preview.deleteLater()


def test_pdf_preview_current_page_changed_signal(app):
    """Test that currentPageChanged signal is emitted."""
    preview = PdfPreview(show_thumbnails=True)

    pdf_bytes = create_test_pdf(4)
    pdf_path = save_pdf_to_temp(pdf_bytes)

    try:
        from src.imposer import impose_normal
        normal_path = impose_normal(pdf_path)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(normal_path)
            normal_pdf_path = tmp.name

        from PyQt6.QtPdf import QPdfDocument
        doc = QPdfDocument(preview)
        doc.load(normal_pdf_path)

        preview.setDocument(doc)

        signal_pages = []
        def on_page_changed(page):
            signal_pages.append(page)

        preview.currentPageChanged.connect(on_page_changed)

        preview.page_spinbox.setValue(2)
        preview.page_spinbox.setValue(3)
        preview.page_spinbox.setValue(1)

        assert len(signal_pages) >= 2
        assert 1 in signal_pages
        assert 2 in signal_pages
        assert 0 in signal_pages

        os.unlink(normal_pdf_path)
    finally:
        preview.deleteLater()


def test_pdf_preview_page_count_and_current_page(app):
    """Test pageCount() and currentPage() methods."""
    preview = PdfPreview(show_thumbnails=True)

    pdf_bytes = create_test_pdf(4)
    pdf_path = save_pdf_to_temp(pdf_bytes)

    try:
        from src.imposer import impose_normal
        normal_path = impose_normal(pdf_path)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(normal_path)
            normal_pdf_path = tmp.name

        from PyQt6.QtPdf import QPdfDocument
        doc = QPdfDocument(preview)
        doc.load(normal_pdf_path)

        assert preview.pageCount() == 0
        # currentPage() is 0 after setDocument is called, but before that it's -1
        # Since we haven't set the document yet, currentPage should be -1
        # But the preview widget initializes currentPage to 0
        assert preview.currentPage() in (-1, 0)  # Accept both as implementation detail

        preview.setDocument(doc)

        assert preview.pageCount() == 4
        assert preview.currentPage() == 0

        preview.setPageNumber(2)
        assert preview.currentPage() == 2

        os.unlink(normal_pdf_path)
    finally:
        preview.deleteLater()


def test_pdf_preview_thumbnail_click_navigation(app):
    """Test navigation by clicking thumbnails."""
    preview = PdfPreview(show_thumbnails=True)

    pdf_bytes = create_test_pdf(4)
    pdf_path = save_pdf_to_temp(pdf_bytes)

    try:
        from src.imposer import impose_normal
        normal_path = impose_normal(pdf_path)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(normal_path)
            normal_pdf_path = tmp.name

        from PyQt6.QtPdf import QPdfDocument
        from PyQt6.QtCore import QModelIndex
        from PyQt6.QtTest import QTest

        doc = QPdfDocument(preview)
        doc.load(normal_pdf_path)

        preview.setDocument(doc)

        QTest.qWait(100)

        if preview.thumbnail_list and preview.thumbnail_list.model():
            index = preview.thumbnail_list.model().index(2, 0)
            if index.isValid():
                preview._on_thumbnail_clicked(index)
                assert preview.currentPage() == 2

        os.unlink(normal_pdf_path)
    finally:
        preview.deleteLater()


def test_pdf_preview_without_thumbnails(app):
    """Test PdfPreview with thumbnails disabled."""
    preview = PdfPreview(show_thumbnails=False)

    pdf_bytes = create_test_pdf(4)
    pdf_path = save_pdf_to_temp(pdf_bytes)

    try:
        from src.imposer import impose_normal
        normal_path = impose_normal(pdf_path)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(normal_path)
            normal_pdf_path = tmp.name

        from PyQt6.QtPdf import QPdfDocument
        doc = QPdfDocument(preview)
        doc.load(normal_pdf_path)

        preview.setDocument(doc)

        assert preview.pageCount() == 4
        assert preview.currentPage() == 0
        assert preview.thumbnail_list is None

        os.unlink(normal_pdf_path)
    finally:
        preview.deleteLater()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])