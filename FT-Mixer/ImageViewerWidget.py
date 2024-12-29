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
from ImageDisplay import ImageDisplay
import logging
from MixerUI import ModernWindow
from PIL import Image, ImageQt




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
                # We need to change the value of topRight and bottomLeft
                if current_pos.x() >= self.topRight.x() - 30 or current_pos.y() >= self.bottomLeft.y() - 30:
                    return
                self.topLeft = current_pos
                self.topRight = QPoint(self.bottomRight.x(), self.topLeft.y())
                self.bottomLeft = QPoint(self.topLeft.x(), self.bottomRight.y())

            elif self.resizing_edge == "topRight":
                if current_pos.x() <= self.topLeft.x() + 30 or current_pos.y() >= self.bottomRight.y() - 30:
                    return
                
                # We need to change the value of topLeft and bottomRight
                self.topRight = current_pos
                self.topLeft = QPoint(self.bottomLeft.x(), self.topRight.y())
                self.bottomRight = QPoint(self.topRight.x(), self.bottomLeft.y())

            elif self.resizing_edge == "bottomLeft":
                if current_pos.x() >= self.bottomRight.x() - 30 or current_pos.y() <= self.topLeft.y() + 30:
                    return
                # We need to change the value of topLeft and bottomRight
                self.bottomLeft = current_pos
                self.topLeft = QPoint(self.bottomLeft.x(), self.topRight.y())
                self.bottomRight = QPoint(self.topRight.x(), self.bottomLeft.y())

            elif self.resizing_edge == "bottomRight":
                if current_pos.x() <= self.bottomLeft.x() + 30 or current_pos.y() <= self.topRight.y() + 30:
                    return
                # We need to change the value of topRight and bottomLeft
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

                #cv2.resize(grayScaledImage, (column,row))
                #self.unify_images(parent.viewers, parent.minimumSize)
                self.imageData = cv2.resize(self.imageData, (600,600))
            
                return grayScaledImage, self.imageData
            
            return 
        except Exception as e:
            print(f"Error: {e}")



    def unify_images(self, viewers, minimumSize):
        print("Unifying Images")
        for viewer in viewers:
            if viewer.imageData is not None:
                # Resize the image using cv2.resize
                target_row, target_column = minimumSize  # Assuming square resizing
                viewer.imageData = cv2.resize(viewer.imageData, (target_column, target_row))
                print(f"Image resized to: {viewer.imageData.shape}")
                self.imageFourierTransform(viewer.imageData)


    def imageFourierTransform(self, imageData):
        width, height = self.qImage.width() , self.qImage.height()
        ptr = self.qImage.bits()
        ptr.setsize(width * height)
        newImageData = np.frombuffer(ptr , np.uint8).reshape((height, width))
        print(newImageData)

        fftComponents = np.fft.fft2(imageData)
        fftComponentsShifted = np.fft.fftshift(fftComponents)
        self.fftComponents= fftComponents
        # Get Magnitude and Phase
        self.ftMagnitudes = np.abs(self.fftComponents)
        self.ftPhase = np.angle(self.fftComponents)
        # Get the Real and Imaginary parts
        self.ftReal = np.real(self.fftComponents)
        self.ftImaginary = np.imag(self.fftComponents)


    def displayFrequencyComponent(self, PlottedComponent):
        # Chnage all Selectors to the current component
    
        if PlottedComponent == "FT Magnitude":
            # Take the Magnitude as log scale

            #ftMagnitudes = np.fft.fftshift(self.ftMagnitudes)
            ftMagnitudes = self.ftMagnitudes
            ftLog = 15 * np.log(ftMagnitudes)
            ftNormalized = cv2.normalize(ftLog , None , 0, 255 , cv2.NORM_MINMAX).astype(np.uint8)
            
            pil_image = Image.fromarray(np.uint8(ftLog)) 
            qimage = self.convert_from_pil_to_qimage(pil_image)
            qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            label_height = self.ftComponentLabel.height()
            label_width = self.ftComponentLabel.width()
            
            pixmap = pixmap.scaled(300, 300, Qt.IgnoreAspectRatio)
            self.magnitudeImage = pixmap
            self.ftComponentLabel.setPixmap(pixmap)
            

        elif PlottedComponent == "FT Phase":
            # Ensure phase is within -pi to pi range and Ajdust for visualization (between 0 - 255)
            #ftPhases = np.fft.fftshift(self.ftPhase)
            ftPhases = self.ftPhase

            f_wrapped = np.angle(np.exp(1j * ftPhases))  
            f_normalized = (f_wrapped + np.pi) / (2 * np.pi) * 255
            
            pil_image = Image.fromarray(np.uint8(f_normalized)) 
            qimage = self.convert_from_pil_to_qimage(pil_image)
            qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            label_height = self.ftComponentLabel.height()
            label_width = self.ftComponentLabel.width()
            
            pixmap = pixmap.scaled(300, 300, Qt.IgnoreAspectRatio)
            self.phaseImage = pixmap
            
            self.ftComponentLabel.setPixmap(pixmap)
        
        elif PlottedComponent == "FT Real":
            
            # Normalization and Adjustment for visualization
            
            #ftReals = np.fft.fftshift(self.ftReal)
            ftReals = self.ftReal
            ftNormalized = np.abs(ftReals)
            
            pil_image = Image.fromarray(np.uint8(ftNormalized)) 
            qimage = self.convert_from_pil_to_qimage(pil_image)
            qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            label_height = self.ftComponentLabel.height()
            label_width = self.ftComponentLabel.width()
            
            pixmap = pixmap.scaled(300, 300, Qt.IgnoreAspectRatio)
            self.realImage = pixmap
            
            self.ftComponentLabel.setPixmap(pixmap)
        
        elif PlottedComponent == "FT Imaginary":
            
            #ftImaginaries = np.fft.fftshift(self.ftImaginary)
            ftImaginaries = self.ftImaginary
            ftNormalized = np.abs(ftImaginaries)
            
            
            pil_image = Image.fromarray(np.uint8(ftNormalized)) 
            qimage = self.convert_from_pil_to_qimage(pil_image)
            
            qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimage)
            label_height = self.ftComponentLabel.height()
            label_width = self.ftComponentLabel.width()
            
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


    def convert_data_to_image(self, imageData):
        try:
            # Convert the image data to a QImage
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
                scaled_size.toSize(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

  
  
