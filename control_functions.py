from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QPainter
from PIL import Image, ImageQt
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt, QRect, QTimer,  QEvent
import numpy as np
from scipy.fft import fft2, fftshift
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


def draw_rectangle(self, viewers, rect_size, region):
    if region == "Inner":
        for viewer in viewers:
            if viewer.imageData is not None:
                pixmapType = viewer.component_selector.currentText()
                if pixmapType == "FT Magnitude":
                    original_pixmap = viewer.magnitudeImage 

                elif pixmapType == "FT Phase":
                    original_pixmap = viewer.imageWidget.phaseImage

                elif pixmapType == "FT Real":
                    original_pixmap = viewer.imageWidget.realImage

                elif pixmapType == "FT Imaginary":
                    original_pixmap = viewer.imageWidget.imaginaryImage

                if original_pixmap is None:
                    continue 
                new_pixmap = original_pixmap.copy() 

                painter = QPainter(new_pixmap)

                painter.setOpacity(0.2) 
                painter.setBrush(QColor(0, 0, 0, 128))  # Black with alpha 128 (out of 255)

                self.rectSize = int(rect_size)
                startPoint = int(150 - (rect_size / 2))
                inner_rect = QRect(startPoint, startPoint, rect_size, rect_size)
                painter.drawRect(inner_rect)

                # Draw the outer region with higher opacity
                painter.setOpacity(0.8) 
                painter.setBrush(QColor(0, 0, 0, 230))  # Black with alpha 230 (out of 255)

                # Create a path for the outer region with a hole in the middle
                path = QPainterPath()
                path.addRect(QRectF(new_pixmap.rect()))  # Convert QRect to QRectF
                path.addRect(QRectF(inner_rect))  # Convert QRect to QRectF
                painter.setClipPath(path)

                painter.drawRect(new_pixmap.rect())
                painter.end()

                viewer.ftComponentLabel.setPixmap(new_pixmap)

    else:
        # Draw the brush inside the rectangle
        for viewer in viewers:
            if viewer.imageData is not None:
                pixmapType = viewer.component_selector.currentText()
                if pixmapType == "FT Magnitude":
                    original_pixmap = viewer.magnitudeImage 

                elif pixmapType == "FT Phase":
                    original_pixmap = viewer.imageWidget.phaseImage

                elif pixmapType == "FT Real":
                    original_pixmap = viewer.imageWidget.realImage

                elif pixmapType == "FT Imaginary":
                    original_pixmap = viewer.imageWidget.imaginaryImage

                
                if original_pixmap is None:
                    continue 
                new_pixmap = original_pixmap.copy() 
                
                painter = QPainter(new_pixmap)

                painter.setOpacity(0.8) 
                painter.setBrush(QColor(0, 0, 0, 128))  # Red with alpha 128 (out of 255)


                self.rectSize = int(rect_size)
                startPoint = int(150 - (rect_size / 2))
                painter.drawRect(QRect(startPoint, startPoint, rect_size, rect_size))
                painter.end()
                
                viewer.ftComponentLabel.setPixmap(new_pixmap)



def clear_rectangle(self, viewers):
    for viewer in viewers:
        pixmapType = viewer.component_selector.currentText()
        if pixmapType == "FT Magnitude":
            original_pixmap = viewer.magnitudeImage 

        elif pixmapType == "FT Phase":
            original_pixmap = viewer.imageWidget.phaseImage

        elif pixmapType == "FT Real":
            original_pixmap = viewer.imageWidget.realImage

        elif pixmapType == "FT Imaginary":
            original_pixmap = viewer.imageWidget.imaginaryImage

        if original_pixmap is None:
            continue 

        new_pixmap = original_pixmap.copy() 
        self.region_size.setValue(0)
        viewer.ftComponentLabel.setPixmap(new_pixmap)