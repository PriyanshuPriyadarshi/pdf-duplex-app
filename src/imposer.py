"""
src/imposer.py - Mathematically rigorous PDF imposition engine for manual duplex and booklet printing.
Provides aspect-ratio preserving 2-up scaling, 4-page signature imposition, and Pass 1 / Pass 2 stream splitting.
"""

import io
import math
from typing import Tuple, Optional, List, Set, Union
from pypdf import PdfReader, PdfWriter, Transformation
from PIL import Image, ImageOps


def _invert_pdf_bytes(pdf_bytes: bytes, page_indices: Optional[Set[int]] = None) -> bytes:
    """Invert colors of a PDF using high-resolution raster inversion.
    If page_indices is provided, only invert pages where page index is in the set.
    If page_indices is None, invert all pages.
    """
    from PyQt6.QtCore import QSize, QBuffer, QIODevice
    from PyQt6.QtGui import QImage, QPainter, QPdfWriter, QPageSize, QPageLayout
    from PyQt6.QtPdf import QPdfDocument

    # Load into QPdfDocument via buffer
    doc = QPdfDocument(None)
    buffer = QBuffer()
    buffer.setData(pdf_bytes)
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    doc.load(buffer)

    page_count = doc.pageCount()
    if page_count == 0:
        return pdf_bytes

    out_stream = io.BytesIO()
    # Use PIL to assemble inverted images into a single PDF
    pil_images = []

    for i in range(page_count):
        # Render at 200 DPI (approx 2.77x 72 DPI)
        psize = doc.pagePointSize(i)
        w, h = int(psize.width() * 2.5), int(psize.height() * 2.5)
        if w <= 0 or h <= 0:
            w, h = 1488, 2105

        qimg = doc.render(i, QSize(w, h))

        # Only invert if this page is targeted
        if page_indices is None or i in page_indices:
            qimg.invertPixels(QImage.InvertMode.InvertRgb)

        # Convert QImage to PIL Image
        bits = qimg.bits().asstring(qimg.sizeInBytes())
        pil_img = Image.frombuffer(
            "RGBA", (qimg.width(), qimg.height()), bits, "raw", "BGRA", 0, 1
        ).convert("RGB")
        pil_images.append(pil_img)

    if pil_images:
        pil_images[0].save(
            out_stream,
            format="PDF",
            save_all=True,
            append_images=pil_images[1:],
            resolution=200.0,
        )
        return out_stream.getvalue()

    return pdf_bytes


def _stamp_page_numbers(pdf_bytes: bytes, position: str) -> bytes:
    """Stamp page numbers onto the physical PDF bytes."""
    try:
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        import io
    except ImportError:
        return pdf_bytes # Fallback if reportlab missing

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for i in range(len(reader.pages)):
        page = reader.pages[i]
        mb = page.mediabox
        pw = float(mb.width)
        ph = float(mb.height)

        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(pw, ph))
        
        text = str(i + 1)
        font_size = max(10, int(pw * 0.02))
        c.setFont("Helvetica-Bold", font_size)
        text_width = c.stringWidth(text, "Helvetica-Bold", font_size)
        
        margin_x = int(pw * 0.03)
        margin_y = int(ph * 0.03)
        
        if position == "Bottom Left":
            x, y = margin_x, margin_y
        elif position == "Bottom Center":
            x, y = (pw - text_width) / 2, margin_y
        elif position == "Bottom Right":
            x, y = pw - text_width - margin_x, margin_y
        elif position == "Top Left":
            x, y = margin_x, ph - margin_y - font_size
        elif position == "Top Center":
            x, y = (pw - text_width) / 2, ph - margin_y - font_size
        elif position == "Top Right":
            x, y = pw - text_width - margin_x, ph - margin_y - font_size
        else:
            x, y = pw - text_width - margin_x, margin_y
            
        c.setFillColorRGB(1, 1, 1, 0.8)
        c.rect(x - 4, y - 4, text_width + 8, font_size + 8, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x, y, text)
        
        c.save()
        packet.seek(0)
        
        overlay_pdf = PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

    out_io = io.BytesIO()
    writer.write(out_io)
    return out_io.getvalue()

def impose_normal(
input_path: str, invert: Union[bool, Set[int]] = False) -> bytes:
    """Return a 1-up PDF copy of the input document, optionally inverted."""
    with open(input_path, "rb") as f:
        data = f.read()

    if invert:
        if isinstance(invert, set):
            data = _invert_pdf_bytes(data, page_indices=invert)
        else:
            data = _invert_pdf_bytes(data)
    return data


