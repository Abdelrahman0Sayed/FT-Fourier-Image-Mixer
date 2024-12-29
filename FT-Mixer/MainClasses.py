from io import BytesIO
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal
import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtGui
from ImageDisplay import ImageDisplay
from PIL import Image
import logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="app.log",  # Log to a file
    filemode="a",  # Append to the file; use "w" for overwriting
)
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
        self.topLeft = QPoint(75, 75)
        self.topRight = QPoint(225, 75)
        self.bottomLeft = QPoint(75, 225)
        self.bottomRight = QPoint(225, 225)    
        self.threshold = QPoint(3, 3)
        self.outputViewers = []
        print(self.skip_setup_ui)
        if not skip_setup_ui:
            print("Let's Call Function")
            self.buildUI()
        self._setup_theme()
        self.oldPos = None
        self.controller = None
        self._setup_shortcuts()
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
            QApplication.processEvents()  # Force UI update
            self.real_time_mix()
        finally:
            QTimer.singleShot(500, lambda: self._finish_mixing())  # Delay hiding

    def schedule_real_time_mix(self):
        if not self.is_mixing:
            self.mix_timer.stop()
            self.mix_timer.start(600)  # 200ms debounce

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

    def _finish_mixing(self):
        self.is_mixing = False
        #self.mix_button.setEnabled(True)
        #self.mix_progress.hide()


    def real_time_mix(self):
        try:
            # Show progress bar at start
            QApplication.processEvents()
            print("Real Time Mixing")
            print(f"Self: {self}")
            # Collect components
            components = []
            print(f"Viewers: {self.viewers}")
            for i, viewer in enumerate(self.viewers):
                print("I Have viewers")
                if viewer and hasattr(viewer, 'fftComponents') and viewer.fftComponents is not None:
                    print("They have fftComponents")
                    ftComponents = []
                    if True:
                        if self.inner_region.isChecked():
                            print("Mixing Ineer Data")
                            data_percentage = self.rectSize / 300
                            # Create zero array same size as shifted input
                            ftComponents = np.zeros_like(viewer.fftComponents)
                            center_x = viewer.fftComponents.shape[0] // 2
                            center_y = viewer.fftComponents.shape[1] // 2 
                            print("Length of x Data")
                            start_x, end_x = center_x , center_x
                            start_y, end_y = center_y , center_y
                            if self.region_size.isChecked():
                                print("We are using ROF")
                                start_x = int(( (150 - self.topLeft.x()) / 150 ) * center_x)  
                                end_x = int(( (self.bottomRight.x() - 150) / 150 ) * center_x)  

                                start_y = int(( (150 - self.topLeft.y()) / 150 ) * center_x)  
                                end_y = int(( (self.bottomRight.y() - 150) / 150 ) * center_x)  

                            # Copy only inner region from shifted data, rest remains zero
                            ftComponents[
                                max(0, center_x - start_x) : min(center_x + end_x , viewer.fftComponents.shape[0]),
                                max(0,center_y - start_y) : min(center_y + end_y , viewer.fftComponents.shape[1]) 
                            ] = viewer.fftComponents[
                                max(0, center_x - start_x) : min(center_x + end_x , viewer.fftComponents.shape[0]),
                                max(0,center_y - start_y) : min(center_y + end_y , viewer.fftComponents.shape[1]) 
                            ]

                        else:
                            data_percentage = self.rectSize / 300  # Calculate the data percentage
                            ftComponents = np.copy(viewer.fftComponents)  # Make a copy of the FFT components
                            center_x = viewer.fftComponents.shape[0] // 2
                            center_y = viewer.fftComponents.shape[1] // 2
                            start_x, end_x = center_x , center_x
                            start_y, end_y = center_y , center_y
                            if self.region_size.isChecked():
                                print("We are using ROF")
                                start_x = int(( (150 - self.topLeft.x()) / 150 ) * center_x)  
                                end_x = int(( (self.bottomRight.x() - 150) / 150 ) * center_x)  

                                start_y = int(( (150 - self.topLeft.y()) / 150 ) * center_x)  
                                end_y = int(( (self.bottomRight.y() - 150) / 150 ) * center_x)  

                            # Zero out the desired region using slicing
                            ftComponents[center_x - start_x: center_x + end_x, 
                                         center_y - start_y: center_y + end_y] = 0

                    weight = viewer.weight1_slider.value() / 100.0
                    components.append({
                        'ft': ftComponents.copy(),
                        'weight': weight,
                        'type': viewer.component_selector.currentText()
                    })
                    #self.mix_progress.setValue(20 + (i * 15))
                    QApplication.processEvents()

            if not components:
                return

            QApplication.processEvents()

            # Get mixing type and perform mix
            mix_type = self.mix_type.currentText()
            if mix_type == "Magnitude/Phase":
                result = self.mix_magnitude_phase(components)
            else:
                result = self.mix_real_imaginary(components)

            #self.mix_progress.setValue(80)
            QApplication.processEvents()

            # Process result
            mixed_image = np.fft.ifft2(result)
            mixed_image = np.abs(mixed_image)
            mixed_image = ((mixed_image - mixed_image.min()) * 255 / (mixed_image.max() - mixed_image.min()))
            mixed_image = mixed_image.astype(np.uint8)

            #self.mix_progress.setValue(90)
            output_index = self.output_selector.currentIndex()
            output_viewer = self.outputViewers[output_index]
            if not output_viewer or not output_viewer.originalImageLabel:
                return
            QApplication.processEvents()

            # Update display
            height, width, channel = mixed_image.shape
            bytesPerLine = 3 * width
            
            # Convert memoryview to bytes
            image_bytes = mixed_image.tobytes()
            
            # Create the QImage
            qImg = QtGui.QImage(image_bytes, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            
            if qImg.isNull():  # Check if the QImage is valid
                print("Error in converting image data to QImage")
            else:
                # Convert to grayscale if needed
                qImg = qImg.rgbSwapped()
                grayscale_qImg = qImg.convertToFormat(QtGui.QImage.Format_Grayscale8)
                qImage =  grayscale_qImg
            
            if qImage and output_viewer and output_viewer.originalImageLabel:
                pixmap = QPixmap.fromImage(qImage)
                output_viewer.originalImageLabel.setPixmap(pixmap.scaled(300, 300, Qt.IgnoreAspectRatio))

            #self.mix_progress.setValue(100)
            QApplication.processEvents()

        except Exception as e:
            print(f"Error during real-time mixing: {str(e)}")
            if hasattr(self, 'show_error'):
                self.show_error(f"Mixing failed: {str(e)}")
        finally:
            # Don't hide immediately to show completion
            QTimer.singleShot(500, lambda: self._finish_mixing())
            

    def mix_magnitude_phase(self, components):

        try:
            print("Start Mixing")
            first_ft = components[0]['ft']
            result = np.zeros_like(first_ft, dtype=complex)
            print(1)
            # Mix magnitudes
            total_magnitude = np.zeros_like(np.abs(first_ft))
            for comp in components:
                weight = comp['weight']
                type = comp['type']
                if type == "FT Magnitude":
                    magnitude = np.abs(comp['ft'])
                else:
                    magnitude = 0
                magnitude = np.abs(comp['ft'])
                total_magnitude += weight * magnitude
            print("Magnitude Done")
            
            print(2)
            # Mix phases
            total_phase = np.zeros_like(np.angle(first_ft))
            for comp in components:
                weight = comp['weight']
                type = comp['type']
                phase = np.angle(comp['ft'])
                if type == "FT Phase":
                    phase = np.angle(comp['ft'])
                else:
                    phase = 0
                total_phase += weight * phase
            print("Phase Done")

            # Combine magnitude and phase
            result = total_magnitude * np.exp(1j * total_phase)
            print("Mixing Done")

            return result
            
        except Exception as e:
            print(f"Error in magnitude/phase mixing: {str(e)}")
            raise


    def mix_real_imaginary(self, components):
        try:
            first_ft = components[0]['ft']
            result = np.zeros_like(first_ft, dtype=complex)
            
            # Mix real parts
            for comp in components:
                weight = comp['weight']
                type = comp['type']
                if type == "FT Real":
                    real = np.real(comp['ft'])
                else:
                    real = 0
                result.real += weight * comp['ft'].real
            
            # Mix imaginary parts
            for comp in components:
                weight = comp['weight']
                type = comp['type']
                if type == "FT Imaginary":
                    imag = np.imag(comp['ft'])
                else:
                    imag = 0
                result.imag += weight * comp['ft'].imag
            
            return result
            
        except Exception as e:
            print(f"Error in real/imaginary mixing: {str(e)}")
            raise



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
                ("✕", self.logExit)]:
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
        # Lets Add a Check Box If user want to select the region of the image
        self.region_size = QCheckBox("ROI")
        self.region_size.setChecked(False)

        self.reset_btn = QPushButton("Reset ROI Dimensions")
        self.reset_btn.clicked.connect(lambda: self.reset_rectangle(self.viewers))
        self.region_size.toggled.connect(lambda: self.clear_rectangle(self.viewers))
        region_controls_layout.addWidget(self.inner_region)
        region_controls_layout.addWidget(self.outer_region)
        region_controls_layout.addWidget(self.region_size)
        region_controls_layout.addWidget(self.reset_btn)
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
        self.output_selector.currentIndexChanged.connect(self.real_time_mix)
        output_selector_layout.addWidget(output_label)
        output_selector_layout.addWidget(self.output_selector)
        # Add widgets to layout
        mixing_type_layout.addWidget(self.mix_type)
        mixing_type_layout.addLayout(output_selector_layout)
        right_layout.addWidget(mixing_type_group)
        # Mixing controls
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
        #mix_controls_layout.addWidget(self.mix_button)
        self.setCentralWidget(self.container)
        self._setup_connection()


    def unify_images(self, minimumSize):
        for viewer in self.viewers:
            imageData = viewer.get_image_data()
            if viewer.imageData is not None:
                # Resize the image using cv2.resize
                target_row, target_column = minimumSize  # Assuming square resizing
                viewer.imageData = cv2.resize(viewer.imageData, (target_column, target_row))
                print(f"Image resized to: {viewer.imageData.shape}")
                self.imageFourierTransform(viewer.imageData)


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

    def reset_rectangle(self, viewers):
        self.topLeft = QPoint(75, 75)
        self.topRight = QPoint(225, 75)
        self.bottomLeft = QPoint(75, 225)
        self.bottomRight = QPoint(225, 225)
        self.threshold = QPoint(3, 3)
        
        for viewer in viewers:
            viewer.topLeft = QPoint(75, 75)
            viewer.topRight = QPoint(225, 75)
            viewer.bottomLeft = QPoint(75, 225)
            viewer.bottomRight = QPoint(225, 225)
            viewer.threshold = QPoint(3, 3)
        self.region_size.setChecked(True)
        self.draw_rectangle(viewers, self.region)
        
    def draw_rectangle(self, viewers, region):
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
                    rectWidth = self.topRight.x() - self.topLeft.x()
                    rectHeight = self.bottomLeft.y() - self.topLeft.y()
                    inner_rect = QRect(self.topLeft.x(), self.topLeft.y(), rectWidth, rectHeight)
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
                    self.drawEdges(painter)
                    painter.end()
                    viewer.ftComponentLabel.setPixmap(new_pixmap)
                    parent = viewer.find_parent_window()

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
                    painter.setOpacity(1) 
                    painter.setBrush(QColor(0, 0, 0, 200))  # Red with alpha 128 (out of 255)

                    rectWidth = self.topRight.x() - self.topLeft.x()
                    rectHeight = self.bottomLeft.y() - self.topLeft.y()
                    painter.drawRect(QRect(self.topLeft.x(), self.topLeft.y(), rectWidth, rectHeight))
                    self.drawEdges(painter)
                    painter.end()
                    viewer.ftComponentLabel.setPixmap(new_pixmap)
                    parent = viewer.find_parent_window()
        parent.schedule_real_time_mix()
    
    def drawEdges(self, painter):
        # let's draw small solid rectangles at the corners of the rectangle
        painter.setOpacity(1)
        # Edges
        topLeft = QPoint(self.topLeft.x() - 5, self.topLeft.y() - 5)
        topRight = QPoint(self.topRight.x() - 5, self.topRight.y() - 5)
        bottomLeft = QPoint(self.bottomLeft.x() - 5, self.bottomLeft.y() - 5)
        bottomRight = QPoint(self.bottomRight.x() - 5, self.bottomRight.y() - 5)
        painter.setBrush(QColor(0, 0, 255, 255))  # Black with alpha 255 (out of 255)
        painter.drawRect(QRect(topLeft.x(), topLeft.y(), 10, 10))
        painter.drawRect(QRect(topRight.x(), topRight.y(), 10, 10))
        painter.drawRect(QRect(bottomLeft.x(), bottomLeft.y(), 10, 10))
        painter.drawRect(QRect(bottomRight.x(), bottomRight.y(), 10, 10))

    def clear_rectangle(self, viewers):
        if not self.region_size.isChecked():
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
                viewer.ftComponentLabel.setPixmap(new_pixmap)
            self.real_time_mix()
        else:
            self.draw_rectangle(viewers, self.region)


    def _on_region_size_changed(self):
        parent = self
        while parent and not isinstance(parent, ModernWindow):
            parent = parent.parent()
        if parent:
            # Schedule the real-time mix instead of calling it directly
            parent.schedule_real_time_mix()

    def changeRegion(self, region):
        self.real_time_mix()
        self.region = region
        if region == "Inner":
            self.outer_region.setChecked(False)
            self.inner_region.setChecked(True)
        else:
            self.inner_region.setChecked(False)
            self.outer_region.setChecked(True)
        
        if self.region_size.isChecked():
            self.draw_rectangle(self.viewers, self.region)
        else:
            self.real_time_mix()
        

    def update_mixing_mode(self, index):
        try:
            mode = self.mix_type.currentText()
            components = ['FT Magnitude', 'FT Phase'] if mode == "Magnitude/Phase" else ['FT Real', 'FT Imaginary']
            
            for viewer in self.viewers:
                # Skip viewers without image data
                if not hasattr(viewer, 'imageData') or viewer.imageData is None:
                    print(f"Skipping viewer {viewer} - no image data")
                    continue
                    
                # Update component selector
                viewer.component_selector.clear()
                viewer.component_selector.addItems(components)
                
            # Only mix if we have valid data
            if any(hasattr(v, 'imageData') and v.imageData is not None for v in self.viewers):
                self.real_time_mix()
            else:
                print("No valid image data to mix")
                
        except Exception as e:
            print(f"Error updating mixing mode: {str(e)}")
            import traceback
            traceback.print_exc()

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
                color: {COLORS['text']}
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

