"""
tests/test_presentation_and_page_numbers.py - Verification for Presentation Print Booklet mode
and unified page numbering across front and back combined passes.
"""

import io
import pytest
from PyQt6.QtWidgets import QApplication
from reportlab.pdfgen import canvas
from pypdf import PdfReader

from src.main_window import MainWindow
from src import imposer


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def create_landscape_presentation_pdf(pages: int = 8, width: float = 960, height: float = 540) -> bytes:
    """Create a 16:9 widescreen presentation slide PDF."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    for i in range(1, pages + 1):
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, height / 2, f"Slide {i} Content")
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def test_presentation_booklet_geometry_and_stacking(tmp_path):
    """Test that presentation booklet creates a portrait sheet with slides stacked Top and Bottom."""
    # 8-page 16:9 presentation (960 x 540) -> 2 sheets (4 pages per sheet)
    pdf_bytes = create_landscape_presentation_pdf(8, width=960, height=540)
    src_file = tmp_path / "slides8.pdf"
    src_file.write_bytes(pdf_bytes)

    # Standard booklet creates landscape sheets (pw*2, ph)
    fronts_std, backs_std = imposer.get_booklet_passes(str(src_file), presentation_mode=False)
    r_std = PdfReader(io.BytesIO(fronts_std))
    page_std = r_std.pages[0]
    assert float(page_std.mediabox.width) > float(page_std.mediabox.height)

    # Presentation booklet creates portrait sheets (pw, sheet_h where sheet_h > pw)
    fronts_pres, backs_pres = imposer.get_booklet_passes(str(src_file), presentation_mode=True)
    r_front = PdfReader(io.BytesIO(fronts_pres))
    r_back = PdfReader(io.BytesIO(backs_pres))

    assert len(r_front.pages) == 2
    assert len(r_back.pages) == 2

    page_pres = r_front.pages[0]
    # Height must be greater than width (portrait sheet for top-and-bottom stacked slides)
    assert float(page_pres.mediabox.height) > float(page_pres.mediabox.width)
    assert float(page_pres.mediabox.width) == 960.0

    # Test impose_booklet with presentation_mode
    booklet_bytes = imposer.impose_booklet(str(src_file), presentation_mode=True)
    r_booklet = PdfReader(io.BytesIO(booklet_bytes))
    # 2 sheets interleaved = 4 pages (Sheet 0 Front, Sheet 0 Back, Sheet 1 Front, Sheet 1 Back)
    assert len(r_booklet.pages) == 4
    for p in r_booklet.pages:
        assert float(p.mediabox.height) > float(p.mediabox.width)


def test_duplex_page_numbers_unified_across_passes(tmp_path):
    """Test that manual duplex stamps input pages so Pass 1 and Pass 2 combined form continuous 1..N."""
    pdf_bytes = create_landscape_presentation_pdf(6)
    src_file = tmp_path / "doc6.pdf"
    src_file.write_bytes(pdf_bytes)

    fronts, backs = imposer.get_duplex_passes(
        str(src_file),
        reverse_backs=False,
        print_page_numbers=True,
        page_number_pos="Bottom Right",
    )
    r_front = PdfReader(io.BytesIO(fronts))
    r_back = PdfReader(io.BytesIO(backs))

    assert len(r_front.pages) == 3
    assert len(r_back.pages) == 3

    # Check that text in front pages contains odd slide text
    f_texts = [p.extract_text() for p in r_front.pages]
    assert "Slide 1 Content" in f_texts[0]
    assert "Slide 3 Content" in f_texts[1]
    assert "Slide 5 Content" in f_texts[2]

    # Check that text in back pages contains even slide text
    b_texts = [p.extract_text() for p in r_back.pages]
    assert "Slide 2 Content" in b_texts[0]
    assert "Slide 4 Content" in b_texts[1]
    assert "Slide 6 Content" in b_texts[2]


def test_presentation_booklet_page_numbers(tmp_path):
    """Test that presentation booklet passes retain stamped page numbers 1..N across both passes."""
    pdf_bytes = create_landscape_presentation_pdf(8)
    src_file = tmp_path / "doc8.pdf"
    src_file.write_bytes(pdf_bytes)

    fronts, backs = imposer.get_booklet_passes(
        str(src_file),
        reverse_backs=False,
        presentation_mode=True,
        print_page_numbers=True,
        page_number_pos="Bottom Right",
    )
    r_front = PdfReader(io.BytesIO(fronts))
    r_back = PdfReader(io.BytesIO(backs))

    assert len(r_front.pages) == 2
    assert len(r_back.pages) == 2

    # Sheet 0 Front has Slide 8 (Top) and Slide 1 (Bottom)
    text_f0 = r_front.pages[0].extract_text()
    assert "Slide 8 Content" in text_f0
    assert "Slide 1 Content" in text_f0

    # Sheet 0 Back has Slide 2 (Top) and Slide 7 (Bottom)
    text_b0 = r_back.pages[0].extract_text()
    assert "Slide 2 Content" in text_b0
    assert "Slide 7 Content" in text_b0


def test_gui_presentation_mode_checkbox(app, tmp_path):
    """Test GUI controls for presentation print booklet mode."""
    window = MainWindow()
    settings_panel = window.settings_panel

    # Checkbox exists
    assert hasattr(settings_panel, "check_presentation_booklet")
    assert not settings_panel.check_presentation_booklet.isEnabled()

    # Switch to Booklet mode -> checkbox becomes enabled
    settings_panel.set_current_mode("Booklet")
    assert settings_panel.check_presentation_booklet.isEnabled()

    # Toggle presentation booklet
    settings_panel.set_presentation_booklet(True)
    settings = settings_panel.get_settings()
    assert settings["presentation_booklet"] is True

    # Switching to Normal disables checkbox
    settings_panel.set_current_mode("Normal")
    assert not settings_panel.check_presentation_booklet.isEnabled()


def test_gui_split_passes_with_selected_pages_and_page_numbers(app, tmp_path):
    """Test generating split passes with custom page range and page numbers enabled."""
    pdf_bytes = create_landscape_presentation_pdf(10)
    src_file = tmp_path / "slides10.pdf"
    src_file.write_bytes(pdf_bytes)

    window = MainWindow()
    window.load_pdf(str(src_file))

    # Select custom range: pages 1 to 4 (4 pages total)
    window.handle_page_range_changed("1-4")
    assert window.selected_page_indices == [0, 1, 2, 3]

    # Enable Booklet and Presentation Mode with page numbers
    window.settings_panel.set_current_mode("Booklet")
    window.settings_panel.set_presentation_booklet(True)
    window.settings_panel.check_page_numbers.setChecked(True)

    pass1, pass2 = window._generate_split_bytes()
    r1 = PdfReader(io.BytesIO(pass1))
    r2 = PdfReader(io.BytesIO(pass2))

    # 4 pages = 1 sheet in booklet
    assert len(r1.pages) == 1
    assert len(r2.pages) == 1

    # Orientation is portrait
    assert float(r1.pages[0].mediabox.height) > float(r1.pages[0].mediabox.width)
    assert float(r2.pages[0].mediabox.height) > float(r2.pages[0].mediabox.width)

    # Front contains Slide 4 and Slide 1
    t1 = r1.pages[0].extract_text()
    assert "Slide 4 Content" in t1
    assert "Slide 1 Content" in t1

    # Back contains Slide 2 and Slide 3
    t2 = r2.pages[0].extract_text()
    assert "Slide 2 Content" in t2
    assert "Slide 3 Content" in t2
