from io import BytesIO
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMenu, QAction, QToolTip
from functools import partial
from Image_functions import loadImage, imageFourierTransform, displayFrequencyComponent, unify_images , convert_data_to_image, convet_mixed_to_qImage
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtCore, QtGui, QtWidgets
from mixer_functions import mix_magnitude_phase, mix_real_imaginary
from control_functions import draw_rectangle, clear_rectangle
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

class ModernWindow(QMainWindow):
    
    def __init__(self, imageWidget=None , skip_setup_ui=False):
        super().__init__() 
        self.skip_setup_ui = skip_setup_ui  
        self.minimumSize = (0, 0)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.imageWidget = imageWidget
        self.viewers = []
        self.rectSize = 0

    

        self.outputViewers = []

        print(self.skip_setup_ui)
        if not skip_setup_ui:
            print("Let's Call Function")
            self.buildUI()

        self._setup_theme()
        self.oldPos = None
        self.controller = None
        self._setup_shortcuts()
        #self._setup_statusbar()
        self._setup_menus()
        
        self.undo_stack = []
        self.redo_stack = []

        self.is_mixing = False
        self.mix_timer = QTimer()
        self.mix_timer.setSingleShot(True)
        self.mix_timer.timeout.connect(self._perform_real_time_mix)

    def _perform_real_time_mix(self):
        if self.is_mixing:
            return
            
        try:
            self.is_mixing = True
            self.mix_button.setEnabled(False)
            # self.mix_progress.setValue(0)
            # self.mix_progress.show()
            QApplication.processEvents()  # Force UI update
            
            # Perform mixing
            self.real_time_mix()
            
        finally:
            QTimer.singleShot(500, lambda: self._finish_mixing())  # Delay hiding


    def schedule_real_time_mix(self):
        if not self.is_mixing:
            self.mix_timer.stop()
            self.mix_timer.start(200)  # 200ms debounce

    def real_time_mix(self):
        try:
            output_index = self.output_selector.currentIndex()
            output_viewer = self.outputViewers[output_index]
            if not output_viewer or not output_viewer.originalImageLabel:
                return

            #self.mix_progress.setValue(10)

            # Collect components
            components = []
            for i, viewer in enumerate(self.viewers):
                if viewer and hasattr(viewer, 'fftComponents') and viewer.fftComponents is not None:
                    # ... existing component collection code ...
                    #self.mix_progress.setValue(20 + (i * 15))
                    pass
            if not components:
                return
            #self.mix_progress.setValue(60)
            # Perform mixing
            mix_type = self.mix_type.currentText()
            if mix_type == "Magnitude/Phase":
                result = mix_magnitude_phase(self, components)
            else:
                result = mix_real_imaginary(self, components)

            #self.mix_progress.setValue(80)
            # Process result
            mixed_image = np.fft.ifft2(result)
            mixed_image = np.abs(mixed_image)
            mixed_image = ((mixed_image - mixed_image.min()) * 255 / (mixed_image.max() - mixed_image.min()))
            mixed_image = mixed_image.astype(np.uint8)
            #self.mix_progress.setValue(90)

            # Update display
            qImage = convet_mixed_to_qImage(mixed_image)
            if qImage and output_viewer and output_viewer.originalImageLabel:
                pixmap = QPixmap.fromImage(qImage)
                output_viewer.originalImageLabel.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))

            #self.mix_progress.setValue(100)

        except Exception as e:
            print(f"Error during real-time mixing: {str(e)}")
            if hasattr(self, 'show_error'):
                self.show_error(f"Mixing failed: {str(e)}")
                
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
        self.mix_button.clicked.connect(self.on_mix_button_clicked)

    def _finish_mixing(self):
        self.is_mixing = False
        self.mix_button.setEnabled(True)
        self.mix_progress.hide()

    def on_mix_button_clicked(self):
        try:
            # Show progress bar at start
            #self.mix_progress.setValue(0)
            #self.mix_progress.show()
            self.mix_button.setEnabled(False)
            QApplication.processEvents()
            
            # Initial progress
            #self.mix_progress.setValue(10)
            QApplication.processEvents()
            logging.info("Mixing on progress.")
            # Store strong reference to output viewer
            output_index = self.output_selector.currentIndex()
            output_viewer = self.outputViewers[output_index]
            if not output_viewer or not output_viewer.originalImageLabel:
                self.show_error("Invalid output viewer")
                return
            self.mix_button.setEnabled(False)
            #self.mix_progress.show()
            
            # Collect and validate components
            components = []
            for viewer in self.viewers:
                if viewer and hasattr(viewer, 'fftComponents') and viewer.fftComponents is not None:
                    ftComponents = []
                    if self.rectSize <= 5:
                        ftComponents = viewer.fftComponents
                    else:
                        if self.inner_region.isChecked():
                            data_percentage = self.rectSize / 300

                            # Create zero array same size as shifted input
                            ftComponents = np.zeros_like(viewer.fftComponents)
                            # Calculate region bounds (now centered at image center)
                            center_x = viewer.fftComponents.shape[0] // 2
                            center_y = viewer.fftComponents.shape[1] // 2    
                            region_size = int(300 * data_percentage)

                            print(f"Region size: {region_size}")

                            # Copy only inner region from shifted data, rest remains zero
                            ftComponents[
                                center_x - region_size:center_x + region_size,
                                center_y - region_size:center_y + region_size
                            ] = viewer.fftComponents[
                                center_x - region_size:center_x + region_size,
                                center_y - region_size:center_y + region_size
                            ]

                            print("Original data shape:", viewer.fftComponents.shape)
                            print("Shifted data shape:", ftComponents.shape)
                        
                        else:
                            data_percentage = self.rectSize / 300
                            
                            # Create zero array same size as input
                            ftComponents = np.copy(viewer.fftComponents)

                            # Calculate region bounds
                            center_x = viewer.fftComponents.shape[0] // 2
                            center_y = viewer.fftComponents.shape[1] // 2
                            region_size = int(300 * data_percentage)

                            # Set inner region to zero, keep outer region
                            mask = np.ones_like(ftComponents)
                            mask[
                                center_x - region_size:center_x + region_size,
                                center_y - region_size:center_y + region_size
                            ] = 0

                            # Apply mask to keep only outer region
                            ftComponents = ftComponents * mask

                            print("The Size of the Original Data is: ", viewer.fftComponents.shape)
                            print("The Size of the Data is: ", ftComponents.shape)

                    weight1 = viewer.weight1_slider.value() / 100.0
                    weight2 = viewer.weight2_slider.value() / 100.0

                    components.append({
                        'ft': ftComponents.copy(),
                        'weight1': weight1,
                        'weight2': weight2
                    })
                    print(f"Added component with weights: {weight1}, {weight2} and Size: {viewer.imageData.shape}")
                    
            # Update progress after components collected
            #self.mix_progress.setValue(60)
            QApplication.processEvents()
            if not components:
                self.show_error("Please load images before mixing!")
                return
            # Get mixing type and perform mix
            mix_type = self.mix_type.currentText()
            if mix_type == "Magnitude/Phase":
                print("We Should Apply Magnitude / Phase Mixing")
                result = mix_magnitude_phase(self, components)
                print(result.shape)
            else:
                print("We Should Apply Real / Imaginary Mixing")
                result =  mix_real_imaginary(self, components)
            
            #self.mix_progress.setValue(80)
            QApplication.processEvents()
            # Cause of the data doesn't apply Shifting of zero by default
            #mixed_image = np.fft.ifftshift(result)
            mixed_image = np.fft.ifft2(result)
            mixed_image = np.abs(mixed_image)
            mixed_image = ((mixed_image - mixed_image.min()) * 255 / (mixed_image.max() - mixed_image.min()))
            mixed_image = mixed_image.astype(np.uint8)

            #self.mix_progress.setValue(90)
            QApplication.processEvents()
            qImage = convet_mixed_to_qImage(mixed_image)
            if qImage is None:
                print("Image is None")

            if output_viewer and output_viewer.originalImageLabel:
                pixmap = QPixmap.fromImage(qImage)
                output_viewer.originalImageLabel.setPixmap(pixmap.scaled(300, 300 ,Qt.KeepAspectRatio))
            #self.mix_progress.setValue(100)
            QApplication.processEvents()

        except Exception as e:
            print(f"Error during mixing: {str(e)}")
            self.show_error(f"Mixing failed: {str(e)}")
        finally:
            QTimer.singleShot(500, lambda: self._finish_mixing())


    def real_time_mix(self):
        try:
            # Show progress bar at start
            #self.mix_progress.setValue(0)
            #self.mix_progress.show()
            QApplication.processEvents()

            output_index = self.output_selector.currentIndex()
            output_viewer = self.outputViewers[output_index]
            if not output_viewer or not output_viewer.originalImageLabel:
                return

            # Collect components
            components = []
            for i, viewer in enumerate(self.viewers):
                if viewer and hasattr(viewer, 'fftComponents') and viewer.fftComponents is not None:
                    ftComponents = []
                    if self.rectSize <= 5:
                        ftComponents = viewer.fftComponents
                    else:
                        if self.inner_region.isChecked():
                            data_percentage = self.rectSize / 300
                            ftComponents = np.zeros_like(viewer.fftComponents)
                            center_x = viewer.fftComponents.shape[0] // 2
                            center_y = viewer.fftComponents.shape[1] // 2    
                            region_size = int(300 * data_percentage)
                            ftComponents[
                                center_x - region_size:center_x + region_size,
                                center_y - region_size:center_y + region_size
                            ] = viewer.fftComponents[
                                center_x - region_size:center_x + region_size,
                                center_y - region_size:center_y + region_size
                            ]
                        else:
                            data_percentage = self.rectSize / 300
                            ftComponents = np.copy(viewer.fftComponents)
                            center_x = viewer.fftComponents.shape[0] // 2
                            center_y = viewer.fftComponents.shape[1] // 2
                            region_size = int(300 * data_percentage)
                            mask = np.ones_like(ftComponents)
                            mask[
                                center_x - region_size:center_x + region_size,
                                center_y - region_size:center_y + region_size
                            ] = 0
                            ftComponents = ftComponents * mask

                    weight1 = viewer.weight1_slider.value() / 100.0
                    weight2 = viewer.weight2_slider.value() / 100.0

                    components.append({
                        'ft': ftComponents.copy(),
                        'weight1': weight1,
                        'weight2': weight2
                    })
                    #self.mix_progress.setValue(20 + (i * 15))
                    QApplication.processEvents()

            if not components:
                return

            #self.mix_progress.setValue(60)
            QApplication.processEvents()

            # Get mixing type and perform mix
            mix_type = self.mix_type.currentText()
            if mix_type == "Magnitude/Phase":
                result = mix_magnitude_phase(self, components)
            else:
                result = mix_real_imaginary(self, components)

            #self.mix_progress.setValue(80)
            QApplication.processEvents()

            # Process result
            mixed_image = np.fft.ifft2(result)
            mixed_image = np.abs(mixed_image)
            mixed_image = ((mixed_image - mixed_image.min()) * 255 / (mixed_image.max() - mixed_image.min()))
            mixed_image = mixed_image.astype(np.uint8)

            #self.mix_progress.setValue(90)
            QApplication.processEvents()

            # Update display
            qImage = convet_mixed_to_qImage(mixed_image)
            if qImage and output_viewer and output_viewer.originalImageLabel:
                pixmap = QPixmap.fromImage(qImage)
                output_viewer.originalImageLabel.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))

            #self.mix_progress.setValue(100)
            QApplication.processEvents()

        except Exception as e:
            print(f"Error during real-time mixing: {str(e)}")
            if hasattr(self, 'show_error'):
                self.show_error(f"Mixing failed: {str(e)}")
        finally:
            # Don't hide immediately to show completion
            QTimer.singleShot(500, lambda: self._finish_mixing())
            
    def buildUI(self):
        # Main container
        logging.info("Starting Application.")
        self._ui_initialized = True
        self.container = QWidget()
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Custom title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(32)
        title_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 10, 0)
        title_bar_layout.setSpacing(4)
        title = QLabel("Fourier Transform Mixer")
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 20px;")
        # Window controls
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(4)
        for btn_data in [(" ⚊ ", self.showMinimized), 
                (" ☐ ", self.toggleMaximized),
                ("✕     انطر ابلكاش", self.logExit)]:
            btn = QPushButton(btn_data[0])
            btn.setFixedSize(124, 24)
            btn.clicked.connect(btn_data[1])
            
            # Set object name based on button type
            if btn_data[0] == "✕":
                btn.setObjectName("closeButton")
            else:
                btn.setObjectName("windowControl")
            
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #CCCCCC;
                }
                QPushButton#windowControl:hover {
                    background: #3E3E42;
                    color: white;
                }
                QPushButton#closeButton:hover {
                    background: #E81123;
                    color: white;
                }
            """)
            controls_layout.addWidget(btn)
        title_bar_layout.addWidget(title)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(controls)
        # Main content area
        content = QWidget()
        content_layout = QHBoxLayout(content)  # Changed to horizontal layout
        content_layout.setContentsMargins(10, 10, 10, 10)
        # Left panel for image viewers
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
        # Right panel for output and controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        # Output viewers
        output_group = QGroupBox("Output Viewers")
        output_layout = QVBoxLayout(output_group)
        for i in range(2):
            viewer = ImageViewerWidget(f"Mixer Output {i+1}", is_output=True)
            self.outputViewers.append(viewer)
            output_layout.addWidget(viewer)
        output_group.setLayout(output_layout)  # Set the layout for group box
        # Region selection controls
        region_group = QGroupBox("Region Selection")
        region_layout = QVBoxLayout(region_group)
        region_controls = QWidget()
        region_controls_layout = QHBoxLayout(region_controls)
        self.inner_region = QRadioButton("Inner")
        self.outer_region = QRadioButton("Outer")
        self.inner_region.setChecked(True)
        self.inner_region.clicked.connect(lambda: self.changeRegion("Inner"))
        self.outer_region.clicked.connect(lambda: self.changeRegion("Outer"))
        self.region = "Inner"
        self.region_size = QSlider(Qt.Horizontal)
        self.region_size.setRange(1, 300)
        self.region_size.setValue(0)
        self.region_size.setSingleStep(5)  # Set the step size to 5
        self.region_size.valueChanged.connect(lambda: draw_rectangle(self, self.viewers, self.region_size.value() , self.region))
        self.region_size.setToolTip("Adjust the size of selected region")
        self.deselect_btn = QPushButton("Clear Selection")
        self.deselect_btn.clicked.connect(lambda: clear_rectangle(self, self.viewers))
        region_controls_layout.addWidget(self.inner_region)
        region_controls_layout.addWidget(self.outer_region)
        region_controls_layout.addWidget(self.region_size)
        region_controls_layout.addWidget(self.deselect_btn)
        region_layout.addWidget(region_controls)
        # Add to right panel
        right_layout.addWidget(output_group)
        right_layout.addWidget(region_group)
        right_layout.addStretch()
        # Add panels to main content
        content_layout.addWidget(left_panel, stretch=60)  # 60% width
        content_layout.addWidget(right_panel, stretch=40)  # 40% width
        # Add content to main layout
        layout.addWidget(title_bar)
        layout.addWidget(content)
        # Component mixing controls
        mixing_type_group = QGroupBox("Mixing Type")
        mixing_type_layout = QVBoxLayout(mixing_type_group)
        self.mix_type = QComboBox()
        self.mix_type.addItems(["Magnitude/Phase", "Real/Imaginary"])
        self.mix_type.currentIndexChanged.connect(self.update_mixing_mode)
        # Output selector
        output_selector_layout = QHBoxLayout()
        output_label = QLabel("Mix to Output:")
        self.output_selector = QComboBox()
        self.output_selector.addItems(["Output 1", "Output 2"])
        output_selector_layout.addWidget(output_label)
        output_selector_layout.addWidget(self.output_selector)
        # Add widgets to layout
        mixing_type_layout.addWidget(self.mix_type)
        mixing_type_layout.addLayout(output_selector_layout)
        right_layout.addWidget(mixing_type_group)
        self.region_size.valueChanged.connect(self._on_region_size_changed)
        # Mixing controls
        mixing_group = QGroupBox("Mixing Controls")
        mixing_layout = QHBoxLayout(mixing_group)
        mix_controls = QWidget()
        mix_controls_layout = QVBoxLayout(mix_controls)
        mix_controls_layout.setContentsMargins(5, 5, 5, 5)
        mix_controls_layout.setSpacing(8)  # Add spacing between elements
        # Add mix button and progress bar
        self.mix_button = QPushButton("Start Mix")
        self.mix_button.setMinimumWidth(100)
        self.mix_button.setFixedHeight(30)  # Set fixed height for button
        # Create the custom progress bar
        self.mix_progress = QProgressBar()
        self.mix_progress.setMinimum(0)
        self.mix_progress.setMaximum(100)
        self.mix_progress.setValue(0)
        self.mix_progress.setTextVisible(True)
        self.mix_progress.setFixedHeight(8)  # Adjusted height
        self.mix_progress.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 {COLORS['primary']},
                                            stop:1 {COLORS['info']});
                border-radius: 3px;
            }}
        """)
        self.mix_progress.hide()
        # Add a button to start loading
        self.start_button = QPushButton("Start Loading")
        self.start_button.clicked.connect(self.start_loading)
        # Add widgets to layout
        layout.addWidget(self.mix_progress)
        # Timer for controlling progress updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        mix_controls_layout.addWidget(self.mix_button)
        mix_controls_layout.addWidget(self.mix_progress)
        mixing_layout.addWidget(mix_controls)
        # Add to right panel layout
        right_layout.addWidget(mixing_group)
        self.setCentralWidget(self.container)
        self._setup_connection()

    def start_loading(self):
        #self.mix_progress.show()  # Show the progress bar
        #self.mix_progress.setValue(0)  # Reset to 0
        self.timer.start(100)  # Set timer interval in milliseconds (e.g., 100 ms)

    def update_progress(self):
        current_value = self.mix_progress.value()
        if current_value < 100:
            # Increment progress by a smaller value to make it slower
            self.mix_progress.setValue(current_value + 0.01)
        else:
            self.timer.stop()  # Stop timer when complete
            self.mix_progress.setValue(0)  # Optionally reset the bar
            self.mix_progress.hide()  # Optionally hide the bar again

    def logExit(self):
        logging.info("Exiting Application.")
        self.close()

    def _on_region_size_changed(self):
        draw_rectangle(self, self.viewers, self.region_size.value(), self.region)
        self.real_time_mix()

    def changeRegion(self, region):
        self.region = region
        draw_rectangle(self, self.viewers , self.region_size.value() ,self.region)

    def update_mixing_mode(self, index):
        mode = self.mix_type.currentText()
        for viewer in self.viewers:
            viewer.update_weight_labels(mode)
        self.real_time_mix()

    def toggleMaximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = event.globalPos() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None

    def show_error(self, message):
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setText("Error")
        error_dialog.setInformativeText(message)
        error_dialog.setStyleSheet(f"""
            QMessageBox {{
                background: {COLORS['background']};
                color: {COLORS['text']};
            }}
            QPushButton {{
                background: {COLORS['secondary']};
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }}
        """)
        error_dialog.exec_()

    def _setup_shortcuts(self):
        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Ctrl+M"), self, self.showMinimized)
        QShortcut(QKeySequence("F11"), self, self.toggleMaximized)
        QShortcut(QKeySequence("Ctrl+R"), self, self.reset_all)

    def _setup_statusbar(self):
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet(f"""
            QStatusBar {{
                background: {COLORS['surface']};
                color: {COLORS['text']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        self.setCentralWidget(self.container)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def reset_all(self):
        for viewer in self.viewers:
            viewer.reset()
        for output in self.outputViewers:
            output.reset()
        self.statusBar.showMessage("All viewers reset", 3000)

    def _setup_menus(self):
        self.context_menu = QMenu(self)
        # File operations
        #self.context_menu.addAction("Open Image...", self.open_image)
        #self.context_menu.addAction("Save Result...", self.save_result)
        self.context_menu.addSeparator()
        # Edit operations
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        self.context_menu.addAction(undo_action)
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        self.context_menu.addAction(redo_action)

    def contextMenuEvent(self, event):
        self.context_menu.exec_(event.globalPos())

    def undo(self):
        if self.undo_stack:
            state = self.undo_stack.pop()
            self.redo_stack.append(state)
            self.restore_state(state)
            self.statusBar.showMessage("Undo successful", 2000)

    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            self.restore_state(state)
            self.statusBar.showMessage("Redo successful", 2000)
        
class ImageViewerWidget(ModernWindow):
    weightChanged = pyqtSignal(float, str)
    def __init__(self, title, window=None, is_output=False):  
        # Initialize ModernWindow with skip_setup_ui=True
        super().__init__(self, skip_setup_ui=True)
        self.setObjectName("imageViewer")
        self.window = window
        self.is_output = is_output

        # Viewer-specific attributes
        self.imageData = None
        self.qImage = None
        self.magnitudeImage = None
        self.phaseImage = None
        self.realImage = None
        self.imaginaryImage = None
        self._ft_components = None
        self._ft_magnitude = None
        self._ft_phase = None
        self._ft_real = None
        self._ft_imaginary = None
        self.brightness = 0  
        self.contrast = 0
        self.dragging = False
        self.last_mouse_pos = None
        self.last_pos = None
        self.zoom_level = 1.0

        # Call the _setup_ui method specific to ImageViewerWidget
        self.build_ui(title)
        self._setup_animations()


    def build_ui(self, title):
        
        self.container = QWidget()
        layout = QVBoxLayout(self.container)
        self.setCentralWidget(self.container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with title
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title)
        header_layout.addWidget(title_label)
        layout.addWidget(header)

        if self.is_output:
            # Single display for output viewers
            self.originalImageLabel = ImageDisplay()
            self.originalImageLabel.setAlignment(Qt.AlignCenter)
            self.originalImageLabel.setMinimumSize(300, 300)
            self.originalImageLabel.setMaximumSize(300, 300)
            self.originalImageLabel.setStyleSheet("""
                QLabel {
                    background-color: #1e1e1e;
                    border: 1px solid #323232;
                    border-radius: 4px;
                }
            """)
            layout.addWidget(self.originalImageLabel)
            
        else:
            # Dual display for input viewers
            displays_layout = QHBoxLayout()
            original_section = QVBoxLayout()
            original_label = QLabel("Original Image")
            self.originalImageLabel = ImageDisplay()
            self.originalImageLabel.setAlignment(Qt.AlignCenter)
            self.originalImageLabel.setMinimumSize(300, 300)
            self.originalImageLabel.setStyleSheet("""
                QLabel {
                    background-color: #1e1e1e;
                    border: 1px solid #323232;
                    border-radius: 4px;
                }
            """)
            self.originalImageLabel.on_double_click = self.apply_effect  # Connect double-click event
            original_section.addWidget(original_label)
            original_section.addWidget(self.originalImageLabel)
            displays_layout.addLayout(original_section)


            # FT Component section (right)
            ft_section = QVBoxLayout()
            self.component_selector = QComboBox()
            self.component_selector.addItems([
                'FT Magnitude',
                'FT Phase',
                'FT Real',
                'FT Imaginary'
            ])
            self.component_selector.setToolTip("Select which Fourier component to view")
            self.component_selector.currentIndexChanged.connect(lambda: displayFrequencyComponent(self, self.component_selector.currentText()))

            ft_section.addWidget(self.component_selector)

            self.ftComponentLabel = ImageDisplay()
            self.ftComponentLabel.setAlignment(Qt.AlignCenter)
            self.ftComponentLabel.setMinimumSize(300, 300)
            self.ftComponentLabel.setStyleSheet("""
                QLabel {
                    background-color: #1e1e1e;
                    border: 1px solid #323232;
                    border-radius: 4px;
                }
            """)
            ft_label = QLabel("Fourier Transform Component")
            ft_section.addWidget(ft_label)
            ft_section.addWidget(self.ftComponentLabel)
            displays_layout.addLayout(ft_section)
            # Add displays layout to main layout
            layout.addLayout(displays_layout)
            # Add weights section
            self.weights_group = QGroupBox("Component Weights")
            weights_layout = QVBoxLayout(self.weights_group)
            weight_widget = QWidget()
            weight_layout = QHBoxLayout(weight_widget)
            self.weight1_label = QLabel("Magnitude:")
            self.weight2_label = QLabel("Phase:")
            self.weight1_slider = QSlider(Qt.Horizontal)
            self.weight1_slider.setRange(0, 100)
            self.weight1_slider.setValue(100)
            self.weight2_slider = QSlider(Qt.Horizontal)
            self.weight2_slider.setRange(-100, 100)
            self.weight2_slider.setValue(100)
            self.weight1_slider.valueChanged.connect(lambda: self.find_parent_window().schedule_real_time_mix())
            self.weight2_slider.valueChanged.connect(lambda: self.find_parent_window().schedule_real_time_mix())
            weight_layout.addWidget(self.weight1_label)
            weight_layout.addWidget(self.weight1_slider)
            weight_layout.addWidget(self.weight2_label)
            weight_layout.addWidget(self.weight2_slider)
            weights_layout.addWidget(weight_widget)
            layout.addWidget(self.weights_group)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.hide()
        layout.addWidget(self.progress)

    def find_parent_window(self):
        # Get the top-level window
        parent = self.parentWidget()
        while parent:
            if isinstance(parent, ModernWindow) and not isinstance(parent, ImageViewerWidget):
                return parent
            parent = parent.parentWidget()
        return None
    
    def _on_slider_changed(self):
        # Find the parent ModernWindow instance
        parent = self
        while parent and not isinstance(parent, ModernWindow):
            parent = parent.parent()
        if parent:
            # Schedule the real-time mix instead of calling it directly
            parent.schedule_real_time_mix()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.originalImageLabel.underMouse():
            self.dragging = True
            self.last_pos = event.pos()  
    
    def mouseMoveEvent(self, event):
        if self.last_pos is None:
            self.last_pos = event.pos() 
        delta_x = event.pos().x() - self.last_pos.x()
        delta_y = event.pos().y() - self.last_pos.y()
        # Adjust brightness and contrast based on mouse movement
        newImageData = self.adjust_brightness_contrast(delta_y / 100, delta_x / 100)
        # Update last position for the next event
        self.last_pos = event.pos()

        imageFourierTransform(self, newImageData)
        displayFrequencyComponent(self, self.component_selector.currentText())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def adjust_brightness_contrast(self, brightness_delta, contrast_delta):
        # Update brightness and contrast values
        self.brightness = max(min(self.brightness + brightness_delta, 1), -1)
        self.contrast = max(min(self.contrast + contrast_delta, 3), 0.1)

        print(f"Brightness: {self.brightness}, Contrast: {self.contrast}")

        if self.imageData is not None:
            print("Adjusting image brightness and contrast...")

            # Apply contrast and brightness adjustments
            adjusted_image = self.imageData * self.contrast + (self.brightness * 255)
            adjusted_image = np.clip(adjusted_image, 0, 255).astype(np.uint8)

            # Convert NumPy array back to QImage
            height, width, channel = adjusted_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(adjusted_image.data, width, height, bytes_per_line, QImage.Format_RGB888)

            # Convert to grayscale if needed (optional step, remove if not desired)
            q_image = q_image.convertToFormat(QImage.Format_Grayscale8)

            # Update QLabel display
            pixmap_image = QPixmap.fromImage(q_image)
            label_width = self.originalImageLabel.width()
            label_height = self.originalImageLabel.height()
            pixmap_image = pixmap_image.scaled(label_width, label_height, Qt.KeepAspectRatio)
            self.originalImageLabel.setPixmap(pixmap_image)

            return adjusted_image

    def _setup_zoom_controls(self):
        zoom_layout = QHBoxLayout()
        
        zoom_out = QPushButton("-")
        zoom_out.setFixedSize(24, 24)
        zoom_out.clicked.connect(partial(self.adjust_zoom, -0.1))
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        
        zoom_in = QPushButton("+")
        zoom_in.setFixedSize(24, 24)
        zoom_in.clicked.connect(partial(self.adjust_zoom, 0.1))
        
        zoom_layout.addWidget(zoom_out)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(zoom_in)
        
        self.container.layout().addLayout(zoom_layout)

    def apply_effect(self):
        try:            
            self.originalImageLabel.showLoadingSpinner()
            # Load image
            parent = self.find_parent_window()

            self.image, self.imageData = loadImage(self, parent)
            self.qImage = convert_data_to_image(self.imageData)
            if self.qImage is None or self.imageData is None:
                raise Exception("Failed to load image")
            print("Image Loaded")
            logging.info("Loading an Image.")

            
            # Display original image
            pixmapImage = QPixmap.fromImage(self.qImage)
            label_height = int(self.originalImageLabel.height())
            label_width = int(self.originalImageLabel.width())
            pixmapImage = pixmapImage.scaled(
                label_width, label_height,
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio
            )
            self.originalImageLabel.setPixmap(pixmapImage)
            
            imageFourierTransform(self, self.imageData)                
            displayFrequencyComponent(self, "FT Magnitude")
            

        except Exception as e:
            print(f"Error in apply_effect: {str(e)}")
            if hasattr(self.window, 'show_error'):
                self.window.show_error(str(e))
        finally:
            self.originalImageLabel.hideLoadingSpinner()

    def update_weight_labels(self, mode):
        if mode == "Magnitude/Phase":
            self.weight1_label.setText("Magnitude:")
            self.weight2_label.setText("Phase:")
        else:
            self.weight1_label.setText("Real:")
            self.weight2_label.setText("Imaginary:")

    def _setup_animations(self):
        self.highlight_animation = QPropertyAnimation(self, b"styleSheet")
        self.highlight_animation.setDuration(300)
        self.highlight_animation.setEasingCurve(QEasingCurve.InOutQuad)

    def highlight(self):
        self.highlight_animation.setStartValue(f"""
            QFrame#imageViewer {{
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
            }}
        """)
        self.highlight_animation.setEndValue(f"""
            QFrame#imageViewer {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['primary']};
            }}
        """)
        self.highlight_animation.start()

    def reset(self):
        self.image = None
        self.ft_components = None
        self.ft_magnitude = None
        self.ft_phase = None
        self.ft_real = None
        self.ft_imaginary = None
        self.brightness = 0
        self.contrast = 1
        self.originalImageLabel.clear()
        if not self.is_output:
            self.ftComponentLabel.clear()
            self.weight1_slider.setValue(50)
            self.weight2_slider.setValue(50)

    def _setup_zoom_controls(self):
        zoom_layout = QHBoxLayout()
        
        zoom_out = QPushButton("-")
        zoom_out.setFixedSize(24, 24)
        zoom_out.clicked.connect(partial(self.adjust_zoom, -0.1))
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        
        zoom_in = QPushButton("+")
        zoom_in.setFixedSize(24, 24)
        zoom_in.clicked.connect(partial(self.adjust_zoom, 0.1))
        
        zoom_layout.addWidget(zoom_out)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(zoom_in)
        
        self.layout().addLayout(zoom_layout)

    def adjust_zoom(self, delta):
        self.zoom_level = max(0.1, min(5.0, self.zoom_level + delta))
        self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
        self.update_display()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y() / 1200
            self.adjust_zoom(delta)
            event.accept()
        else:
            super().wheelEvent(event)

    def update_display(self):
        if self.image:
            scaled_size = self.image.size() * self.zoom_level
            self.originalImageLabel.setPixmap(self.image.scaled(
                scaled_size.toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

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

class MainController:
    def __init__(self, window):
        self.window = window
        self.current_thread = None
        

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModernWindow()
    window.controller = MainController(window)  # Set controller after window creation
    window.show()
    sys.exit(app.exec_())