import re

with open('src/center_preview.py', 'r') as f:
    content = f.read()

# Add to __init__
init_patch = '''
        self._inverted_pages = set()
        self._print_page_numbers = False
        self._page_number_pos = "Bottom Right"
        
        # Panning state
'''
content = content.replace('self._inverted_pages = set()\n        \n        # Panning state', init_patch.lstrip())

# Add method
method_patch = '''
    def set_page_number_settings(self, enabled: bool, position: str):
        self._print_page_numbers = enabled
        self._page_number_pos = position

    def set_inverted_pages(self, pages: set):
'''
content = content.replace('    def set_inverted_pages(self, pages: set):', method_patch.lstrip())

# Add drawing to _render_page_image
draw_patch = '''
        painter.end()

        # Draw page number watermark if enabled
        if self._print_page_numbers:
            p = QPainter(qimg)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            text = str(page_idx + 1)
            font = QFont("Helvetica", max(10, int(w * 0.02)), QFont.Weight.Bold)
            p.setFont(font)
            fm = p.fontMetrics()
            
            tw = fm.horizontalAdvance(text)
            th = fm.height()
            
            margin_x = int(w * 0.03)
            margin_y = int(h * 0.03)
            
            if self._page_number_pos == "Bottom Left":
                x = margin_x
                y = h - margin_y
            elif self._page_number_pos == "Bottom Center":
                x = (w - tw) // 2
                y = h - margin_y
            elif self._page_number_pos == "Bottom Right":
                x = w - tw - margin_x
                y = h - margin_y
            elif self._page_number_pos == "Top Left":
                x = margin_x
                y = margin_y + th
            elif self._page_number_pos == "Top Center":
                x = (w - tw) // 2
                y = margin_y + th
            elif self._page_number_pos == "Top Right":
                x = w - tw - margin_x
                y = margin_y + th
            else:
                x = w - tw - margin_x
                y = h - margin_y

            # Draw subtle semi-transparent background for contrast
            from PyQt6.QtGui import QColor, QPainterPath
            path = QPainterPath()
            path.addRoundedRect(x - 6, y - th + 2, tw + 12, th + 4, 4, 4)
            p.fillPath(path, QColor(255, 255, 255, 200))
            
            p.setPen(QColor(0, 0, 0))
            p.drawText(x, y, text)
            p.end()

        if page_idx in self._inverted_pages:
'''
content = content.replace('        painter.end()\n\n        if page_idx in self._inverted_pages:', draw_patch.lstrip())

with open('src/center_preview.py', 'w') as f:
    f.write(content)
