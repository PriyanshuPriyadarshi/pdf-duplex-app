import re

with open('src/center_preview.py', 'r') as f:
    content = f.read()

# Add panning state to __init__
init_patch = '''
        self._doc = None
        self._fit_mode = "width"
        self._inverted_pages = set()
        
        # Panning state
        self._panning = False
        self._last_mouse_pos = None

        self._setup_ui()
'''
content = re.sub(r'self\._doc = None\s+self\._fit_mode = "width"\s+self\._inverted_pages = set\(\)\s+self\._setup_ui\(\)', init_patch.strip(), content)

# In _setup_ui, install event filter on viewport and paper_label
setup_patch = '''
        self.scroll_area.viewport().installEventFilter(self)
        self.paper_label.installEventFilter(self)

        self._setup_floating_zoom()
'''
content = re.sub(r'self\._setup_floating_zoom\(\)', setup_patch.strip(), content)

# Add eventFilter method right after resizeEvent
filter_patch = '''
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import Qt
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._panning = True
                self._last_mouse_pos = event.globalPosition().toPoint()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                return True
        elif event.type() == QEvent.Type.MouseMove:
            if getattr(self, '_panning', False) and self._last_mouse_pos:
                delta = event.globalPosition().toPoint() - self._last_mouse_pos
                self._last_mouse_pos = event.globalPosition().toPoint()
                
                h_bar = self.scroll_area.horizontalScrollBar()
                v_bar = self.scroll_area.verticalScrollBar()
                
                h_bar.setValue(h_bar.value() - delta.x())
                v_bar.setValue(v_bar.value() - delta.y())
                return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton and getattr(self, '_panning', False):
                self._panning = False
                self.unsetCursor()
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
'''
content = content.replace('def resizeEvent(self, event):', filter_patch.strip())

with open('src/center_preview.py', 'w') as f:
    f.write(content)
