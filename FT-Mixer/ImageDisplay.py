from io import BytesIO
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMenu, QAction, QToolTip
from functools import partial
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtCore, QtGui, QtWidgets


COLORS = {
    'background': '#1E1E1E',  # Darker background
    'surface': '#252526',     # Slightly lighter surface
    'primary': '#007ACC',     # Keep the blue accent
    'secondary': '#3E3E42',   # Darker secondary
    'text': '#FFFFFF',        # Brighter text
    'border': '#3E3E42',      # Subtler borders
    'hover': '#2D2D30',       # Subtle hover state
    'success': '#4CAF50',
    'warning': '#FFA726',
    'info': '#29B6F6'
}


# Add to COLORS dictionary
COLORS.update({
    'hover': '#404040',
    'success': '#4CAF50', 
    'warning': '#FFA726',
    'info': '#29B6F6'
})



class ImageDisplay(QLabel):
    # Add custom signal
    dragComplete = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setToolTip("Drag & Drop images here\nDrag mouse to adjust brightness/contrast")
        self.loading_spinner = None
        self._setup_loading_spinner()
        self.setAcceptDrops(True)
        self.drop_indicator = QLabel(self)
        self.drop_indicator.hide()
        self._setup_drop_indicator()
        self.last_pos = None
        self.image = None
        self.brightness = 0
        self.contrast = 1

        self.setStyleSheet(f"""
            QLabel {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QLabel:hover {{
                border-color: {COLORS['primary']};
            }}
        """)    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_double_click()

    def on_double_click(self):
        pass

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_pos = None
            # Emit signal when drag is complete
            self.dragComplete.emit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasImage() or event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.hide_drop_indicator()
        if event.mimeData().hasImage():
            self.setPixmap(QPixmap.fromImage(event.mimeData().imageData()))
        elif event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.setPixmap(QPixmap(file_path))
    
    def _setup_loading_spinner(self):
        self.loading_spinner = QProgressIndicator(self)
        self.loading_spinner.hide()
        
    def showLoadingSpinner(self):
        if self.loading_spinner:
            self.loading_spinner.start()
            self.loading_spinner.show()
    
    def hideLoadingSpinner(self):
        if self.loading_spinner:
            self.loading_spinner.stop()
            self.loading_spinner.hide()

    def _setup_drop_indicator(self):
        self.drop_indicator.setStyleSheet(f"""
            QLabel {{
                background: {COLORS['info']};
                color: white;
                padding: 10px;
                border-radius: 5px;
            }}
        """)
        self.drop_indicator.setText("Drop image here")
        self.drop_indicator.setAlignment(Qt.AlignCenter)

    def dragEnterEvent(self, event):
        print("Dragging")
        if event.mimeData().hasImage() or event.mimeData().hasUrls():
            event.accept()
            self.show_drop_indicator()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.hide_drop_indicator()

    def show_drop_indicator(self):
        if self.drop_indicator:
            self.drop_indicator.show()
            # Center the indicator
            self.drop_indicator.move(
                (self.width() - self.drop_indicator.width()) // 2,
                (self.height() - self.drop_indicator.height()) // 2
            )

    def hide_drop_indicator(self):
        if self.drop_indicator:
            self.drop_indicator.hide()




        

# Add a custom loading spinner widget
class QProgressIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(40, 40)

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def start(self):
        self.timer.start(100)

    def stop(self):
        self.timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        
        painter.setPen(QPen(QColor(COLORS['primary']), 3))
        painter.drawArc(-15, -15, 30, 30, 0, 300 * 16)

class InfoButton(QPushButton):
    def __init__(self, tooltip, parent=None):
        super().__init__("ⓘ", parent)
        self.setToolTip(tooltip)
        self.setFixedSize(16, 16)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['info']};
                border-radius: 8px;
                color: white;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary']};
            }}
        """)



# Add custom QSlider with value tooltip
class SliderWithTooltip(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        value = self.value_at_pos(event.pos())
        QToolTip.showText(event.globalPos(), str(value), self)
        super().mouseMoveEvent(event)

    def value_at_pos(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        handle = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)

        if self.orientation() == Qt.Horizontal:
            slider_length = handle.width()
            slider_min = groove.x()
            slider_max = groove.right() - slider_length + 1
            pos = pos.x()
        else:
            slider_length = handle.height()
            slider_min = groove.y()
            slider_max = groove.bottom() - slider_length + 1
            pos = pos.y()

        return QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), pos - slider_min,
            slider_max - slider_min, opt.upsideDown)


