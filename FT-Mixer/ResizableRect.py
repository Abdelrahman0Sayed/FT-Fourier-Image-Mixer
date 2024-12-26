import sys
from PyQt5.QtWidgets import (
    QApplication, QLabel, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QVBoxLayout, QMainWindow, QGraphicsItem
)
from PyQt5.QtGui import QPixmap, QPen, QColor
from PyQt5.QtCore import Qt, QRectF

class ResizableRect(QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.handle_size = 8
        self.handles = {
            "top-left": None,
            "top-right": None,
            "bottom-left": None,
            "bottom-right": None
        }
        self.current_handle = None
        self._pen = QPen(Qt.black, 1)
        self._brush = QColor(255, 255, 255, 100)  # Semi-transparent white
        
    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        rect = self.rect()
        
        # Draw resize handles
        handle_size = self.handle_size
        for pos in self.handles.keys():
            self.handles[pos] = self.get_handle_rect(pos, handle_size)
            painter.drawRect(self.handles[pos])
    
    def get_handle_rect(self, pos, size):
        rect = self.rect()
        if pos == "top-left":
            return QRectF(rect.left(), rect.top(), size, size)
        elif pos == "top-right":
            return QRectF(rect.right() - size, rect.top(), size, size)
        elif pos == "bottom-left":
            return QRectF(rect.left(), rect.bottom() - size, size, size)
        elif pos == "bottom-right":
            return QRectF(rect.right() - size, rect.bottom() - size, size, size)
    
    def hoverMoveEvent(self, event):
        cursor = Qt.ArrowCursor
        for pos, handle in self.handles.items():
            if handle.contains(event.pos()):
                if pos in ["top-left", "bottom-right"]:
                    cursor = Qt.SizeFDiagCursor
                elif pos in ["top-right", "bottom-left"]:
                    cursor = Qt.SizeBDiagCursor
                break
        self.setCursor(cursor)
        super().hoverMoveEvent(event)
    
    def mousePressEvent(self, event):
        for pos, handle in self.handles.items():
            if handle.contains(event.pos()):
                self.current_handle = pos
                break
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.current_handle:
            rect = self.rect()
            delta = event.pos() - event.lastPos()
            if self.current_handle == "top-left":
                rect.setTopLeft(rect.topLeft() + delta)
            elif self.current_handle == "top-right":
                rect.setTopRight(rect.topRight() + delta)
            elif self.current_handle == "bottom-left":
                rect.setBottomLeft(rect.bottomLeft() + delta)
            elif self.current_handle == "bottom-right":
                rect.setBottomRight(rect.bottomRight() + delta)
            self.setRect(rect)
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.current_handle = None
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Create main layout
        self.label = QLabel()
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.white)
        self.label.setPixmap(pixmap)
        
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 400, 300)
        
        # Add resizable rectangle
        rect_item = ResizableRect(50, 50, 100, 100)
        rect_item.setPen(QPen(Qt.red, 2))
        rect_item.setBrush(QColor(255, 0, 0, 100))  # Semi-transparent red
        self.scene.addItem(rect_item)
        
        # Add widgets to layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.view)
        
        # Central widget
        central_widget = QLabel()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
