# src/imposer.py
import io
from pypdf import PdfReader, PdfWriter, Transformation

def impose_normal(input_path: str) -> bytes:
    """Return a byte-for-byte copy of the input PDF (1-up, same order)."""
    with open(input_path, "rb") as f:
        return f.read()


def impose_duplex(input_path: str) -> bytes:
    """
    Reorder pages for manual duplex printing (long‑edge flip).
    For N pages the order is: 1, N, 2, N‑1, 3, N‑2, …
    Printing all front sides, then flipping the stack, yields correct sequence.
    """
    reader = PdfReader(input_path)
    pages = reader.pages
    n = len(pages)
    order = []
    i, j = 0, n - 1
    while i <= j:
        order.append(i)
        if i != j:
            order.append(j)
        i += 1
        j -= 1
    writer = PdfWriter()
    for idx in order:
        writer.add_page(pages[idx])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def impose_booklet(input_path: str) -> bytes:
    """
    Booklet imposition: 2 pages per sheet (half size each), then duplex order.
    Assumes all pages are the same size and portrait orientation.
    Output is ready for duplex printing (flip after first side).
    """
    reader = PdfReader(input_path)
    pages = reader.pages
    n = len(pages)
    if n == 0:
        return b""
    # Determine page size from first page
    page0 = pages[0]
    width = float(page0.mediabox.width)
    height = float(page0.mediabox.height)
    # We'll create landscape sheets where each half is width/2, height
    sheet_width = width  # each half will be width/2, so total width = width
    sheet_height = height
    # We'll scale each page to half width, keep height
    scale_x = 0.5
    scale_y = 1.0
    # Build list of page indices for booklet ordering
    # For booklet, we need to arrange pages so that when printed double-sided and folded,
    # the sequence is correct. We'll use the classic algorithm:
    # Let sheet_count = ceil(n/4)
    # For each sheet i (0-indexed), we have four positions:
    #   left_front, right_front, left_back, right_back
    # We'll compute the actual page numbers for each position.
    import math
    sheet_count = math.ceil(n / 4)
    # Create a list that will hold page indices for each sheet side in the order they will be printed
    # We'll produce a list of lists: for each sheet, [left_front_idx, right_front_idx, left_back_idx, right_back_idx]
    # If a position is beyond n-1, we use None (blank page).
    sheets = []
    for sheet in range(sheet_count):
        # Base page numbers for this sheet (0-indexed)
        base = sheet * 4
        left_front = base + 0
        right_front = base + 1
        left_back = base + 2
        right_back = base + 3
        # Convert to actual page index, but note that booklet ordering is not linear.
        # We'll use the classic booklet arrangement:
        # For a booklet of N pages, the pages are arranged as:
        #   For each sheet from outside to inside:
        #     left_front = N - sheet*2
        #     right_front = sheet*2 + 1
        #     left_back = sheet*2 + 2
        #     right_back = N - sheet*2 - 1
        # This is for 1-indexed pages. We'll adapt to 0-indexed.
        # Let's implement using 0-indexed:
        lf = n - 1 - sheet * 2
        rf = sheet * 2
        lb = sheet * 2 + 1
        rb = n - 2 - sheet * 2
        # Ensure indices are within [0, n-1]; if not, set to None
        def idx_or_none(i):
            return i if 0 <= i < n else None
        lf_idx = idx_or_none(lf)
        rf_idx = idx_or_none(rf)
        lb_idx = idx_or_none(lb)
        rb_idx = idx_or_none(rb)
        sheets.append((lf_idx, rf_idx, lb_idx, rb_idx))
    # Now we need to create the PDF: for each sheet we create a landscape page
    # and place two pages (if present) side by side, each scaled to half width.
    writer = PdfWriter()
    for lf_idx, rf_idx, lb_idx, rb_idx in sheets:
        # Front side
        front_page = writer.add_blank_page(width=sheet_width, height=sheet_height)
        if lf_idx is not None:
            # Place left page
            transformation = Transformation().scale(scale_x, scale_y).translate(tx=0, ty=0)
            front_page.merge_transformed_page(pages[lf_idx], transformation)
        if rf_idx is not None:
            # Place right page at x = width/2
            transformation = Transformation().scale(scale_x, scale_y).translate(tx=width/2, ty=0)
            front_page.merge_transformed_page(pages[rf_idx], transformation)
        # Back side
        back_page = writer.add_blank_page(width=sheet_width, height=sheet_height)
        if lb_idx is not None:
            transformation = Transformation().scale(scale_x, scale_y).translate(tx=0, ty=0)
            back_page.merge_transformed_page(pages[lb_idx], transformation)
        if rb_idx is not None:
            transformation = Transformation().scale(scale_x, scale_y).translate(tx=width/2, ty=0)
            back_page.merge_transformed_page(pages[rb_idx], transformation)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def invert_page(page):
    """
    Placeholder for page inversion.
    To be implemented via rasterization (Pillow) or PDF transformation.
    """
    # For now, return the page unchanged.
    return page