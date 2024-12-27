from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np

@dataclass
class VisualizationData:
    pattern: np.ndarray
    interference: np.ndarray
    array_positions: List[Tuple[float, float]]
    theta: np.ndarray
    x_field: np.ndarray
    y_field: np.ndarray
    steering_angles: List[float]
    show_full_pattern: bool

class VisualizationManager:
    def __init__(self, pattern_plot, interference_plot, array_plot):
        self.pattern_plot = pattern_plot
        self.interference_plot = interference_plot
        self.array_plot = array_plot

    def update_all(self, data: VisualizationData):
        """Update all visualization plots with provided data"""
        # Add validation
        
        if data.pattern is None or data.interference is None or not data.array_positions:
            print("Warning: Missing visualization data")
            return
            
        # Update pattern plot
        self.pattern_plot.update(
            data.theta, 
            data.pattern, 
            data.steering_angles,
            show_full_pattern=data.show_full_pattern  # Pass this parameter
        )
        
        # Update interference plot  
        self.interference_plot.update(
            data.x_field,
            data.y_field,
            data.interference
        )
        
        # Update array geometry plot
        self.array_plot.update(data.array_positions)

    def clear_all(self):
        """Clear all plots"""
        self.pattern_plot.clear()
        self.interference_plot.clear()
        self.array_plot.clear()