class MainController:
    def __init__(self, window):
        self.window = window
        self.current_thread = None

class ImageViewerWidget(ModernWindow):
    weightChanged = pyqtSignal(float, str)
    def __init__(self, title, window=None, is_output=False):  
        # Initialize ModernWindow with skip_setup_ui=True
        super().__init__(self, skip_setup_ui=True)
        self.setObjectName("imageViewer")
        self.window = window
        self.is_output = is_output
        self.minimumSize = (0, 0)
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
        self.contrast = 1 
        self.dragging = False
        self.last_mouse_pos = None
        self.last_pos = None
        self.zoom_level = 1.0
        # Viewer-specific attributes
        self.drawing = False
        self.start_point = None
        self.end_point = None
        # Initialize dragging flag and last position
        self.dragging = False
        self.last_pos = None
        self.build_ui(title)

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
                'FT Phase'
            ])
            self.component_selector.setToolTip("Select which Fourier component to view")
            self.component_selector.currentIndexChanged.connect(lambda: self.displayFrequencyComponent(self.component_selector.currentText()))
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
            # Create a QGraphicsView overlay for the label
            ft_section.addWidget(self.ftComponentLabel)
            displays_layout.addLayout(ft_section)
            # Add displays layout to main layout
            layout.addLayout(displays_layout)
            # Add weights section
            self.weights_group = QGroupBox("Component Weights")
            weights_layout = QVBoxLayout(self.weights_group)
            weight_widget = QWidget()
            weight_layout = QHBoxLayout(weight_widget)

            self.weight1_slider = QSlider(Qt.Horizontal)
            self.weight1_slider.setRange(0, 100)
            self.weight1_slider.setValue(100)

            self.weight1_slider.valueChanged.connect(lambda: self.find_parent_window().schedule_real_time_mix())
            weight_layout.addWidget(self.weight1_slider)

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


    def _on_slider_changed(self):
        # Find the parent ModernWindow instance
        parent = self
        while parent and not isinstance(parent, ModernWindow):
            parent = parent.parent()
        if parent:
            # Schedule the real-time mix instead of calling it directly
            parent.schedule_real_time_mix()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.originalImageLabel.underMouse():
                self.dragging = True
                self.last_pos = event.pos()
                # No need to check for edges when adjusting brightness, just drag to adjust
            elif self.ftComponentLabel.underMouse():
                # Now we need to get the position of the mouse relative to the image that he is clicked on , if the position at one of the edges of the rectangle, we need to resize the rectangle
                print("You trying to adjust the rectangle")
                self.dragging = True
                # I need to current Position depending the self.ftComponentLabel not the ImageViewerWidget
                global_pos = event.globalPos()
                self.last_pos = self.ftComponentLabel.mapFromGlobal(global_pos)
                print("The Last Position is: ", self.last_pos)
                self.resizing_edge = None
                # I want to check the position of the mouse relative to the edges of the rectangle with a threshold of 3 pixels
                margin = 10
                if  (self.last_pos.x() - self.topLeft.x() ) <= margin and ( self.last_pos.y() - self.topLeft.y() ) <= margin:
                    self.resizing_edge = "topLeft"
                elif (self.last_pos.x() - self.topRight.x()) <= margin and (self.last_pos.y() - self.topRight.y()) <= margin:
                    self.resizing_edge = "topRight"
                
                elif (self.last_pos.x() - self.bottomLeft.x()) <= margin and (self.last_pos.y() - self.bottomLeft.y()) <= margin:
                    self.resizing_edge = "bottomLeft"
                
                elif (self.last_pos.x() - self.bottomRight.x()) <= margin and (self.last_pos.y() - self.bottomRight.y()) <= margin:
                    self.resizing_edge = "bottomRight"
                
                print("The Resizing Edge is: ", self.resizing_edge)
                self.resizeRectangle()
                
    def mouseMoveEvent(self, event):
        if self.dragging:
            if self.originalImageLabel.underMouse():
                if self.last_pos is None:
                    self.last_pos = event.pos()
                delta_x = event.pos().x() - self.last_pos.x()
                delta_y = event.pos().y() - self.last_pos.y()
                # Adjust brightness and contrast based on mouse movement
                newImageData = self.adjust_brightness_contrast(delta_x / 10, delta_y / 10)
                # Update last position for the next event
                self.last_pos = event.pos()
                # Process the adjusted image
                self.imageFourierTransform(newImageData)
                self.displayFrequencyComponent(self.component_selector.currentText())

            elif self.ftComponentLabel.underMouse():
                parent = self.find_parent_window()
                self.resizeRectangle()
                    

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing_edge = None

    def adjust_brightness_contrast(self, delta_x, delta_y):
        brightness_step = 0.2
        contrast_step = 0.2
        # X for contrast, Y for brightness
        self.brightness = np.clip(self.brightness + delta_y * brightness_step, -50, 200)
        self.contrast = np.clip(self.contrast + delta_x * contrast_step, 0.5, 2)
        print(f"Brightness: {self.brightness}, Contrast: {self.contrast}")
        if self.imageData is not None:
            print("Adjusting image brightness and contrast...")
            # Apply contrast and brightness adjustments
            adjusted_image = cv2.convertScaleAbs(self.imageData, alpha=self.contrast, beta=self.brightness)
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
            pixmap_image = pixmap_image.scaled(300, 300, Qt.IgnoreAspectRatio)
            self.originalImageLabel.setPixmap(pixmap_image)
            return adjusted_image

    def resizeRectangle(self):
        if self.resizing_edge is not None:
            # Get the current position of the mouse
            # Get the current Position
            global_pos = QCursor.pos()
            current_pos = self.ftComponentLabel.mapFromGlobal(global_pos)
            if self.resizing_edge == "topLeft":
                if current_pos.x() >= self.topRight.x() - 30 or current_pos.y() >= self.bottomLeft.y() - 30:
                    return
                self.topLeft = current_pos
                self.topRight = QPoint(self.bottomRight.x(), self.topLeft.y())
                self.bottomLeft = QPoint(self.topLeft.x(), self.bottomRight.y())

            elif self.resizing_edge == "topRight":
                if current_pos.x() <= self.topLeft.x() + 30 or current_pos.y() >= self.bottomRight.y() - 30:
                    return
                self.topRight = current_pos
                self.topLeft = QPoint(self.bottomLeft.x(), self.topRight.y())
                self.bottomRight = QPoint(self.topRight.x(), self.bottomLeft.y())

            elif self.resizing_edge == "bottomLeft":
                if current_pos.x() >= self.bottomRight.x() - 30 or current_pos.y() <= self.topLeft.y() + 30:
                    return
                self.bottomLeft = current_pos
                self.topLeft = QPoint(self.bottomLeft.x(), self.topRight.y())
                self.bottomRight = QPoint(self.topRight.x(), self.bottomLeft.y())

            elif self.resizing_edge == "bottomRight":
                if current_pos.x() <= self.bottomLeft.x() + 30 or current_pos.y() <= self.topRight.y() + 30:
                    return
                self.bottomRight = current_pos
                self.topRight = QPoint(self.bottomRight.x(), self.topLeft.y())
                self.bottomLeft = QPoint(self.topLeft.x(), self.bottomRight.y())
            
            parent = self.find_parent_window()
            parent.topLeft= self.topLeft
            parent.topRight = self.topRight
            parent.bottomLeft = self.bottomLeft
            parent.bottomRight = self.bottomRight
            self.draw_rectangle(parent.viewers, parent.region)

    def loadImage(self, parent):
        try:
            filePath, _ = QFileDialog.getOpenFileName(None, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
            if filePath:
                # Load the image
                self.imageData = cv2.imread(filePath)
                
                # Convert to grayscale
                grayScaledImage = cv2.cvtColor(self.imageData, cv2.COLOR_BGR2GRAY)
                
                row, column = grayScaledImage.shape
                print(row, column)
                print(parent.minimumSize)
                
                # This means that's the first image 
                if parent.minimumSize == (0, 0):
                    parent.minimumSize = (row, column)

                if parent.minimumSize >= (row, column) and (row, column) != (0, 0):
                    parent.minimumSize = (row, column)
                    print(parent.minimumSize)

                parent = self.find_parent_window()
                #cv2.resize(grayScaledImage, (column,row))F
                #parent.unify_images(parent.minimumSize)

                self.imageData = cv2.resize(self.imageData, (600,600))
                return grayScaledImage, self.imageData
            
            return 
        except Exception as e:
            print(f"Error: {e}")

    # ------------------------------------------------------------- Getters and Setters ------------------------------------------------------------ #
    def get_component_data(self, component):
        if component == "magnitude":
            return self.ftMagnitudes
        elif component == "phase":
            return self.ftPhase
        elif component == "real":
            return self.ftReal
        else:
            return self.ftImaginary
        
    def set_component_data(self, component, value):
        if component == "magnitude":
            self.ftMagnitudes = value
        elif component == "phase":
            self.ftPhase = value
        elif component == "real":
            self.ftReal = value
        else:
            self.ftImaginary = value

    def find_parent_window(self):
        # Get the top-level window
        parent = self.parentWidget()
        while parent:
            if isinstance(parent, ModernWindow) and not isinstance(parent, ImageViewerWidget):
                return parent
            parent = parent.parentWidget()
        return None
    
    def get_image_data(self):
        return self.imageData

    # ------------------------------------------------------------- Frequency Label Functions ------------------------------------------------------ #
    def imageFourierTransform(self, imageData):
        fftComponents = np.fft.fft2(imageData)
        fftComponentsShifted = np.fft.fftshift(fftComponents)
        self.fftComponents= fftComponents
        self.set_component_data("magnitude", np.abs(self.fftComponents))
        self.set_component_data("phase" , np.angle(self.fftComponents))
        self.set_component_data("real", np.real(self.fftComponents))
        self.set_component_data("imaginary", np.imag(self.fftComponents))

    def displayFrequencyComponent(self, PlottedComponent):    
        if PlottedComponent == "FT Magnitude":
            # Take the Magnitude as log scale
            #ftMagnitudes = np.fft.fftshift(self.ftMagnitudes)
            ftMagnitudes = self.get_component_data("magnitude")
            ftLog = 15 * np.log(ftMagnitudes)
            ftNormalized = cv2.normalize(ftLog , None , 0, 255 , cv2.NORM_MINMAX).astype(np.uint8)
            pil_image = Image.fromarray(np.uint8(ftLog)) 
            qimage = self.convert_from_pil_to_qimage(pil_image)
            qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            pixmap = pixmap.scaled(300, 300, Qt.IgnoreAspectRatio)
            self.magnitudeImage = pixmap
            self.ftComponentLabel.setPixmap(pixmap)
        elif PlottedComponent == "FT Phase":
            # Ensure phase is within -pi to pi range and Ajdust for visualization (between 0 - 255)
            #ftPhases = np.fft.fftshift(self.ftPhase)
            ftPhases = self.get_component_data("phase")
            f_wrapped = np.angle(np.exp(1j * ftPhases))  
            f_normalized = (f_wrapped + np.pi) / (2 * np.pi) * 255
            pil_image = Image.fromarray(np.uint8(f_normalized)) 
            qimage = self.convert_from_pil_to_qimage(pil_image)
            qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            pixmap = pixmap.scaled(300, 300, Qt.IgnoreAspectRatio)
            self.phaseImage = pixmap
            self.ftComponentLabel.setPixmap(pixmap)
        elif PlottedComponent == "FT Real":
            # Normalization and Adjustment for visualization
            #ftReals = np.fft.fftshift(self.ftReal)
            ftReals = self.get_component_data("real")
            ftNormalized = np.abs(ftReals)
            pil_image = Image.fromarray(np.uint8(ftNormalized)) 
            qimage = self.convert_from_pil_to_qimage(pil_image)
            qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            pixmap = pixmap.scaled(300, 300, Qt.IgnoreAspectRatio)
            self.realImage = pixmap
            self.ftComponentLabel.setPixmap(pixmap)
        elif PlottedComponent == "FT Imaginary":
            #ftImaginaries = np.fft.fftshift(self.ftImaginary)
            ftImaginaries = self.get_component_data("imaginary")
            ftNormalized = np.abs(ftImaginaries)
            pil_image = Image.fromarray(np.uint8(ftNormalized)) 
            qimage = self.convert_from_pil_to_qimage(pil_image)
            qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            pixmap = pixmap.scaled(300, 300, Qt.IgnoreAspectRatio)
            self.imaginaryImage = pixmap
            self.ftComponentLabel.setPixmap(pixmap)

        parent = self.find_parent_window()
        parent.real_time_mix()
        if parent.region_size.isChecked():
            parent.draw_rectangle( parent.viewers ,parent.region)

    def convert_from_pil_to_qimage(self, pilImage):
            img_data = pilImage.tobytes()
            qimage = QImage(img_data, pilImage.width, pilImage.height, pilImage.width * 3, QImage.Format_RGB888)
            return qimage

    def convert_data_to_image(self, imageData):
        try:
            height, width, channel = imageData.shape
            bytesPerLine = 3 * width
            qImg = QtGui.QImage(imageData.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            if qImg is None:
                print("Error in converting image data to QImage")
            qImg = qImg.rgbSwapped()
            grayscale_qImg = qImg.convertToFormat(QtGui.QImage.Format_Grayscale8)
            return grayscale_qImg
        except Exception as e:
            print(e)

    def apply_effect(self):
        try:            
            self.originalImageLabel.showLoadingSpinner()
            # Load image
            parent = self.find_parent_window()
            print("My Parent is ", parent)
            self.image, self.imageData = self.loadImage(parent)
            self.qImage = self.convert_data_to_image(self.imageData)
            if self.qImage is None or self.imageData is None:
                raise Exception("Failed to load image")
            print("Image Loaded")
            logging.info("Loading an Image.")
            # Display original image
            pixmapImage = QPixmap.fromImage(self.qImage)
            label_height = int(self.originalImageLabel.height())
            label_width = int(self.originalImageLabel.width())
            print(label_height, label_width)
            pixmapImage = pixmapImage.scaled(
                label_width, label_height,
                aspectRatioMode=Qt.AspectRatioMode.IgnoreAspectRatio
            )
            self.originalImageLabel.setPixmap(pixmapImage)
            self.imageFourierTransform(self.imageData)                
            self.displayFrequencyComponent("FT Magnitude")
            parent.real_time_mix()

        except Exception as e:
            print(f"Error in apply_effect: {str(e)}")
            if hasattr(self.window, 'show_error'):
                self.window.show_error(str(e))
        finally:
            self.originalImageLabel.hideLoadingSpinner()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModernWindow()
    window.controller = MainController(window)  # Set controller after window creation
    window.show()
    sys.exit(app.exec_())
