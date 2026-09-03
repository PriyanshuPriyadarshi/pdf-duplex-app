# tests/test_imposer_full.py
import io
import tempfile
import os
from reportlab.pdfgen import canvas
from src.imposer import impose_normal, impose_duplex, impose_booklet


def create_test_pdf(num_pages=4):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    for i in range(1, num_pages + 1):
        c.drawString(50, 800, f"Page {i}")
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def test_imposer():
    pdf_bytes = create_test_pdf(4)
    print(f"Original PDF size: {len(pdf_bytes)} bytes")

    # Write PDF bytes to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        # For impose_normal, we expect the same bytes
        normal = impose_normal(tmp_path)
        print(f"Normal imposed size: {len(normal)} bytes")
        assert normal == pdf_bytes, "Normal imposer failed"

        # For duplex, we expect the same number of pages but reordered
        duplex = impose_duplex(tmp_path)
        print(f"Duplex imposed size: {len(duplex)} bytes")
        
        # Verify the duplex PDF has the same number of pages and correct order
        from pypdf import PdfReader
        import io
        duplex_reader = PdfReader(io.BytesIO(duplex))
        assert len(duplex_reader.pages) == 4, "Duplex should have 4 pages"
        # Check page order: Pass 1 Fronts (1, 3), Pass 2 Backs (2, 4)
        extracted = [page.extract_text().strip() for page in duplex_reader.pages]
        assert extracted == ["Page 1", "Page 3", "Page 2", "Page 4"], f"Wrong duplex order: {extracted}"

        # For booklet, we expect a PDF that is not empty
        booklet = impose_booklet(tmp_path)
        print(f"Booklet imposed size: {len(booklet)} bytes")
        assert len(booklet) > 0, "Booklet imposer returned empty PDF"
        
        # Verify booklet has 2 pages (2 sheets = 2 pages in output)
        booklet_reader = PdfReader(io.BytesIO(booklet))
        assert len(booklet_reader.pages) == 2, "Booklet should have 2 pages (sheets)"

        print("All imposer tests passed.")
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    test_imposer()