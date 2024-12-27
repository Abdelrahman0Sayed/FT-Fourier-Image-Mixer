from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton
from matplotlib import style
import matplotlib as mpl
from matplotlib import rcParams
from beam_style import PLOT_STYLE



class ModernSlider(QWidget):
    """Custom slider widget with enhanced visual styling"""
    valueChanged = pyqtSignal(float)
    
    def __init__(self, minimum, maximum, value, step=0.1, suffix=""):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Create main slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(minimum/step), int(maximum/step))
        self.slider.setValue(int(value/step))
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(int((maximum-minimum)/(10*step)))
        self.step = step
        self.suffix = suffix
        
        # Enhanced value label
        self.value_label = QLabel(f"{value:.1f}{suffix}")
        self.value_label.setFixedWidth(70)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
        """)
        
        # Apply slider styling
        self.slider.setStyleSheet("""
            QSlider {
                height: 30px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #3a3a3a;
                margin: 0 12px;
            }
            QSlider::handle:horizontal {
                background: #2196f3;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #42a5f5;
            }
            QSlider::sub-page:horizontal {
                background: #2196f3;
            }
            QSlider::tick-mark:horizontal {
                color: white;
                background: white;
                width: 1px;
                height: 3px;
            }
        """)
        
        layout.addWidget(self.slider)
        layout.addWidget(self.value_label)
        self.setLayout(layout)
        
        self.slider.valueChanged.connect(self._on_slider_changed)
        
    def _on_slider_changed(self, value):
        actual_value = value * self.step
        self.value_label.setText(f"{actual_value:.1f}{self.suffix}")
        self.value_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #1976d2;
                border: 1px solid #2196f3;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
        """)
        self.valueChanged.emit(actual_value)
        
        # Reset label style after delay
        QTimer.singleShot(200, self._reset_label_style)
        
    def _reset_label_style(self):
        self.value_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
        """)
        
    def value(self):
        return self.slider.value() * self.step
    
    def setValue(self, value):
        self.slider.setValue(int(value/self.step))
        
    def blockSignals(self, block):
        self.slider.blockSignals(block)


class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(35)
        self.setCursor(Qt.PointingHandCursor)
        style.use('dark_background')
        mpl.rcParams.update(PLOT_STYLE)