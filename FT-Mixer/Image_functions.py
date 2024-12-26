import cv2
import numpy as np
from scipy.interpolate import CubicSpline
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QSlider
from PyQt5.QtGui import QIcon , QFont, QPixmap, QColor # Package to set an icon , fonts and images
from PyQt5.QtCore import Qt , QTimer  # used for alignments.
from PyQt5.QtWidgets import QLayout , QVBoxLayout , QHBoxLayout, QGridLayout ,QWidget, QFileDialog, QPushButton, QColorDialog, QInputDialog, QComboBox, QDialog, QDoubleSpinBox
import pyqtgraph as pg
import random
import pandas as pd
from scipy.signal import find_peaks
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem
from scipy import signal
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PIL import Image, ImageQt


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
            unify_images(self, parent.viewers, parent.minimumSize)
            #self.imageData = cv2.resize(self.imageData, (600,600))
        
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
            imageFourierTransform(viewer , viewer.imageData)



def convert_data_to_image(imageData):
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




def imageFourierTransform(self, imageData):
    fftComponents = np.fft.fft2(imageData)
    fftComponentsShifted = np.fft.fftshift(fftComponents)
    self.fftComponents= fftComponents
    # Get Magnitude and Phase
    self.ftMagnitudes = np.abs(fftComponents)
    self.ftPhase = np.angle(fftComponents)
    # Get the Real and Imaginary parts
    self.ftReal = np.real(fftComponents)
    self.ftImaginary = np.imag(fftComponents)
    



def displayFrequencyComponent(self, PlottedComponent):
    # Chnage all Selectors to the current component
    for viewer in self.viewers:
        viewer.imageWidget.component_selector.setCurrentText(PlottedComponent)
        
    if PlottedComponent == "FT Magnitude":
        # Take the Magnitude as log scale
        
        
        ftMagnitudes = np.fft.fftshift(self.ftMagnitudes)
        #ftMagnitudes = self.ftMagnitudes
        ftLog = 15 * np.log(ftMagnitudes + 1e-10)
        ftNormalized = (255 * (ftLog / ftLog.max())).astype(np.uint8)
        
        pil_image = Image.fromarray(np.uint8(ftNormalized)) 
        qimage = convert_from_pil_to_qimage(pil_image)
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
        qimage = convert_from_pil_to_qimage(pil_image)
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
        qimage = convert_from_pil_to_qimage(pil_image)
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
        qimage = convert_from_pil_to_qimage(pil_image)
        
        qimage = qimage.convertToFormat(QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        label_height = self.ftComponentLabel.height()
        label_width = self.ftComponentLabel.width()
        
        pixmap = pixmap.scaled(300, 300, Qt.ignoreAspectRatio)
        self.imaginaryImage = pixmap
        self.ftComponentLabel.setPixmap(pixmap)
    
    parent = self.find_parent_window()
    parent.real_time_mix()






def convert_from_pil_to_qimage(pilImage):
        img_data = pilImage.tobytes()
        qimage = QImage(img_data, pilImage.width, pilImage.height, pilImage.width * 3, QImage.Format_RGB888)
        return qimage







def convet_mixed_to_qImage(imageData):
    try:
        # Convert the image data to a QImage    
        height, width, channel = imageData.shape
        bytesPerLine = 3 * width
        
        # Convert memoryview to bytes
        image_bytes = imageData.tobytes()
        
        # Create the QImage
        qImg = QtGui.QImage(image_bytes, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        
        if qImg.isNull():  # Check if the QImage is valid
            print("Error in converting image data to QImage")
        else:
            # Convert to grayscale if needed
            qImg = qImg.rgbSwapped()
            grayscale_qImg = qImg.convertToFormat(QtGui.QImage.Format_Grayscale8)
            return grayscale_qImg
        
    except Exception as e:
        print(e)