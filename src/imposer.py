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
    Non-targeted pages are preserved as pristine vector pages.
    If page_indices is None, invert all pages.
    """
    from PyQt6.QtCore import QSize, QBuffer, QIODevice
    from PyQt6.QtGui import QImage, QPainter, QColor
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

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    pages_to_invert = set(range(page_count)) if page_indices is None else set(page_indices)
    dpi = 200.0
    scale = dpi / 72.0

    for i in range(page_count):
        if i not in pages_to_invert:
            # Preserve original vector page directly
            if i < len(reader.pages):
                writer.add_page(reader.pages[i])
        else:
            psize = doc.pagePointSize(i)
            pw = float(psize.width()) if psize.width() > 0 else (float(reader.pages[i].mediabox.width) if i < len(reader.pages) else 595.0)
            ph = float(psize.height()) if psize.height() > 0 else (float(reader.pages[i].mediabox.height) if i < len(reader.pages) else 842.0)
            w = max(1, int(round(pw * scale)))
            h = max(1, int(round(ph * scale)))

            bg_img = QImage(QSize(w, h), QImage.Format.Format_ARGB32)
            bg_img.fill(QColor("#ffffff"))
            painter = QPainter(bg_img)
            qimg = doc.render(i, QSize(w, h))
            painter.drawImage(0, 0, qimg)
            painter.end()

            bg_img.invertPixels(QImage.InvertMode.InvertRgb)

            bits = bg_img.bits().asstring(bg_img.sizeInBytes())
            pil_img = Image.frombuffer(
                "RGBA", (w, h), bits, "raw", "BGRA", 0, 1
            ).convert("RGB")

            img_buf = io.BytesIO()
            pil_img.save(img_buf, format="PDF", resolution=dpi)
            img_buf.seek(0)
            inv_reader = PdfReader(img_buf)
            writer.add_page(inv_reader.pages[0])

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _stamp_page_numbers(
    pdf_bytes: bytes,
    position: str = "Bottom Right",
    page_numbers: Optional[List[str]] = None,
) -> bytes:
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
        
        text = page_numbers[i] if (page_numbers and i < len(page_numbers)) else str(i + 1)
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

def _prepare_input_reader(
    input_path: str,
    invert: Union[bool, Set[int]] = False,
    print_page_numbers: bool = False,
    page_number_pos: str = "Bottom Right",
) -> PdfReader:
    """Read input PDF, applying per-page inversion and optional page numbers to input pages."""
    with open(input_path, "rb") as f:
        data = f.read()

    if invert:
        if isinstance(invert, set):
            if invert:
                data = _invert_pdf_bytes(data, page_indices=invert)
        else:
            data = _invert_pdf_bytes(data)

    if print_page_numbers:
        data = _stamp_page_numbers(data, position=page_number_pos)

    return PdfReader(io.BytesIO(data))


def impose_normal(
    input_path: str,
    invert: Union[bool, Set[int]] = False,
    print_page_numbers: bool = False,
    page_number_pos: str = "Bottom Right",
) -> bytes:
    """Return a 1-up PDF copy of the input document, optionally inverted and with page numbers."""
    with open(input_path, "rb") as f:
        data = f.read()

    if invert:
        if isinstance(invert, set):
            if invert:
                data = _invert_pdf_bytes(data, page_indices=invert)
        else:
            data = _invert_pdf_bytes(data)

    if print_page_numbers:
        data = _stamp_page_numbers(data, position=page_number_pos)

    return data


def get_duplex_passes(
    input_path: str,
    reverse_backs: bool = False,
    invert: Union[bool, Set[int]] = False,
    print_page_numbers: bool = False,
    page_number_pos: str = "Bottom Right",
) -> Tuple[bytes, bytes]:
    """
    Split document into two distinct print streams for manual duplex:
    - Pass 1 (Fronts): Pages 1, 3, 5, 7... (0-indexed: 0, 2, 4, 6...)
    - Pass 2 (Backs): Pages 2, 4, 6, 8... (0-indexed: 1, 3, 5, 7...)
    If reverse_backs is True, Pass 2 page order is inverted for face-up output trays.
    Page numbers are stamped on input pages before splitting so that front and back
    form a continuous combined sequence matching the selected pages.
    """
    reader = _prepare_input_reader(
        input_path,
        invert=invert,
        print_page_numbers=print_page_numbers,
        page_number_pos=page_number_pos,
    )
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

    return data_front, data_back


def impose_duplex_combined(
    input_path: str,
    reverse_backs: bool = False,
    invert: Union[bool, Set[int]] = False,
    print_page_numbers: bool = False,
    page_number_pos: str = "Bottom Right",
) -> bytes:
    """Return a single PDF with Pass 1 (Fronts) followed by Pass 2 (Backs)."""
    front_bytes, back_bytes = get_duplex_passes(
        input_path,
        reverse_backs=reverse_backs,
        invert=invert,
        print_page_numbers=print_page_numbers,
        page_number_pos=page_number_pos,
    )
    r_front = PdfReader(io.BytesIO(front_bytes))
    r_back = PdfReader(io.BytesIO(back_bytes))

    writer = PdfWriter()
    for page in r_front.pages:
        writer.add_page(page)
    for page in r_back.pages:
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def impose_duplex(
    input_path: str,
    invert: Union[bool, Set[int]] = False,
    print_page_numbers: bool = False,
    page_number_pos: str = "Bottom Right",
) -> bytes:
    """Alias for backwards compatibility: returns combined duplex PDF."""
    return impose_duplex_combined(
        input_path,
        reverse_backs=False,
        invert=invert,
        print_page_numbers=print_page_numbers,
        page_number_pos=page_number_pos,
    )


def get_booklet_passes(
    input_path: str,
    reverse_backs: bool = False,
    invert: Union[bool, Set[int]] = False,
    presentation_mode: bool = False,
    print_page_numbers: bool = False,
    page_number_pos: str = "Bottom Right",
) -> Tuple[bytes, bytes]:
    """
    Generate two separate print streams for manual duplex booklet printing:
    - Pass 1: All Front sides of all sheets (Sheet 0 Front, Sheet 1 Front...)
    - Pass 2: All Back sides of all sheets (Sheet 0 Back, Sheet 1 Back...)

    If presentation_mode is True:
    Places 2 slides per sheet stacked Top and Bottom on a portrait sheet (ideal for 16:9/4:3 slides).
    If presentation_mode is False:
    Places 2 pages per sheet side by side on a landscape sheet.
    """
    reader = _prepare_input_reader(
        input_path,
        invert=invert,
        print_page_numbers=print_page_numbers,
        page_number_pos=page_number_pos,
    )
    pages = reader.pages
    n = len(pages)
    if n == 0:
        return b"", b""

    # Determine reference sheet dimensions
    page0 = pages[0]
    pw = float(page0.mediabox.width)
    ph = float(page0.mediabox.height)

    sheet_count = math.ceil(n / 4)
    total_booklet_pages = sheet_count * 4

    writer_front = PdfWriter()
    writer_back = PdfWriter()

    if presentation_mode:
        # Portrait sheet with slides stacked Top and Bottom
        if pw >= ph:
            sheet_w = pw
            sheet_h = max(pw * 1.4142, ph * 2.0)
        else:
            sheet_w = pw
            sheet_h = ph * 2.0

        half_h = sheet_h / 2.0
        scale = min(sheet_w / pw, half_h / ph)

        def place_dual_pages(writer: PdfWriter, top_idx: Optional[int], bottom_idx: Optional[int]):
            new_page = writer.add_blank_page(width=sheet_w, height=sheet_h)
            # Top page (y in [half_h, sheet_h])
            if top_idx is not None and 0 <= top_idx < n:
                tx = (sheet_w - pw * scale) / 2.0
                ty = half_h + (half_h - ph * scale) / 2.0
                t = Transformation().scale(scale, scale).translate(tx=tx, ty=ty)
                new_page.merge_transformed_page(pages[top_idx], t)
            # Bottom page (y in [0, half_h])
            if bottom_idx is not None and 0 <= bottom_idx < n:
                tx = (sheet_w - pw * scale) / 2.0
                ty = (half_h - ph * scale) / 2.0
                t = Transformation().scale(scale, scale).translate(tx=tx, ty=ty)
                new_page.merge_transformed_page(pages[bottom_idx], t)

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

    else:
        # Standard side-by-side booklet on landscape sheet
        if pw <= ph:
            sheet_w = ph * 1.4142
            sheet_h = ph
        else:
            sheet_w = pw * 2
            sheet_h = ph

        half_w = sheet_w / 2.0
        scale = min(half_w / pw, sheet_h / ph)

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

    return data_front, data_back


# Booklet passes alias
impose_booklet_passes = get_booklet_passes


def impose_booklet(
    input_path: str,
    invert: Union[bool, Set[int]] = False,
    presentation_mode: bool = False,
    print_page_numbers: bool = False,
    page_number_pos: str = "Bottom Right",
) -> bytes:
    """
    Generate a complete booklet PDF with interleaved Front and Back sheets:
    Sheet 0 Front, Sheet 0 Back, Sheet 1 Front, Sheet 1 Back...
    Uses uniform proportional 2-up scaling with zero aspect ratio distortion.
    """
    reader = _prepare_input_reader(
        input_path,
        invert=invert,
        print_page_numbers=print_page_numbers,
        page_number_pos=page_number_pos,
    )
    pages = reader.pages
    n = len(pages)
    if n == 0:
        return b""

    page0 = pages[0]
    pw = float(page0.mediabox.width)
    ph = float(page0.mediabox.height)

    sheet_count = math.ceil(n / 4)
    total_booklet_pages = sheet_count * 4

    writer = PdfWriter()

    if presentation_mode:
        if pw >= ph:
            sheet_w = pw
            sheet_h = max(pw * 1.4142, ph * 2.0)
        else:
            sheet_w = pw
            sheet_h = ph * 2.0

        half_h = sheet_h / 2.0
        scale = min(sheet_w / pw, half_h / ph)

        def place_dual_pages(top_idx: Optional[int], bottom_idx: Optional[int]):
            new_page = writer.add_blank_page(width=sheet_w, height=sheet_h)
            if top_idx is not None and 0 <= top_idx < n:
                tx = (sheet_w - pw * scale) / 2.0
                ty = half_h + (half_h - ph * scale) / 2.0
                t = Transformation().scale(scale, scale).translate(tx=tx, ty=ty)
                new_page.merge_transformed_page(pages[top_idx], t)
            if bottom_idx is not None and 0 <= bottom_idx < n:
                tx = (sheet_w - pw * scale) / 2.0
                ty = (half_h - ph * scale) / 2.0
                t = Transformation().scale(scale, scale).translate(tx=tx, ty=ty)
                new_page.merge_transformed_page(pages[bottom_idx], t)

        for s in range(sheet_count):
            # Front
            lf = total_booklet_pages - 1 - 2 * s
            rf = 2 * s
            place_dual_pages(lf if lf < n else None, rf if rf < n else None)

            # Back
            lb = 2 * s + 1
            rb = total_booklet_pages - 2 - 2 * s
            place_dual_pages(lb if lb < n else None, rb if rb < n else None)

    else:
        if pw <= ph:
            sheet_w = ph * 1.4142
            sheet_h = ph
        else:
            sheet_w = pw * 2
            sheet_h = ph

        half_w = sheet_w / 2.0
        scale = min(half_w / pw, sheet_h / ph)

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
    return out.getvalue()