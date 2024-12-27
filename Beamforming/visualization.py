from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np

@dataclass
class VisualizationData:
    # Pattern plot data
    pattern: Optional[np.ndarray] = None
    interference: Optional[np.ndarray] = None
    array_positions: List[Tuple[float, float]] = None
    theta: Optional[np.ndarray] = None
    x_field: Optional[np.ndarray] = None 
    y_field: Optional[np.ndarray] = None
    steering_angles: List[float] = None

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
            data.steering_angles or []
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