def get_duplex_passes(
    input_path: str,
    reverse_backs: bool = False,
    invert: Union[bool, Set[int]] = False,
) -> Tuple[bytes, bytes]:
    """
    Split document into two distinct print streams for manual duplex:
    - Pass 1 (Fronts): Pages 1, 3, 5, 7... (0-indexed: 0, 2, 4, 6...)
    - Pass 2 (Backs): Pages 2, 4, 6, 8... (0-indexed: 1, 3, 5, 7...)
    If reverse_backs is True, Pass 2 page order is inverted for face-up output trays.
    """
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    writer_front = PdfWriter()
    writer_back = PdfWriter()

    # Pass 1: Fronts (Odds)
    for i in range(0, total_pages, 2):
        writer_front.add_page(reader.pages[i])

    # Pass 2: Backs (Evens)
    back_indices = list(range(1, total_pages, 2))
    if reverse_backs:
        back_indices.reverse()

    for i in back_indices:
        writer_back.add_page(reader.pages[i])

    buf_front = io.BytesIO()
    writer_front.write(buf_front)
    data_front = buf_front.getvalue()

    buf_back = io.BytesIO()
    writer_back.write(buf_back)
    data_back = buf_back.getvalue()

    if invert:
        if isinstance(invert, set):
            data_front = _invert_pdf_bytes(data_front, page_indices=invert)
            data_back = _invert_pdf_bytes(data_back, page_indices=invert)
        else:
            data_front = _invert_pdf_bytes(data_front)
            data_back = _invert_pdf_bytes(data_back)

    return data_front, data_back


def impose_duplex_combined(
    input_path: str,
    reverse_backs: bool = False,
    invert: Union[bool, Set[int]] = False,
) -> bytes:
    """Return a single PDF with Pass 1 (Fronts) followed by Pass 2 (Backs)."""
    front_bytes, back_bytes = get_duplex_passes(input_path, reverse_backs, invert=False)
    r_front = PdfReader(io.BytesIO(front_bytes))
    r_back = PdfReader(io.BytesIO(back_bytes))

    writer = PdfWriter()
    for page in r_front.pages:
        writer.add_page(page)
    for page in r_back.pages:
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    data = out.getvalue()

    if invert:
        if isinstance(invert, set):
            data = _invert_pdf_bytes(data, page_indices=invert)
        else:
            data = _invert_pdf_bytes(data)

    return data


def impose_duplex(input_path: str, invert: Union[bool, Set[int]] = False) -> bytes:
    """Alias for backwards compatibility: returns combined duplex PDF."""
    return impose_duplex_combined(input_path, reverse_backs=False, invert=invert)


