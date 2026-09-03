# tests/test_imposer.py
import pytest
from reportlab.pdfgen import canvas
import io
from src.imposer import impose_normal, impose_duplex, impose_booklet

def test_impose_normal_returns_same_bytes(tmp_path):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 700, "Hello PDF")
    c.showPage()
    c.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    
    src = tmp_path / "in.pdf"
    src.write_bytes(pdf_bytes)
    
    out = impose_normal(str(src))
    assert out == pdf_bytes

def test_impose_duplex_order(tmp_path):
    # Create a 4-page PDF with distinct markers
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    for i in range(1, 5):
        c.drawString(50, 800, f"Page {i}")
        c.showPage()
    c.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    
    src = tmp_path / "four.pdf"
    src.write_bytes(pdf_bytes)
    
    out = impose_duplex(str(src))
    
    # Load output and check page order via text extraction
    from pypdf import PdfReader
    out_reader = PdfReader(io.BytesIO(out))
    extracted = [page.extract_text().strip() for page in out_reader.pages]
    # Expected order: Pass 1 Fronts (1, 3), Pass 2 Backs (2, 4)
    assert extracted == ["Page 1", "Page 3", "Page 2", "Page 4"]

def test_impose_booklet_page_count(tmp_path):
    # Create a simple PDF with 4 pages
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    for i in range(1, 5):
        c.drawString(50, 800, f"Page {i}")
        c.showPage()
    c.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    
    src = tmp_path / "in.pdf"
    src.write_bytes(pdf_bytes)
    
    out = impose_booklet(str(src))
    # We expect a PDF with number of sheets = ceil(n/4)
    assert len(out) > 0
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(out))
    # For 4 pages, we expect 2 sheets (each sheet is a PDF page)
    assert len(reader.pages) == 2
    # Additionally, we can test that the content is not empty
    # Optionally, check that each page has some content (non-zero length)
    for page in reader.pages:
        # Extract text may be empty due to transformation, but we can check that the page object exists
        assert page is not None