from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QPen, QCursor
from PyQt5.QtCore import Qt, QRectF

class ResizableRect(QGraphicsRectItem):
    # Flags to handle selection and interaction with the rectangle
    TopLeft = 0
    TopRight = 1
    BottomLeft = 2
    BottomRight = 3
    Top = 4
    Bottom = 5
    Left = 6
    Right = 7

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.setFlags(QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemIsMovable)
        self.setPen(QPen(Qt.red, 2))
        self.setBrush(Qt.transparent)
        self.resizing = None  # To track which corner/edge is being resized

    def mousePressEvent(self, event):
        """Detects which part of the rectangle is being clicked for resizing."""
        rect = self.rect()
        cursor_pos = event.pos()

        # Check for corner selection
        if rect.topLeft().x() - 10 < cursor_pos.x() < rect.topLeft().x() + 10 and \
           rect.topLeft().y() - 10 < cursor_pos.y() < rect.topLeft().y() + 10:
            self.resizing = self.TopLeft
        elif rect.topRight().x() - 10 < cursor_pos.x() < rect.topRight().x() + 10 and \
             rect.topRight().y() - 10 < cursor_pos.y() < rect.topRight().y() + 10:
            self.resizing = self.TopRight
        elif rect.bottomLeft().x() - 10 < cursor_pos.x() < rect.bottomLeft().x() + 10 and \
             rect.bottomLeft().y() - 10 < cursor_pos.y() < rect.bottomLeft().y() + 10:
            self.resizing = self.BottomLeft
        elif rect.bottomRight().x() - 10 < cursor_pos.x() < rect.bottomRight().x() + 10 and \
             rect.bottomRight().y() - 10 < cursor_pos.y() < rect.bottomRight().y() + 10:
            self.resizing = self.BottomRight
        # Check for edge selection
        elif rect.top() - 10 < cursor_pos.y() < rect.top() + 10:
            self.resizing = self.Top
        elif rect.bottom() - 10 < cursor_pos.y() < rect.bottom() + 10:
            self.resizing = self.Bottom
        elif rect.left() - 10 < cursor_pos.x() < rect.left() + 10:
            self.resizing = self.Left
        elif rect.right() - 10 < cursor_pos.x() < rect.right() + 10:
            self.resizing = self.Right
        else:
            self.resizing = None  # No resizing

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handles the mouse dragging to resize the rectangle."""
        if self.resizing is not None:
            rect = self.rect()
            delta = event.pos() - event.lastPos()

            if self.resizing == self.TopLeft:
                rect.setTopLeft(rect.topLeft() + delta.toPoint())
            elif self.resizing == self.TopRight:
                rect.setTopRight(rect.topRight() + delta.toPoint())
            elif self.resizing == self.BottomLeft:
                rect.setBottomLeft(rect.bottomLeft() + delta.toPoint())
            elif self.resizing == self.BottomRight:
                rect.setBottomRight(rect.bottomRight() + delta.toPoint())
            elif self.resizing == self.Top:
                rect.setTop(rect.top() + delta.y())
            elif self.resizing == self.Bottom:
                rect.setBottom(rect.bottom() + delta.y())
            elif self.resizing == self.Left:
                rect.setLeft(rect.left() + delta.x())
            elif self.resizing == self.Right:
                rect.setRight(rect.right() + delta.x())

            self.setRect(rect)  # Update the rectangle size

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Reset resizing mode after mouse release."""
        self.resizing = None
        super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget=None):
        """Optional: Customize appearance (highlight edges when hovering over them)."""
        super().paint(painter, option, widget)
        if self.resizing:
            painter.setPen(QPen(Qt.green, 2))
            painter.drawRect(self.rect())