def get_booklet_passes(
    input_path: str,
    reverse_backs: bool = False,
    invert: Union[bool, Set[int]] = False,
) -> Tuple[bytes, bytes]:
    """
    Generate two separate print streams for manual duplex booklet printing:
    - Pass 1: All Front sides of all sheets (Sheet 0 Front, Sheet 1 Front...)
    - Pass 2: All Back sides of all sheets (Sheet 0 Back, Sheet 1 Back...)
    """
    reader = PdfReader(input_path)
    pages = reader.pages
    n = len(pages)
    if n == 0:
        return b"", b""

    # Determine reference sheet dimensions
    page0 = pages[0]
    pw = float(page0.mediabox.width)
    ph = float(page0.mediabox.height)

    # Landscape sheet: width = 2 * half_width, height = ph (or standard proportional)
    # If portrait (pw <= ph), sheet is landscape with width = ph * 1.414 or 2 * pw
    if pw <= ph:
        sheet_w = ph * 1.4142
        sheet_h = ph
    else:
        sheet_w = pw * 2
        sheet_h = ph

    half_w = sheet_w / 2.0
    scale = min(half_w / pw, sheet_h / ph)

    sheet_count = math.ceil(n / 4)
    total_booklet_pages = sheet_count * 4

    writer_front = PdfWriter()
    writer_back = PdfWriter()

    def place_dual_pages(writer: PdfWriter, left_idx: Optional[int], right_idx: Optional[int]):
        new_page = writer.add_blank_page(width=sheet_w, height=sheet_h)
        # Left page
        if left_idx is not None and 0 <= left_idx < n:
            tx = (half_w - pw * scale) / 2.0
            ty = (sheet_h - ph * scale) / 2.0
            t = Transformation().scale(scale, scale).translate(tx=tx, ty=ty)
            new_page.merge_transformed_page(pages[left_idx], t)
        # Right page
        if right_idx is not None and 0 <= right_idx < n:
            tx = half_w + (half_w - pw * scale) / 2.0
            ty = (sheet_h - ph * scale) / 2.0
            t = Transformation().scale(scale, scale).translate(tx=tx, ty=ty)
            new_page.merge_transformed_page(pages[right_idx], t)

    # Fronts (Pass 1)
    for s in range(sheet_count):
        lf = total_booklet_pages - 1 - 2 * s
        rf = 2 * s
        place_dual_pages(
            writer_front,
            lf if lf < n else None,
            rf if rf < n else None,
        )

    # Backs (Pass 2)
    sheet_order = list(range(sheet_count))
    if reverse_backs:
        sheet_order.reverse()

    for s in sheet_order:
        lb = 2 * s + 1
        rb = total_booklet_pages - 2 - 2 * s
        place_dual_pages(
            writer_back,
            lb if lb < n else None,
            rb if rb < n else None,
        )

    buf_front = io.BytesIO()
    writer_front.write(buf_front)
    data_front = buf_front.getvalue()

    buf_back = io.BytesIO()
    writer_back.write(buf_back)
    data_back = buf_back.getvalue()

    if invert:
        if isinstance(invert, set):
            data_front = _invert_pdf_bytes(data_front, page_indices=invert)
            data_back = _invert_pdf_bytes(data_back, page_indices=invert)
        else:
            data_front = _invert_pdf_bytes(data_front)
            data_back = _invert_pdf_bytes(data_back)

    return data_front, data_back


# Booklet passes alias
impose_booklet_passes = get_booklet_passes


def impose_booklet(input_path: str, invert: Union[bool, Set[int]] = False) -> bytes:
    """
    Generate a complete booklet PDF with interleaved Front and Back sheets:
    Sheet 0 Front, Sheet 0 Back, Sheet 1 Front, Sheet 1 Back...
    Uses uniform proportional 2-up scaling with zero aspect ratio distortion.
    """
    reader = PdfReader(input_path)
    pages = reader.pages
    n = len(pages)
    if n == 0:
        return b""

    page0 = pages[0]
    pw = float(page0.mediabox.width)
    ph = float(page0.mediabox.height)

    if pw <= ph:
        sheet_w = ph * 1.4142
        sheet_h = ph
    else:
        sheet_w = pw * 2
        sheet_h = ph

    half_w = sheet_w / 2.0
    scale = min(half_w / pw, sheet_h / ph)

    sheet_count = math.ceil(n / 4)
    total_booklet_pages = sheet_count * 4

    writer = PdfWriter()

    def place_dual_pages(left_idx: Optional[int], right_idx: Optional[int]):
        new_page = writer.add_blank_page(width=sheet_w, height=sheet_h)
        if left_idx is not None and 0 <= left_idx < n:
            tx = (half_w - pw * scale) / 2.0
            ty = (sheet_h - ph * scale) / 2.0
            t = Transformation().scale(scale, scale).translate(tx=tx, ty=ty)
            new_page.merge_transformed_page(pages[left_idx], t)
        if right_idx is not None and 0 <= right_idx < n:
            tx = half_w + (half_w - pw * scale) / 2.0
            ty = (sheet_h - ph * scale) / 2.0
            t = Transformation().scale(scale, scale).translate(tx=tx, ty=ty)
            new_page.merge_transformed_page(pages[right_idx], t)

    for s in range(sheet_count):
        # Front
        lf = total_booklet_pages - 1 - 2 * s
        rf = 2 * s
        place_dual_pages(lf if lf < n else None, rf if rf < n else None)

        # Back
        lb = 2 * s + 1
        rb = total_booklet_pages - 2 - 2 * s
        place_dual_pages(lb if lb < n else None, rb if rb < n else None)

    out = io.BytesIO()
    writer.write(out)
    data = out.getvalue()

    if invert:
        if isinstance(invert, set):
            data = _invert_pdf_bytes(data, page_indices=invert)
        else:
            data = _invert_pdf_bytes(data)

    return data