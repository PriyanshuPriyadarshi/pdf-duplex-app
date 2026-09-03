from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QVariantAnimation, QRectF, Qt
from PyQt6.QtGui import QPainter, QTransform, QColor, QBrush, QPen

class FlipAnimationWidget(QWidget):
    def __init__(self, flip_edge="long", parent=None):
        super().__init__(parent)
        self.flip_edge = flip_edge
        self.setFixedSize(200, 150)
        
        self.angle = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(180.0)
        self.anim.setDuration(2000)
        self.anim.valueChanged.connect(self._on_anim_step)
        self.anim.setLoopCount(-1)  # Infinite
        self.anim.start()

    def _on_anim_step(self, value):
        self.angle = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Draw base printer outline
        painter.setPen(QPen(QColor("#555562"), 2))
        painter.drawRoundedRect(10, h - 30, w - 20, 20, 4, 4)
        
        # Paper dimensions
        pw, ph = 60, 80
        
        # Translate to center of printer
        painter.translate(w / 2, h - 30)
        
        transform = QTransform()
        if self.flip_edge == "short":
            transform.rotate(self.angle, Qt.Axis.XAxis)
        else:
            transform.rotate(self.angle, Qt.Axis.YAxis)
            
        painter.setTransform(transform, True)
        
        # Draw paper
        rect = QRectF(-pw/2, -ph, pw, ph)
        painter.setPen(QPen(QColor("#EEEEEE"), 1))
        
        # Determine if we see front or back based on angle
        if self.angle < 90:
            painter.setBrush(QBrush(QColor("#E64B3D")))
            painter.drawRect(rect)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "1")
        else:
            painter.setBrush(QBrush(QColor("#EEEEEE")))
            painter.drawRect(rect)
            if self.flip_edge == "short":
                painter.scale(1, -1)
                painter.setPen(QPen(QColor("#212126"), 2))
                painter.drawText(QRectF(-pw/2, 0, pw, ph), Qt.AlignmentFlag.AlignCenter, "2")
            else:
                painter.scale(-1, 1)
                painter.setPen(QPen(QColor("#212126"), 2))
                painter.drawText(QRectF(-pw/2, -ph, pw, ph), Qt.AlignmentFlag.AlignCenter, "2")
