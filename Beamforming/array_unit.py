import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ArrayUnit:
    id: int
    name: str
    x_pos: float
    y_pos: float
    num_elements: int
    element_spacing: float
    steering_angle: float
    geometry_type: str
    curvature_factor: float 
    operating_freqs: List[float]
    enabled: bool = True

    def __post_init__(self):
        """Validate array parameters after initialization"""
        self._validate_parameters()

    def _validate_parameters(self):
        """Validate array unit parameters"""
        if self.num_elements < 1:
            raise ValueError("Number of elements must be positive")
        if self.element_spacing <= 0:
            raise ValueError("Element spacing must be positive")
        if not self.operating_freqs:
            raise ValueError("At least one operating frequency required")
        if self.geometry_type not in ["Linear", "Curved"]:
            raise ValueError("Invalid geometry type")
        if self.curvature_factor <= 0:
            raise ValueError("Curvature factor must be positive")

    def calculate_geometry(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate element positions based on array geometry"""
        if self.geometry_type == "Linear":
            x = (np.arange(self.num_elements) - self.num_elements/2) * self.element_spacing + self.x_pos
            y = np.zeros_like(x) + self.y_pos
        else:  # Curved array
            angle_span = np.pi/3  # 60 degrees default
            radius = self.curvature_factor * self.element_spacing * self.num_elements / 2
            angles = np.linspace(-angle_span/2, angle_span/2, self.num_elements)
            x = radius * np.sin(angles) + self.x_pos
            y = radius * (1 - np.cos(angles)) + self.y_pos
        return x, y

    @property
    def array_length(self) -> float:
        """Calculate total array length"""
        return self.num_elements * self.element_spacing

    @property
    def wavelength(self) -> float:
        """Calculate wavelength for primary frequency"""
        return 1 / self.operating_freqs[0] if self.operating_freqs else 0

    @property
    def phase_shifts(self) -> np.ndarray:
        """Calculate phase shifts for beam steering"""
        x, _ = self.calculate_geometry()
        k = 2 * np.pi / self.wavelength
        return k * x * np.sin(np.radians(self.steering_angle))