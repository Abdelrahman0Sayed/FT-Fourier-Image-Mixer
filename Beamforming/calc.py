
from dataclasses import dataclass
from typing import List, Optional, Tuple
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

    def calculate_array_geometry(self, unit):
        """Calculate element positions based on array geometry."""
        if unit.geometry_type == "Linear":
            x_pos = np.arange(unit.num_elements) * unit.element_spacing
            y_pos = np.zeros_like(x_pos)
        else:  # Curved
            theta = np.linspace(-np.pi/4, np.pi/4, unit.num_elements)
            x_pos = unit.curvature_factor * np.cos(theta)
            y_pos = unit.curvature_factor * np.sin(theta)
        
        return x_pos, y_pos

    def _calculate_far_field_pattern(self, pattern, angles, x_pos, y_pos, k, steering, geom_type):
        """Calculate far-field beam pattern contribution."""
        for i in range(len(x_pos)):
            if geom_type == "Linear":
                phase = k * (x_pos[i] * (np.sin(angles) - np.sin(steering)))
            else:
                phase = k * (x_pos[i] * np.sin(angles) + y_pos[i] * np.cos(angles))
            pattern += np.exp(1j * phase)

    def calculate_pattern(self, units: List['ArrayUnit']) -> Optional[np.ndarray]:
        """Calculate combined beam pattern for all array units."""
        if not units or not any(u.enabled for u in units):
            return None

        # Setup parameters
        viewing_angles = np.linspace(-np.pi/2, np.pi/2, 1000)
        pattern = np.zeros_like(viewing_angles, dtype=np.complex128)
        highest_freq = max([max(u.operating_freqs) for u in units if u.enabled])

        # Process each active unit
        for unit in units:
            if not unit.enabled:
                continue

            # Calculate element positions
            element_x, element_y = self.calculate_array_geometry(unit)
            steering_rad = np.radians(unit.steering_angle)

            # Process each frequency
            unit_pattern = np.zeros_like(viewing_angles, dtype=np.complex128)
            for freq in unit.operating_freqs:
                k = 2 * np.pi * (freq/highest_freq)
                self._calculate_far_field_pattern(
                    unit_pattern, viewing_angles, 
                    element_x, element_y,
                    k, steering_rad, 
                    unit.geometry_type
                )

            # Add position offset phase
            offset_phase = 2 * np.pi * (
                unit.x_pos * np.sin(viewing_angles) + 
                unit.y_pos * np.cos(viewing_angles)
            )
            unit_pattern *= np.exp(1j * offset_phase)
            
            # Combine patterns
            pattern += unit_pattern / len(unit.operating_freqs)

        # Normalize final pattern
        normalized_pattern = np.abs(pattern)
        return normalized_pattern / np.max(normalized_pattern)


    def calculate_interference(self, units: List['ArrayUnit']) -> Optional[np.ndarray]:
        if not units:
            return None
            
        field = np.zeros_like(self.X, dtype=np.complex128)
        highest_freq = self._get_highest_frequency(units)
        
        for unit in units:
            if not unit.enabled:
                continue
                
            self._add_unit_interference(unit, field, highest_freq)
                    
        return np.abs(field)

    def _get_highest_frequency(self, units: List['ArrayUnit']) -> float:
        return max([max(unit.operating_freqs) for unit in units])

    def _add_unit_pattern(self, unit: 'ArrayUnit', pattern: np.ndarray, 
                         viewing_angles: np.ndarray, highest_freq: float) -> None:
        element_x, element_y = unit.calculate_geometry()
        steer_angle = np.radians(unit.steering_angle)
        
        for freq in unit.operating_freqs:
            k = 2 * np.pi / (3e8 / (freq * 1e6))
            element_factor = 1.0 / len(element_x)
            
            for idx, theta in enumerate(viewing_angles):
                phase = self._calculate_phase(unit.geometry_type, element_x, element_y,
                                           k, theta, steer_angle)
                pattern[idx] += np.sum(element_factor * np.exp(1j * phase))

    def _add_unit_interference(self, unit: 'ArrayUnit', field: np.ndarray, 
                             highest_freq: float) -> None:
        element_x, element_y = unit.calculate_geometry()
        center_x, center_y = np.mean(element_x), np.mean(element_y)
        steer_angle = np.radians(unit.steering_angle)
        
        X_calc, Y_calc = self._get_calculation_coordinates(unit.geometry_type, 
                                                         center_x, center_y, steer_angle)
        
        for freq in unit.operating_freqs:
            self._add_frequency_interference(unit, field, freq, highest_freq,
                                          element_x, element_y, X_calc, Y_calc, steer_angle)

    def _calculate_phase(self, geometry_type: str, x: np.ndarray, y: np.ndarray,
                        k: float, theta: float, steer_angle: float) -> np.ndarray:
        if geometry_type == "Linear":
            phase = k * (x * np.sin(theta) + y * np.cos(theta))
            steer_phase = k * x * np.sin(steer_angle)
        else:
            r = np.sqrt((x * np.sin(theta))**2 + (y * np.cos(theta))**2)
            r_steer = np.sqrt((x * np.sin(steer_angle))**2 + (y * np.cos(steer_angle))**2)
            phase = k * r
            steer_phase = k * r_steer
        return phase - steer_phase

    def _get_calculation_coordinates(self, geometry_type: str, center_x: float,
                                   center_y: float, steer_angle: float) -> Tuple[np.ndarray, np.ndarray]:
        if geometry_type == "Curved":
            return self.X, self.Y
        else:
            theta = -steer_angle
            X_calc = ((self.X - center_x) * np.cos(theta) - 
                     (self.Y - center_y) * np.sin(theta) + center_x)
            Y_calc = ((self.X - center_x) * np.sin(theta) + 
                     (self.Y - center_y) * np.cos(theta) + center_y)
            return X_calc, Y_calc

    def _add_frequency_interference(self, unit: 'ArrayUnit', field: np.ndarray,
                          freq: float, highest_freq: float, element_x: np.ndarray,
                          element_y: np.ndarray, X_calc: np.ndarray,
                          Y_calc: np.ndarray, steer_angle: float) -> None:
        norm_freq = freq/highest_freq
        k = 2 * np.pi * norm_freq
        wavelength = 1/freq
        
        array_length = unit.num_elements * unit.element_spacing
        transition = 2 * array_length**2 / wavelength
        
        # Frequency-dependent spread factor - higher at lower frequencies
        spread_factor = 1 + (1 - norm_freq) * 2
        
        for i in range(len(element_x)):
            dx = X_calc - element_x[i]
            dy = Y_calc - element_y[i]
            distance = np.sqrt(dx**2 + dy**2)
            
            angle = np.arctan2(dy, dx)
            asymmetric_factor = 1 + 0.2 * np.sin(angle)
            
            if unit.geometry_type == "Curved":
                phase = k * (distance * asymmetric_factor - element_x[i] * np.sin(steer_angle))
            else:
                phase = k * distance * asymmetric_factor
            
            # Modified amplitude with frequency-dependent spread
            amplitude = np.where(distance < transition * spread_factor,
                            1.0 / (distance/spread_factor + wavelength/10),
                            1.0 / np.sqrt(distance/spread_factor + wavelength/10))
            
            wave = amplitude * np.sqrt(norm_freq)
            field += wave * np.exp(1j * phase) * np.clip(distance/transition, 0, 1)