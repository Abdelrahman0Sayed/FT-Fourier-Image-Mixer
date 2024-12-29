from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QComboBox, QGroupBox, QGridLayout,
                           QApplication, QMenuBar, QMenu, QAction)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QIcon, QKeySequence
from ImageViewerWidget import ImageViewerWidget
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="app.log",  # Log to a file
    filemode="a",  # Append to the file; use "w" for overwriting
)

# Define color palette
# Define color palette with better contrast and cohesion
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

class BaseUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.oldPos = None
        self.setupUI()

        
    def setupUI(self):
        # Window setup
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title bar
        self.setup_title_bar()
        
        # Content area
        self.setup_content_area()
        
        # Status bar
        self.setup_status_bar()
        
        # Menu bar
        self.setup_menu_bar()
        
        # Shortcuts
        self.setup_shortcuts()
        
        # Theme
        self.setup_theme()
        
    def setup_title_bar(self):
        self.title_bar = QWidget()
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        # Title
        title = QLabel("Fourier Transform Mixer")
        
        # Window controls
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setSpacing(0)
        
        minimize_btn = QPushButton("－")
        maximize_btn = QPushButton("□")
        close_btn = QPushButton("×")
        
        for btn in (minimize_btn, maximize_btn, close_btn):
            controls_layout.addWidget(btn)
            btn.setFixedSize(45, 30)
        
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(controls)
        
        self.main_layout.addWidget(self.title_bar)
        
    def setup_content_area(self):
        self.content = QWidget()
        self.content_layout = QHBoxLayout(self.content)
        self.main_layout.addWidget(self.content)
        
    def setup_status_bar(self):
        self.statusBar().showMessage("Ready")
        
    def setup_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)
        
    def setup_shortcuts(self):
        # Undo/Redo
        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        
    def setup_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background: #323232;
                color: #ffffff;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background: #404040;
            }
        """)

    def buildUI(self):
        self.setup_title_bar()
        # Main layout setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        
        # Content layout
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel setup
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Image viewers grid
        viewers_grid = QGridLayout()
        viewers_grid.setSpacing(10)
        for i in range(4):
            viewer = ImageViewerWidget('', is_output=False)
            self.viewers.append(viewer)
            viewers_grid.addWidget(viewer, i // 2, i % 2)
            
        left_layout.addLayout(viewers_grid)
        
        # Right panel setup
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Output viewers
        output_group = QGroupBox("Output Viewers")
        output_layout = QVBoxLayout(output_group)
        for i in range(2):
            viewer = ImageViewerWidget(f"Output {i+1}", is_output=True)
            self.outputViewers.append(viewer)
            output_layout.addWidget(viewer)
            
        right_layout.addWidget(output_group)
        
        # Region controls
        self.setup_region_controls(right_layout)
        
        # Mix controls
        self.setup_mix_controls(right_layout)
        
        # Layout assembly
        content_layout.addWidget(left_panel, stretch=2)
        content_layout.addWidget(right_panel, stretch=1)
        main_layout.addWidget(content)
        
    def setup_region_controls(self, parent_layout):
        region_group = QGroupBox("Region Selection")
        region_layout = QVBoxLayout(region_group)
        
        # Region size checkbox
        self.region_size = QCheckBox("Enable Region Selection")
        region_layout.addWidget(self.region_size)
        
        # Region size controls
        size_widget = QWidget()
        size_layout = QGridLayout(size_widget)
        
        self.region_width = QSpinBox()
        self.region_height = QSpinBox()
        for spinbox in [self.region_width, self.region_height]:
            spinbox.setRange(1, 1000)
            spinbox.setValue(100)
            
        size_layout.addWidget(QLabel("Width:"), 0, 0)
        size_layout.addWidget(self.region_width, 0, 1)
        size_layout.addWidget(QLabel("Height:"), 1, 0)
        size_layout.addWidget(self.region_height, 1, 1)
        
        region_layout.addWidget(size_widget)
        parent_layout.addWidget(region_group)
        
    def setup_mix_controls(self, parent_layout):
        mix_group = QGroupBox("Mixing Controls")
        mix_layout = QVBoxLayout(mix_group)
        
        # Mix type selector
        self.mix_type = QComboBox()
        self.mix_type.addItems(["Magnitude/Phase", "Real/Imaginary"])
        mix_layout.addWidget(self.mix_type)
        
        # Mix button
        self.mix_button = QPushButton("Mix Components")
        mix_layout.addWidget(self.mix_button)
        
        parent_layout.addWidget(mix_group)
    
    def _setup_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {COLORS['background']};
            }}
            
            QWidget#container {{
                background: {COLORS['background']};
            }}
            
            QWidget {{
                background: {COLORS['background']};
                color: {COLORS['text']};
            }}
            
            QGroupBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: {COLORS['primary']};
            }}
            
            QPushButton {{
                background: {COLORS['secondary']};
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                color: {COLORS['text']};
            }}
            
            QPushButton:hover {{
                background: {COLORS['primary']};
            }}
            
            QComboBox {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 120px;
            }}
            
            QComboBox:hover {{
                border-color: {COLORS['primary']};
            }}
            
            QSlider::groove:horizontal {{
                background: {COLORS['surface']};
                height: 4px;
                border-radius: 2px;
            }}
            
            QSlider::handle:horizontal {{
                background: {COLORS['primary']};
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            
            QLabel#imageDisplay {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            
            QProgressBar {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                height: 6px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background: {COLORS['primary']};
                border-radius: 2px;
            }}
        """)

    def _setup_connection(self):
        print("Setting up connections")
        # Use direct method connection instead of lambda
        #self.mix_button.clicked.connect(self.on_mix_button_clicked)