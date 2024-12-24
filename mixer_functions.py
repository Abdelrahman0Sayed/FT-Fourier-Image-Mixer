import numpy as np
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Done by ModernWindow
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


def get_rectangle_data(self):
    pass