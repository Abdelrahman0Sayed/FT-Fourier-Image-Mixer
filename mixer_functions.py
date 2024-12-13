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
            weight = comp['weight1']
            magnitude = np.abs(comp['ft'])
            total_magnitude += weight * magnitude
        print("Magnitude Done")
        print(2)
        # Mix phases
        total_phase = np.zeros_like(np.angle(first_ft))
        for comp in components:
            weight = comp['weight2']
            phase = np.angle(comp['ft'])
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
            weight = comp['weight1']
            result.real += weight * comp['ft'].real
        
        # Mix imaginary parts
        for comp in components:
            weight = comp['weight2']
            result.imag += weight * comp['ft'].imag
        
        return result
        
    except Exception as e:
        print(f"Error in real/imaginary mixing: {str(e)}")
        raise


def get_rectangle_data(self):
    pass