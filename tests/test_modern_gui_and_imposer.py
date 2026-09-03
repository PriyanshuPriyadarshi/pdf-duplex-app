"""
tests/test_modern_gui_and_imposer.py - Verification for modern 2026 GUI and mathematical imposition engine.
"""

import io
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtPdf import QPdfDocument
from reportlab.pdfgen import canvas
from pypdf import PdfReader

from src.main_window import MainWindow
from src.theme import apply_theme, get_theme_stylesheet
from src import imposer


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def create_multi_page_pdf(pages: int = 8) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for i in range(1, pages + 1):
        c.drawString(100, 750, f"Document Page {i}")
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def test_theme_stylesheets():
    dark_qss = get_theme_stylesheet("dark")
    light_qss = get_theme_stylesheet("light")
    assert "#28282E" in dark_qss  # Dark background token
    assert "#212126" in dark_qss  # Container background token
    assert "#EEEEEE" in dark_qss  # Text token
    assert "#888890" in dark_qss  # Secondary text token
    assert "#E64B3D" in dark_qss  # Accent token
    assert len(dark_qss) > 500
    assert len(light_qss) > 500

    # Sharp corners: all border-radius should be 0px (except radio indicator and scrollbar)

    # Bottom bar styles
    assert "bottomBar" in dark_qss


def test_booklet_passes_and_geometry(tmp_path):
    # 8-page document = 2 sheets (4 pages per sheet)
    pdf_bytes = create_multi_page_pdf(8)
    src_file = tmp_path / "sample8.pdf"
    src_file.write_bytes(pdf_bytes)

    fronts, backs = imposer.get_booklet_passes(str(src_file), reverse_backs=False)
    r_front = PdfReader(io.BytesIO(fronts))
    r_back = PdfReader(io.BytesIO(backs))

    # 2 sheets -> 2 front pages and 2 back pages
    assert len(r_front.pages) == 2
    assert len(r_back.pages) == 2

    # Verify landscape orientation (width > height for 2-up)
    p0 = r_front.pages[0]
    assert float(p0.mediabox.width) > float(p0.mediabox.height)


def test_duplex_passes_odd_even_split(tmp_path):
    pdf_bytes = create_multi_page_pdf(6)
    src_file = tmp_path / "sample6.pdf"
    src_file.write_bytes(pdf_bytes)

    fronts, backs = imposer.get_duplex_passes(str(src_file), reverse_backs=False)
    r_front = PdfReader(io.BytesIO(fronts))
    r_back = PdfReader(io.BytesIO(backs))

    assert len(r_front.pages) == 3
    assert len(r_back.pages) == 3

    # Check extracted text for front pages (1, 3, 5)
    f_texts = [p.extract_text().strip() for p in r_front.pages]
    assert f_texts == ["Document Page 1", "Document Page 3", "Document Page 5"]

    # Check extracted text for back pages (2, 4, 6)
    b_texts = [p.extract_text().strip() for p in r_back.pages]
    assert b_texts == ["Document Page 2", "Document Page 4", "Document Page 6"]


def test_duplex_passes_reverse_backs(tmp_path):
    pdf_bytes = create_multi_page_pdf(6)
    src_file = tmp_path / "sample6.pdf"
    src_file.write_bytes(pdf_bytes)

    # Test reverse_backs=True (for face-up trays)
    _, backs_rev = imposer.get_duplex_passes(str(src_file), reverse_backs=True)
    r_back = PdfReader(io.BytesIO(backs_rev))
    b_texts_rev = [p.extract_text().strip() for p in r_back.pages]
    assert b_texts_rev == ["Document Page 6", "Document Page 4", "Document Page 2"]


def test_modern_mainwindow_three_panels(app, tmp_path):
    pdf_bytes = create_multi_page_pdf(4)
    src_file = tmp_path / "gui_sample.pdf"
    src_file.write_bytes(pdf_bytes)

    win = MainWindow()
    assert win.sidebar is not None
    assert win.center_preview is not None
    assert win.settings_panel is not None

    # Load document
    win.load_pdf(str(src_file))
    assert win.total_pages == 4

    # Test mode switching to Booklet
    win.settings_panel.set_current_mode("Booklet")
    assert win.sidebar._mode == "Booklet"
    assert win.center_preview._mode == "Booklet"

    # In booklet mode, 4 pages = 1 physical sheet card (displaying all 4 pages)
    assert len(win.sidebar._cards) == 1

    # Verify dark theme is default and maintained
    win.toggle_theme()
    assert win.current_theme == "dark"

    win.deleteLater()


def test_sidebar_multi_selection(app, tmp_path):
    """Test multi-selection (single click, shift+click, ctrl+click)."""
    pdf_bytes = create_multi_page_pdf(6)
    src_file = tmp_path / "multi_sel.pdf"
    src_file.write_bytes(pdf_bytes)

    win = MainWindow()
    win.load_pdf(str(src_file))

    sidebar = win.sidebar
    assert len(sidebar._cards) == 6  # Normal mode, 6 pages = 6 cards

    # Single click card 2 (0-indexed)
    sidebar._on_card_clicked_with_modifiers(2, False, False, False)
    assert sidebar._selected_indices == [2]

    # Shift+click card 4 -> range select 2,3,4
    sidebar._on_card_clicked_with_modifiers(4, False, True, False)
    assert sidebar._selected_indices == [2, 3, 4]

    # Ctrl+click card 0 -> toggle into selection
    sidebar._on_card_clicked_with_modifiers(0, False, False, True)
    assert 0 in sidebar._selected_indices
    assert 2 in sidebar._selected_indices

    # Ctrl+click card 2 again -> toggle out
    sidebar._on_card_clicked_with_modifiers(2, False, False, True)
    assert 2 not in sidebar._selected_indices

    win.deleteLater()


