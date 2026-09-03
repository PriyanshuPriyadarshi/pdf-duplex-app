import re

with open('src/imposer.py', 'r') as f:
    content = f.read()

# Add _stamp_page_numbers
stamp_func = '''
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
'''
content = content.replace('def impose_normal(', stamp_func.lstrip())

# Add args to impose_normal
content = content.replace('def impose_normal(pdf_path: str, invert: Union[bool, Set[int]] = False) -> bytes:', 'def impose_normal(pdf_path: str, invert: Union[bool, Set[int]] = False, print_page_numbers: bool = False, page_number_pos: str = "Bottom Right") -> bytes:')

# Add args to get_duplex_passes
content = content.replace('def get_duplex_passes(pdf_path: str, reverse_backs: bool = False, invert: Union[bool, Set[int]] = False) -> Tuple[bytes, bytes]:', 'def get_duplex_passes(pdf_path: str, reverse_backs: bool = False, invert: Union[bool, Set[int]] = False, print_page_numbers: bool = False, page_number_pos: str = "Bottom Right") -> Tuple[bytes, bytes]:')

# Add args to impose_duplex_combined
content = content.replace('def impose_duplex_combined(pdf_path: str, invert: Union[bool, Set[int]] = False) -> bytes:', 'def impose_duplex_combined(pdf_path: str, invert: Union[bool, Set[int]] = False, print_page_numbers: bool = False, page_number_pos: str = "Bottom Right") -> bytes:')

# Add args to get_booklet_passes
content = content.replace('def get_booklet_passes(pdf_path: str, reverse_backs: bool = False, invert: Union[bool, Set[int]] = False) -> Tuple[bytes, bytes]:', 'def get_booklet_passes(pdf_path: str, reverse_backs: bool = False, invert: Union[bool, Set[int]] = False, print_page_numbers: bool = False, page_number_pos: str = "Bottom Right") -> Tuple[bytes, bytes]:')

# Add args to impose_booklet
content = content.replace('def impose_booklet(pdf_path: str, invert: Union[bool, Set[int]] = False) -> bytes:', 'def impose_booklet(pdf_path: str, invert: Union[bool, Set[int]] = False, print_page_numbers: bool = False, page_number_pos: str = "Bottom Right") -> bytes:')

# Inject _stamp_page_numbers in impose_normal
stamp_inject = '''
    with open(pdf_path, "rb") as f:
        data = f.read()

    if print_page_numbers:
        data = _stamp_page_numbers(data, page_number_pos)

    if invert:
'''
content = re.sub(r'\s+with open\(pdf_path, "rb"\) as f:\s+data = f\.read\(\)\s+if invert:', stamp_inject, content)

# Inject _stamp_page_numbers in get_duplex_passes
stamp_inject2 = '''
    with open(pdf_path, "rb") as f:
        data = f.read()

    if print_page_numbers:
        data = _stamp_page_numbers(data, page_number_pos)

    if invert:
'''
content = re.sub(r'\s+with open\(pdf_path, "rb"\) as f:\s+data = f\.read\(\)\s+if invert:', stamp_inject2, content)

# Inject _stamp_page_numbers in get_booklet_passes
stamp_inject3 = '''
    with open(pdf_path, "rb") as f:
        data = f.read()

    if print_page_numbers:
        data = _stamp_page_numbers(data, page_number_pos)

    if invert:
'''
content = re.sub(r'\s+with open\(pdf_path, "rb"\) as f:\s+data = f\.read\(\)\s+if invert:', stamp_inject3, content)

# Note: impose_duplex_combined and impose_booklet just call get_duplex_passes/get_booklet_passes, so we must forward the args.
content = content.replace('p1, p2 = get_duplex_passes(pdf_path, False, invert)', 'p1, p2 = get_duplex_passes(pdf_path, False, invert, print_page_numbers, page_number_pos)')
content = content.replace('p1, p2 = get_booklet_passes(pdf_path, False, invert)', 'p1, p2 = get_booklet_passes(pdf_path, False, invert, print_page_numbers, page_number_pos)')

with open('src/imposer.py', 'w') as f:
    f.write(content)
