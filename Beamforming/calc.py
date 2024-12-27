from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass 
class FieldParameters:
    frequency: float
    wave_number: float
    steering_angle: float

class FieldCalculator:
    def __init__(self, x_field: np.ndarray, y_field: np.ndarray):
        self.x_field = x_field
        self.y_field = y_field
        self.X, self.Y = np.meshgrid(x_field, y_field)

    def calculate_pattern(self, units: List['ArrayUnit']) -> Optional[np.ndarray]:
        if not units:
            return None
            
        viewing_angles = np.linspace(-np.pi/2, np.pi/2, 1000)
        pattern = np.zeros_like(viewing_angles, dtype=np.complex128)
        
        # Get reference wavelength from highest frequency
        highest_freq = max([max(unit.operating_freqs) for unit in units])
        wavelength_ref = 3e8 / (highest_freq * 1e6)  # Convert MHz to meters
        
        for unit in units:
            if not unit.enabled:
                continue
                
            element_x, element_y = unit.calculate_geometry()
            steer_angle = np.radians(unit.steering_angle)
            
            for freq in unit.operating_freqs:
                # Calculate wavelength and wavenumber
                wavelength = 3e8 / (freq * 1e6)
                k = 2 * np.pi / wavelength
                
                # Calculate normalized element spacing
                d_lambda = unit.element_spacing * wavelength_ref
                
                for idx, theta in enumerate(viewing_angles):
                    if unit.geometry_type == "Linear":
                        # Improved phase calculation for linear array
                        phase = k * (
                            element_x * np.sin(theta) + 
                            element_y * np.cos(theta)
                        )
                        # Progressive phase for steering
                        steer_phase = k * element_x * np.sin(steer_angle)
                    else:  # Curved
                        # Improved curved array calculations
                        r = np.sqrt(
                            (element_x * np.sin(theta))**2 + 
                            (element_y * np.cos(theta))**2
                        )
                        phase = k * r
                        
                        r_steer = np.sqrt(
                            (element_x * np.sin(steer_angle))**2 + 
                            (element_y * np.cos(steer_angle))**2
                        )
                        steer_phase = k * r_steer
                        
                    # Add element contributions with proper normalization
                    element_factor = 1.0 / len(element_x)
                    pattern[idx] += np.sum(
                        element_factor * np.exp(1j * (phase - steer_phase))
                    )
                        
        return np.abs(pattern) / len(units)  # Normalize by number of units

    def calculate_interference(self, units: List['ArrayUnit']) -> Optional[np.ndarray]:
        if not units:
            return None
            
        field = np.zeros_like(self.X, dtype=np.complex128)
        highest_freq = max([max(unit.operating_freqs) for unit in units])
        
        for unit in units:
            if not unit.enabled:
                continue
                
            element_x, element_y = unit.calculate_geometry()
            steer_angle = np.radians(unit.steering_angle)
            
            # Calculate array center
            center_x = np.mean(element_x)
            center_y = np.mean(element_y)
            
            # Modified coordinate handling for curved arrays
            if unit.geometry_type == "Curved":
                # Use original coordinates for curved arrays
                X_calc = self.X
                Y_calc = self.Y
            else:
                # Only rotate for linear arrays
                theta = -steer_angle
                X_calc = ((self.X - center_x) * np.cos(theta) - 
                        (self.Y - center_y) * np.sin(theta) + center_x)
                Y_calc = ((self.X - center_x) * np.sin(theta) + 
                        (self.Y - center_y) * np.cos(theta) + center_y)
            
            for freq in unit.operating_freqs:
                norm_freq = freq/highest_freq
                k = 2 * np.pi * norm_freq
                wavelength = 1/freq
                
                # Near/far field transition
                array_length = unit.num_elements * unit.element_spacing
                transition = 2 * array_length**2 / wavelength
                
                for i in range(len(element_x)):
                    distance = np.sqrt((X_calc - element_x[i])**2 + 
                                    (Y_calc - element_y[i])**2)
                    
                    # Phase calculation includes steering for curved arrays
                    if unit.geometry_type == "Curved":
                        phase = k * (distance - element_x[i] * np.sin(steer_angle))
                    else:
                        phase = k * distance
                    
                    # Amplitude including near/far field transition
                    amplitude = np.where(
                        distance < transition,
                        1.0 / (distance + wavelength/10),  # Near field
                        1.0 / np.sqrt(distance + wavelength/10)  # Far field
                    )
                    
                    wave = amplitude * np.sqrt(norm_freq)
                    field += wave * np.exp(1j * phase) * np.clip(distance/transition, 0, 1)
                    
        return np.abs(field)