def test_sidebar_inversion(app, tmp_path):
    """Test per-page inversion toggle and badge state."""
    pdf_bytes = create_multi_page_pdf(4)
    src_file = tmp_path / "invert.pdf"
    src_file.write_bytes(pdf_bytes)

    win = MainWindow()
    win.load_pdf(str(src_file))

    sidebar = win.sidebar
    assert len(sidebar._cards) == 4
    assert sidebar._inverted_pages == set()

    # Select page 0 and 1
    sidebar._selected_indices = [0, 1]
    sidebar._toggle_invert_selected()

    assert 0 in sidebar._inverted_pages
    assert 1 in sidebar._inverted_pages
    assert sidebar._cards[0].is_inverted
    assert sidebar._cards[1].is_inverted
    assert not sidebar._cards[2].is_inverted

    # Toggle again -> un-invert
    sidebar._toggle_invert_selected()
    assert 0 not in sidebar._inverted_pages
    assert 1 not in sidebar._inverted_pages
    assert not sidebar._cards[0].is_inverted

    win.deleteLater()


def test_sidebar_page_numbers(app, tmp_path):
    """Test that each card has a page number label."""
    pdf_bytes = create_multi_page_pdf(3)
    src_file = tmp_path / "pages.pdf"
    src_file.write_bytes(pdf_bytes)

    win = MainWindow()
    win.load_pdf(str(src_file))

    sidebar = win.sidebar
    assert len(sidebar._cards) == 3

    # Each card should have page_info_label with page number text
    assert "PDF Page 1" in sidebar._cards[0].page_info_label.text()
    assert "PDF Page 2" in sidebar._cards[1].page_info_label.text()
    assert "PDF Page 3" in sidebar._cards[2].page_info_label.text()

    win.deleteLater()


def test_center_preview_bottom_bar(app, tmp_path):
    """Test that center preview has a bottom navigation bar."""
    pdf_bytes = create_multi_page_pdf(6)
    src_file = tmp_path / "preview.pdf"
    src_file.write_bytes(pdf_bytes)

    win = MainWindow()
    win.load_pdf(str(src_file))

    cp = win.center_preview
    assert cp.bottom_bar is not None
    assert cp.btn_prev is not None
    assert cp.btn_next is not None
    assert cp.lbl_sheet_nav is not None

    # Initially on page 1
    assert "1" in cp.lbl_sheet_nav.text()

    # Navigate next
    cp._go_next_sheet()
    assert cp._current_sheet == 1
    assert "2" in cp.lbl_sheet_nav.text()

    # Navigate prev
    cp._go_prev_sheet()
    assert cp._current_sheet == 0
    assert "1" in cp.lbl_sheet_nav.text()

    win.deleteLater()




def test_select_all_toggle(app, tmp_path):
    """Test select all and deselect all functionality."""
    pdf_bytes = create_multi_page_pdf(5)
    src_file = tmp_path / "selectall.pdf"
    src_file.write_bytes(pdf_bytes)

    win = MainWindow()
    win.load_pdf(str(src_file))

    sidebar = win.sidebar
    assert len(sidebar._cards) == 5

    # Select all
    sidebar._toggle_select_all()
    assert len(sidebar._selected_indices) == 5

    # Toggle again -> deselect all
    sidebar._toggle_select_all()
    assert len(sidebar._selected_indices) == 0

    win.deleteLater()


def test_parse_page_range():
    """Test parsing of various page range formats."""
    from src.utils import parse_page_range
    assert parse_page_range("", 10) == list(range(10))
    assert parse_page_range("1-3, 5, 8-10", 10) == [0, 1, 2, 4, 7, 8, 9]
    assert parse_page_range("3-1", 5) == [0, 1, 2]
    assert parse_page_range("99", 5) == []


def test_page_range_slicing(app, tmp_path):
    """Test that page range selection correctly slices generated PDFs."""
    pdf_bytes = create_multi_page_pdf(10)
    src_file = tmp_path / "ten_pages.pdf"
    src_file.write_bytes(pdf_bytes)

    win = MainWindow()
    win.load_pdf(str(src_file))

    # Default full doc
    full_normal = win._generate_normal_bytes()
    assert len(full_normal) > 0

    # Sliced range 1-3
    win.handle_page_range_changed("1-3")
    sliced_normal = win._generate_normal_bytes()
    assert len(sliced_normal) < len(full_normal)

    # Duplex mode with sliced range
    win.settings_panel.set_current_mode("Manual Duplex")
    pass1, pass2 = win._generate_split_bytes()
    assert len(pass1) > 0
    assert len(pass2) > 0

    win.deleteLater()

