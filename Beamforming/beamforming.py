
"""
    This is the Whole Application without applying OOP Concepts 
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import json
from matplotlib import style
import matplotlib as mpl
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
from beam_style import PLOT_STYLE, STYLE_SHEET
from mpl_toolkits.axes_grid1 import make_axes_locatable

@dataclass
class ArrayUnit:
    id: int
    name: str  # Add name field
    x_pos: float
    y_pos: float
    num_elements: int
    element_spacing: float
    steering_angle: float
    geometry_type: str
    curvature_factor: float 
    operating_freqs: List[float]
    enabled: bool = True

class ScenarioType(Enum):
    FiveG = "5G Communications"
    ULTRASOUND = "Medical Ultrasound"
    ABLATION = "Tumor Ablation"

class ModernSlider(QWidget):
    """Custom slider widget with enhanced visual styling"""
    valueChanged = pyqtSignal(float)
    
    def __init__(self, minimum, maximum, value, step=0.1, suffix=""):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Create main slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(minimum/step), int(maximum/step))
        self.slider.setValue(int(value/step))
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(int((maximum-minimum)/(10*step)))
        self.step = step
        self.suffix = suffix
        
        # Enhanced value label
        self.value_label = QLabel(f"{value:.1f}{suffix}")
        self.value_label.setFixedWidth(70)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
        """)
        
        # Apply slider styling
        self.slider.setStyleSheet("""
            QSlider {
                height: 30px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #3a3a3a;
                margin: 0 12px;
            }
            QSlider::handle:horizontal {
                background: #2196f3;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #42a5f5;
            }
            QSlider::sub-page:horizontal {
                background: #2196f3;
            }
            QSlider::tick-mark:horizontal {
                color: white;
                background: white;
                width: 1px;
                height: 3px;
            }
        """)
        
        layout.addWidget(self.slider)
        layout.addWidget(self.value_label)
        self.setLayout(layout)
        
        self.slider.valueChanged.connect(self._on_slider_changed)
        
    def _on_slider_changed(self, value):
        actual_value = value * self.step
        self.value_label.setText(f"{actual_value:.1f}{self.suffix}")
        self.value_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #1976d2;
                border: 1px solid #2196f3;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
        """)
        self.valueChanged.emit(actual_value)
        
        # Reset label style after delay
        QTimer.singleShot(200, self._reset_label_style)
        
    def _reset_label_style(self):
        self.value_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
        """)
        
    def value(self):
        return self.slider.value() * self.step
    
    def setValue(self, value):
        self.slider.setValue(int(value/self.step))
        
    def blockSignals(self, block):
        self.slider.blockSignals(block)


class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(35)
        self.setCursor(Qt.PointingHandCursor)
        style.use('dark_background')
        mpl.rcParams.update(PLOT_STYLE)


class BeamformingSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Beamforming Simulator")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(STYLE_SHEET)
        self.editing_mode = False
        
        # Initialize field variables
        self.x_field = np.linspace(-30, 30, 200)
        self.y_field = np.linspace(0, 60, 200)
        self.X, self.Y = np.meshgrid(self.x_field, self.y_field)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Create widgets (removed create_control_panel)
        self.create_visualization_area()
        self.create_menu_bar()
        self.array_units: List[ArrayUnit] = []
        self.current_unit_id = 0
        self.setup_preset_scenarios()
        self.create_array_units_panel()
        
    def create_control_panel(self):
        control_dock = QDockWidget("Parameters", self)
        control_dock.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        control_widget = QWidget()
        control_layout = QVBoxLayout()
        control_layout.setSpacing(15)
        
        # Array parameters
        array_group = QGroupBox("Array Parameters")
        array_layout = QFormLayout()
        array_layout.setSpacing(10)
        
        self.num_elements = QSpinBox()
        self.num_elements.setRange(1, 128)
        self.num_elements.setValue(16)
        array_layout.addRow("Number of Elements:", self.num_elements)
        
        self.element_spacing = QDoubleSpinBox()
        self.element_spacing.setRange(0.1, 10.0)
        self.element_spacing.setValue(0.5)
        array_layout.addRow("Element Spacing (λ):", self.element_spacing)
        
        self.steering_angle = QDoubleSpinBox()
        self.steering_angle.setRange(-90, 90)
        self.steering_angle.setValue(0)
        array_layout.addRow("Steering Angle (°):", self.steering_angle)
        
        array_group.setLayout(array_layout)
        control_layout.addWidget(array_group)
        
        # Geometry parameters
        geometry_group = QGroupBox("Array Geometry")
        geometry_layout = QFormLayout()
        geometry_layout.setSpacing(10)
        
        self.geometry_type = QComboBox()
        self.geometry_type.addItems(["Linear", "Curved"])
        geometry_layout.addRow("Array Type:", self.geometry_type)
        
        self.curvature = QDoubleSpinBox()
        self.curvature.setRange(0, 360)
        self.curvature.setValue(0)
        geometry_layout.addRow("Curvature (°):", self.curvature)
        
        geometry_group.setLayout(geometry_layout)
        control_layout.addWidget(geometry_group)
        
        # Frequency parameters
        freq_group = QGroupBox("Frequency Settings")
        freq_layout = QFormLayout()
        freq_layout.setSpacing(10)
        
        self.freq = QDoubleSpinBox()
        self.freq.setRange(1, 1000)
        self.freq.setValue(100)
        freq_layout.addRow("Frequency (MHz):", self.freq)
        
        freq_group.setLayout(freq_layout)
        control_layout.addWidget(freq_group)
        
        
        control_layout.addStretch()
        control_widget.setLayout(control_layout)
        control_dock.setWidget(control_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, control_dock)

        # Add tooltips
        self.num_elements.setToolTip("Number of array elements (1-128)")
        self.element_spacing.setToolTip("Spacing between elements in wavelengths")
        self.steering_angle.setToolTip("Beam steering angle in degrees")
        self.curvature.setToolTip("Array curvature angle for curved arrays")
        
        # Enhance spinboxes
        for spinbox in [self.num_elements, self.element_spacing, self.steering_angle, self.curvature, self.freq]:
            spinbox.setFixedHeight(30)
            spinbox.setAlignment(Qt.AlignCenter)
            
        # Add value changed connections for real-time updates
        self.num_elements.valueChanged.connect(self.update_pattern)
        self.element_spacing.valueChanged.connect(self.update_pattern)
        self.steering_angle.valueChanged.connect(self.update_pattern)
        self.geometry_type.currentTextChanged.connect(self.update_pattern)
        self.curvature.valueChanged.connect(self.update_pattern)
        
    
    def update_colormap(self):
        # Re-draw interference plot with new colormap
        if hasattr(self, 'last_interference_data'):
            self.update_interference_plot(
                self.x_field, 
                self.y_field, 
                self.last_interference_data,
                self.colormap_selector.currentText()
            )

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        load_scenario = QAction("Load Scenario", self)
        load_scenario.setShortcut("Ctrl+O")
        load_scenario.triggered.connect(self.load_scenario)
        file_menu.addAction(load_scenario)
        
        save_scenario = QAction("Save Scenario", self)
        save_scenario.setShortcut("Ctrl+S")
        save_scenario.triggered.connect(self.save_scenario)
        file_menu.addAction(save_scenario)

        scenario_menu = self.menuBar().addMenu("Scenarios")
        
        for scenario_type in ScenarioType:
            action = QAction(scenario_type.value, self)
            action.triggered.connect(
                lambda checked, st=scenario_type: self.load_preset_scenario(st)
            )
            scenario_menu.addAction(action)
        
    def create_visualization_area(self):
        viz_widget = QWidget()
        viz_layout = QVBoxLayout()
        viz_layout.setSpacing(15)
        
        # First row - Pattern plots side by side
        plots_row = QHBoxLayout()
        plots_row.setSpacing(10)
        
        # Left - Beam pattern
        pattern_container = QWidget()
        pattern_layout = QVBoxLayout(pattern_container)
        self.pattern_fig = Figure(figsize=(10, 10))
        self.pattern_fig.patch.set_facecolor('#1e1e1e')
        self.pattern_canvas = FigureCanvasQTAgg(self.pattern_fig)
        pattern_layout.addWidget(self.pattern_canvas)
        
        pattern_toolbar = NavigationToolbar2QT(self.pattern_canvas, pattern_container)
        pattern_toolbar.setStyleSheet("background-color: #2d2d2d; color: white;")
        pattern_layout.addWidget(pattern_toolbar)
        plots_row.addWidget(pattern_container)
        
        # Right - Interference pattern
        interference_container = QWidget()
        interference_layout = QVBoxLayout(interference_container)
        self.interference_fig = Figure(figsize=(10, 10))
        self.interference_fig.patch.set_facecolor('#1e1e1e')
        self.interference_canvas = FigureCanvasQTAgg(self.interference_fig)
        interference_layout.addWidget(self.interference_canvas)
        
        interference_toolbar = NavigationToolbar2QT(self.interference_canvas, interference_container)
        interference_toolbar.setStyleSheet("background-color: #2d2d2d; color: white;")
        interference_layout.addWidget(interference_toolbar)
        plots_row.addWidget(interference_container)
        
        viz_layout.addLayout(plots_row)
        
        # Second row - Array plot (full width)
        array_row = QHBoxLayout()
        array_row.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        array_container = QWidget()
        array_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Allow horizontal expansion
        array_layout = QVBoxLayout(array_container)
        array_layout.setContentsMargins(0, 0, 0, 0)  # Remove container margins
        
        self.array_fig = Figure(figsize=(12, 8))  # Wider figure
        self.array_fig.patch.set_facecolor('#1e1e1e')
        self.array_canvas = FigureCanvasQTAgg(self.array_fig)
        array_layout.addWidget(self.array_canvas)
        
        array_toolbar = NavigationToolbar2QT(self.array_canvas, array_container)
        array_toolbar.setStyleSheet("background-color: #2d2d2d; color: white;")
        array_layout.addWidget(array_toolbar)

        
        
        array_container.setLayout(array_layout)
        array_row.addWidget(array_container, stretch=1)  # Add stretch factor
        
        viz_layout.addLayout(array_row)
        viz_widget.setLayout(viz_layout)
        self.layout.addWidget(viz_widget)

    def update_pattern(self):
        if not self.array_units:
            # Clear the pattern plot
            self.pattern_fig.clear()
            self.pattern_canvas.draw()

            # Clear the array plot
            self.array_fig.clear()
            self.array_canvas.draw()

            # Clear the interference plot
            self.interference_fig.clear()
            self.interference_canvas.draw()
        else:
            # Calculate combined pattern for all units
            self.calculate_combined_pattern()


    def calculate_array_geometry(self, unit):
        if unit.geometry_type == "Linear":
            x = (np.arange(unit.num_elements) - unit.num_elements/2) * unit.element_spacing + unit.x_pos
            y = np.zeros_like(x) + unit.y_pos
        else:
            # Curved array with angle span
            angle_span = np.pi/3  # 60 degrees default
            radius = unit.curvature_factor * unit.element_spacing * unit.num_elements / 2
            angles = np.linspace(-angle_span/2, angle_span/2, unit.num_elements)
            x = radius * np.sin(angles) + unit.x_pos
            y = radius * (1 - np.cos(angles)) + unit.y_pos
        return x, y

    def calculate_combined_pattern(self):    
        # Step 1: Setup basic parameters
        viewing_angles = np.linspace(-np.pi/2, np.pi/2, 1000)
        beam_pattern = np.zeros_like(viewing_angles, dtype=np.complex128)
        field_interference = np.zeros_like(self.X, dtype=np.complex128)
        
        # Find reference frequency for normalization
        highest_freq = max([max(unit.operating_freqs) for unit in self.array_units if unit.enabled])
        
        # Step 2: Process each active array unit
        for unit in self.array_units:
            if not unit.enabled:
                continue
                
            element_x, element_y = self.calculate_array_geometry(unit)
            steering_angle = np.radians(unit.steering_angle)
            
            # Step 3: Process each frequency
            for freq in unit.operating_freqs:
                # Modified frequency scaling to enhance beam width variation
                freq_scale = freq/highest_freq
                k = 2 * np.pi * freq_scale  # Scaled wavenumber
                wavelength = 2 * np.pi/k
                
                # Calculate array parameters scaled by frequency
                array_length = unit.num_elements * unit.element_spacing * wavelength
                near_far_transition = 2 * array_length**2 / wavelength
                
                # Calculate patterns with enhanced frequency dependence
                self._calculate_far_field_pattern(
                    beam_pattern, viewing_angles, element_x, element_y,
                    k, steering_angle, unit.geometry_type, freq_scale
                )
                
                self._calculate_interference_field(
                    field_interference, element_x, element_y,
                    k, wavelength, steering_angle,
                    near_far_transition, freq_scale, unit.geometry_type
                )
        
        normalized_pattern = self._normalize_pattern(beam_pattern)
        processed_interference = self._process_interference(field_interference)
        self._update_all_plots(normalized_pattern, viewing_angles, processed_interference)

    def _calculate_far_field_pattern(self, pattern, angles, x, y, k, steer_angle, geometry, freq_scale):
        # Modified to show stronger frequency dependence
        for i, theta in enumerate(angles):
            if geometry == "Linear":
                phase = k * (x * np.sin(theta) + y * np.cos(theta))
                steer_phase = k * (x * np.sin(steer_angle))
            else:  # Curved array
                r = np.sqrt((x * np.sin(theta))**2 + (y * np.cos(theta))**2)
                phase = k * r
                r_steer = np.sqrt((x * np.sin(steer_angle))**2 + (y * np.cos(steer_angle))**2)
                steer_phase = k * r_steer
            
            # Enhanced frequency-dependent amplitude scaling
            amplitude = freq_scale**1.5  # More pronounced frequency effect
            pattern[i] += amplitude * np.sum(np.exp(1j * (phase - steer_phase)))

    def _calculate_interference_field(self, interference, x, y, k, wavelength, 
                    steer_angle, transition_dist, freq_scale, geometry):
        array_center_x = np.mean(x)
        array_center_y = np.mean(y)
        theta = -steer_angle
        
        # Rotated coordinates
        X_rot = (self.X - array_center_x) * np.cos(theta) - (self.Y - array_center_y) * np.sin(theta) + array_center_x
        Y_rot = (self.X - array_center_x) * np.sin(theta) + (self.Y - array_center_y) * np.cos(theta) + array_center_y
        
        # Enhanced beam width scaling with frequency
        beam_width_factor = (1 / freq_scale) ** 2  # Quadratic scaling for more pronounced effect
        
        # Wavelength-dependent spreading
        spread_distance = wavelength * 5  # Scale spreading with wavelength
        
        for i in range(len(x)):
            distance = np.sqrt((X_rot - x[i])**2 + (Y_rot - y[i])**2)
            
            # Phase calculation with frequency scaling
            phase = k * distance
            
            # Modified amplitude calculation with enhanced frequency dependence
            amplitude = np.where(
                distance < transition_dist,
                beam_width_factor / (1 + distance/spread_distance),  # Enhanced near field
                beam_width_factor / np.sqrt(1 + distance/spread_distance)  # Enhanced far field
            )
            
            # Apply wavelength-dependent spreading
            spread_factor = np.exp(-distance / (transition_dist * beam_width_factor))
            amplitude *= spread_factor
            
            interference += amplitude * np.exp(1j * phase)
                
    def _normalize_pattern(self, pattern):
        pattern = np.abs(pattern)
        return pattern / np.max(pattern) if np.max(pattern) > 0 else pattern

    def _process_interference(self, interference):
        magnitude = np.abs(interference)
        max_value = np.max(magnitude)
        
        if max_value > 0:
            db_values = 20 * np.log10(magnitude / max_value + 1e-10)
            return np.clip(db_values, -60, 0)
        return np.zeros_like(magnitude) - 60

    def _update_all_plots(self, pattern, angles, interference):
        self.update_pattern_plot(angles, pattern)
        
        active_elements_x = []
        active_elements_y = []
        for unit in self.array_units:
            if unit.enabled:
                x, y = self.calculate_array_geometry(unit)
                active_elements_x.extend(x)
                active_elements_y.extend(y)
        
        self.update_array_plot(np.array(active_elements_x), np.array(active_elements_y))
        self.update_interference_plot(self.x_field, self.y_field, interference)


    def update_interference_plot(self, x, y, interference, cmap='RdBu_r'):
        self.last_interference_data = interference
        self.interference_fig.clear()
        ax = self.interference_fig.add_subplot(111)
        
        # Plot interference pattern in dB scale
        im = ax.imshow(interference,
                    extent=[x.min(), x.max(), y.min(), y.max()],
                    origin='lower',
                    cmap=cmap,
                    aspect='equal',
                    vmin=-60,  # dB range minimum
                    vmax=0)    # dB range maximum
        
        ax.set_title('Interference Pattern (dB)', color='white', pad=10)
        ax.set_xlabel('X Position (λ)', color='white')
        ax.set_ylabel('Y Position (λ)', color='white')
        
        # Add colorbar matched to plot height
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = self.interference_fig.colorbar(im, cax=cax, label='Relative Power (dB)')
        cbar.ax.yaxis.label.set_color('white')
        cbar.ax.tick_params(colors='white')
        
        # Add grid
        ax.grid(True, color='#404040', alpha=0.5, linestyle='--')
        ax.tick_params(colors='white')
        
        # Ensure tight layout
        self.interference_fig.tight_layout()
        self.interference_canvas.draw()

    def update_pattern_plot(self, theta, pattern):
        """Visualizes the beam pattern in polar coordinates"""
        # Clear previous plot
        self.pattern_fig.clear()
        ax = self.pattern_fig.add_subplot(111, projection='polar')
        
        # Configure plot orientation
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi/2)
        
        # Prepare data for plotting
        mask = (theta >= -np.pi/2) & (theta <= np.pi/2)
        theta_plot = theta[mask]
        pattern_plot = pattern[mask]
        
        # Convert to dB scale with proper normalization
        pattern_db = 20 * np.log10(np.clip(pattern_plot, 1e-10, None))
        pattern_db = np.clip(pattern_db, -40, 0)  # Limit dynamic range
        normalized_pattern = pattern_db + 40  # Shift to positive values for visualization
        
        # Plot main and side lobes
        main_lobe_mask = pattern_db >= -3
        side_lobe_mask = (pattern_db < -3) & (pattern_db >= -20)
        
        ax.fill_between(theta_plot, 0, normalized_pattern,
                        where=main_lobe_mask,
                        color='#2196f3', alpha=0.3,
                        label='Main Lobe (-3dB)')
        ax.fill_between(theta_plot, 0, normalized_pattern,
                        where=side_lobe_mask,
                        color='#ff9800', alpha=0.2,
                        label='Side Lobes')
        
        # Add beam metrics and power level indicators
        self._add_power_level_indicators(ax)
        self._show_beam_metrics(ax, theta_plot, pattern_db)
        self._add_steering_indicators(ax)
        
        # Configure plot appearance
        ax.set_thetamin(-90)
        ax.set_thetamax(90)
        ax.set_ylim(0, 60)
        ax.set_rticks([0, 15, 30, 45, 60])
        ax.set_rlabel_position(90)
        ax.grid(True, color='white', alpha=0.1, linestyle=':')
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white')
        ax.set_title('Beam Pattern Analysis',
                    color='white', pad=20,
                    fontsize=14, fontweight='bold')
        
        # Add legend
        ax.legend(loc='upper right', 
                bbox_to_anchor=(1.3, 1.1),
                facecolor='#2d2d2d',
                edgecolor='none',
                labelcolor='white')
        
        # Update canvas
        self.pattern_fig.tight_layout()
        self.pattern_canvas.draw()

    def _add_power_level_indicators(self, ax):
        """Adds concentric circles showing power levels in dB."""
        db_levels = [-3, -6, -10, -20, -30, -40]
        for db in db_levels:
            # Add circle for each power level
            circle = plt.Circle((0, 0), 40 + db,
                            fill=False, color='white',
                            linestyle='--', alpha=0.3)
            ax.add_artist(circle)
            
            # Label major power levels
            if db in [-3, -10, -20]:
                ax.text(np.pi/4, 40 + db,
                    f'{db} dB',
                    color='white',
                    ha='left', va='bottom',
                    bbox=dict(facecolor='#2d2d2d',
                            alpha=0.7,
                            edgecolor='none'))

    def _show_beam_metrics(self, ax, theta, pattern_db):
        """Calculates and displays key beam pattern metrics."""
        half_power = -3  # -3dB power level
        idx_above = np.where(pattern_db > half_power)[0]
        
        if len(idx_above) > 0:
            # Calculate beam width
            beam_width = np.abs(np.degrees(theta[idx_above[-1]] - theta[idx_above[0]]))
            # Calculate directivity
            directivity = 10*np.log10(1/beam_width*180/np.pi)
            
            # Display metrics
            metrics_text = (
                f'Key Metrics:\n'
                f'• Beam Width: {beam_width:.1f}°\n'
                f'• Directivity: {directivity:.1f} dB'
            )
            ax.text(np.pi/2, 45, metrics_text,
                    color='white',
                    ha='left', va='top',
                    bbox=dict(facecolor='#2d2d2d',
                            alpha=0.9,
                            edgecolor='#404040',
                            boxstyle='round,pad=0.5'))

    def _add_steering_indicators(self, ax):
        """Adds visual indicators for beam steering angles."""
        for unit in self.array_units:
            if unit.enabled and unit.steering_angle != 0:
                angle = np.radians(unit.steering_angle)
                
                # Add steering direction line
                ax.plot([angle, angle], [0, 40],
                    color='#ff9800',
                    linestyle='--',
                    linewidth=2,
                    alpha=0.7,
                    label=f'Steering {unit.steering_angle}°')
                
                # Add arc indicator
                arc = np.linspace(angle-np.pi/12, angle+np.pi/12, 100)
                ax.plot(arc, np.ones_like(arc)*40,
                    color='#ff9800',
                    alpha=0.3)
        
    def update_array_plot(self, x, y):
        self.array_fig.clear()
        ax = self.array_fig.add_subplot(111)
        
        # Set background color
        ax.set_facecolor('#1e1e1e')
        
        # Add better grid
        ax.grid(True, color='#404040', alpha=0.3, linestyle=':', zorder=1)
        major_ticks = np.arange(np.floor(min(x)-1), np.ceil(max(x)+1), 1)
        ax.set_xticks(major_ticks)
        ax.set_yticks(major_ticks)
        
            
        # Plot elements with better visibility
        scatter = ax.scatter(x, y, 
                            c='#2196f3',
                            marker='o', 
                            s=150,  # Larger markers
                            edgecolor='white',
                            linewidth=1,
                            alpha=0.8,
                            zorder=3)
        
        # Set title and labels with better styling
        ax.set_title('Array Geometry', color='white', pad=15, fontsize=14, fontweight='bold')
        ax.set_xlabel('X Position (λ)', color='white', fontsize=12, labelpad=10)
        ax.set_ylabel('Y Position (λ)', color='white', fontsize=12, labelpad=10)
        
        # Improve tick labels
        ax.tick_params(colors='white', labelsize=10, length=6, width=1)
        
        # Auto-scale with better padding
        x_min, x_max = np.min(x), np.max(x)
        y_min, y_max = np.min(y), np.max(y)
        x_range = max(x_max - x_min, 1)  # Ensure minimum range
        y_range = max(y_max - y_min, 1)
        padding = max(x_range, y_range) * 0.3  # More padding
        
        ax.set_xlim(x_min - padding, x_max + padding)
        ax.set_ylim(y_min - padding, y_max + padding)
        
        # Enhanced unit colors with better contrast
        unit_colors = ['#2196f3', '#4caf50', '#f44336', '#ff9800', '#9c27b0']
        current_unit_start = 0
        
        if hasattr(self, 'array_units') and self.array_units:
            for i, unit in enumerate(self.array_units):
                if not unit.enabled:
                    continue
                    
                x_unit, y_unit = self.calculate_array_geometry(unit)
                unit_size = len(x_unit)
                unit_end = current_unit_start + unit_size
                
                # Draw enhanced unit boundary
                hull_x = np.concatenate([x_unit, [x_unit[0]]])
                hull_y = np.concatenate([y_unit, [y_unit[0]]])
                ax.plot(hull_x, hull_y, 
                    color=unit_colors[i % len(unit_colors)], 
                    alpha=0.7, 
                    linewidth=2,
                    linestyle='--',
                    zorder=2)
                
                # Add improved unit label with more info
                center_x = np.mean(x_unit)
                center_y = np.mean(y_unit)
                label_text = (f'Unit {unit.id}\n'
                            f'θ = {unit.steering_angle}°\n'
                            f'N = {unit.num_elements}')
                ax.text(center_x, center_y + padding/3,
                    label_text,
                    color=unit_colors[i % len(unit_colors)],
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    bbox=dict(facecolor='#2d2d2d',
                            edgecolor=unit_colors[i % len(unit_colors)],
                            alpha=0.8,
                            boxstyle='round,pad=0.5'))
                
                # Add element numbers with better visibility
                for j, (xi, yi) in enumerate(zip(x_unit, y_unit)):
                    ax.annotate(f'{current_unit_start + j + 1}',
                            (xi, yi),
                            xytext=(0, -20),
                            textcoords='offset points',
                            ha='center',
                            va='top',
                            color='white',
                            fontsize=9,
                            bbox=dict(facecolor='#2d2d2d',
                                    edgecolor='none',
                                    alpha=0.6,
                                    pad=1))
                    
                current_unit_start = unit_end
                
                # Add steering direction indicator
                if unit.steering_angle != 0:
                    angle = np.radians(unit.steering_angle)
                    arrow_len = padding * 0.3
                    dx = arrow_len * np.sin(angle)
                    dy = arrow_len * np.cos(angle)
                    ax.arrow(center_x, center_y,
                            dx, dy,
                            head_width=0.2,
                            head_length=0.3,
                            fc=unit_colors[i % len(unit_colors)],
                            ec=unit_colors[i % len(unit_colors)],
                            alpha=0.7,
                            zorder=4)
        else:
            # Single unit case with improved visibility
            for i, (xi, yi) in enumerate(zip(x, y)):
                ax.annotate(f'{i + 1}',
                        (xi, yi),
                        xytext=(0, -20),
                        textcoords='offset points',
                        ha='center',
                        va='top',
                        color='white',
                        fontsize=9,
                        bbox=dict(facecolor='#2d2d2d',
                                alpha=0.6,
                                pad=1))
        
        # Set equal aspect ratio
        ax.set_aspect('equal')
        
        # Add spines with better visibility
        for spine in ax.spines.values():
            spine.set_color('#404040')
            spine.set_linewidth(1)
        
        # Update layout with more space
        ax.set_aspect('equal', adjustable='box')
    
        # Reduce vertical size while maintaining readability
        plt.subplots_adjust(bottom=0.2, top=0.9)
        
        # Update layout with less vertical padding
        self.array_fig.tight_layout(pad=0.5, h_pad=0.5, w_pad=0.5)
        self.array_canvas.draw()
        
    def save_scenario(self):
        params = {
            'num_elements': self.num_elements.value(),
            'element_spacing': self.element_spacing.value(),
            'steering_angle': self.steering_angle.value(),
            'geometry_type': self.geometry_type.currentText(),
            'curvature': self.curvature.value(),
            'frequency': self.freq.value()
        }
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Scenario",
            "",
            "JSON Files (*.json)"
        )
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(params, f, indent=4)
                
    def load_scenario(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Scenario",
            "",
            "JSON Files (*.json)"
        )
        
        if filename:
            with open(filename, 'r') as f:
                params = json.load(f)
                
            self.num_elements.setValue(params['num_elements'])
            self.element_spacing.setValue(params['element_spacing'])
            self.steering_angle.setValue(params['steering_angle'])
            self.geometry_type.setCurrentText(params['geometry_type'])
            self.curvature.setValue(params['curvature'])
            self.freq.setValue(params['frequency'])
            
            # Update visualization
            self.update_pattern()

    def load_preset_scenario(self, scenario_type: ScenarioType):
        scenario = self.scenarios[scenario_type]
        self.array_units.clear()
        
        for unit_params in scenario["params"]["units"]:
            unit = ArrayUnit(
                id=self.current_unit_id,
                **unit_params
            )
            self.array_units.append(unit)
            self.current_unit_id += 1
        
        self.update_units_list()  # Add this line
        self.update_pattern()

    def setup_preset_scenarios(self):
        self.scenarios = {
            ScenarioType.FiveG: {
                "description": "5G Beamforming Array (28 GHz)",
                "params": {
                    "units": [
                        {
                            "name": "5G Base Station",
                            "num_elements": 16,
                            "element_spacing": 0.5,
                            "steering_angle": 0,
                            "geometry_type": "Linear",
                            "curvature_factor": 1.0,
                            "operating_freqs": [100],
                            "x_pos": 0,
                            "y_pos": 0,
                            
                        }
                    ]
                }
            },
            ScenarioType.ULTRASOUND: {
                "description": "Medical Ultrasound Scanner (5 MHz)",
                "params": {
                    "units": [
                        {
                            "name": "Ultrasound Probe",
                            "num_elements": 16,
                            "element_spacing": 0.06,
                            "steering_angle": 0,
                            "geometry_type": "Linear", 
                            "curvature_factor": 1.5,
                            "operating_freqs": [0.5],
                            "x_pos": 0,
                            "y_pos": 0 
                        }
                    ]
                }
            },
            ScenarioType.ABLATION: {
                "description": "Medical Ultrasound Scanner (5 MHz)",
                "params": {
                    "units": [
                        {
                            "name": "Tumor Ablation Array",
                            "num_elements": 35,
                            "element_spacing": 0.25,
                            "steering_angle": 0,
                            "geometry_type": "Curved",
                            "curvature_factor": 1.5,
                            "operating_freqs": [5],
                            "x_pos": 0,
                            "y_pos": 0,
                            
                        }
                    ]
                }
            }
        }

    def create_array_units_panel(self):
        # Create dock widget for unit management
        units_dock = QDockWidget("Array Units Manager", self)
        units_widget = QWidget()
        units_layout = QVBoxLayout()

        # List of units with better styling
        self.units_list = QListWidget()
        self.units_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                min-width: 200px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
            }
        """)
        self.units_list.currentItemChanged.connect(self.on_unit_selected)
        units_layout.addWidget(self.units_list)

        # Buttons for unit management
        buttons_layout = QHBoxLayout()
        self.add_edit_button = ModernButton("Add Unit")
        self.add_edit_button.setToolTip("Create new unit with current parameters")
        self.add_edit_button.clicked.connect(self.toggle_edit_mode)
        
        remove_button = ModernButton("Remove Unit")
        remove_button.setToolTip("Remove selected unit")
        remove_button.clicked.connect(self.remove_selected_unit)
        
        buttons_layout.addWidget(self.add_edit_button)
        buttons_layout.addWidget(remove_button)
        units_layout.addLayout(buttons_layout)

        # Unit specific controls
        unit_controls = QGroupBox("Selected Unit Controls")
        unit_layout = QFormLayout()

        # Geometry type control remains a combobox
        self.geometry_type = QComboBox()
        self.geometry_type.addItems(["Linear", "Curved"])
        self.geometry_type.currentTextChanged.connect(self.on_geometry_changed)
        unit_layout.addRow("Array Type:", self.geometry_type)

        # Position controls
        self.unit_x = ModernSlider(-20, 20, 0, 0.1, " λ")
        self.unit_x.valueChanged.connect(self.update_unit_position)
        unit_layout.addRow("X Position:", self.unit_x)

        self.unit_y = ModernSlider(-20, 20, 0, 0.1, " λ")
        self.unit_y.valueChanged.connect(self.update_unit_position)
        unit_layout.addRow("Y Position:", self.unit_y)

        # Unit parameters with sliders
        self.unit_elements = ModernSlider(1, 128, 16, 1, "")
        self.unit_elements.valueChanged.connect(self.update_unit_parameters)
        unit_layout.addRow("Elements:", self.unit_elements)

        self.unit_spacing = ModernSlider(0.1, 10.0, 0.5, 0.1, " λ")
        self.unit_spacing.valueChanged.connect(self.update_unit_parameters)
        unit_layout.addRow("Spacing:", self.unit_spacing)

        self.unit_steering = ModernSlider(-90, 90, 0, 1, "°")
        self.unit_steering.valueChanged.connect(self.update_unit_parameters)
        unit_layout.addRow("Steering:", self.unit_steering)

        self.curvature_widget = QWidget()
        curvature_layout = QFormLayout()
        curvature_layout.setContentsMargins(0, 0, 0, 0)
        
        self.unit_curvature = ModernSlider(0, 2, 1, 0.1, "")
        self.unit_curvature.valueChanged.connect(self.update_unit_parameters)
        curvature_layout.addRow("Curvature Factor:", self.unit_curvature)
        
        self.curvature_widget.setLayout(curvature_layout)
        unit_layout.addRow("", self.curvature_widget)
        self.curvature_widget.hide()  # Initially hidden

        # Add frequency controls
        freq_group = QGroupBox("Operating Frequencies")
        freq_layout = QVBoxLayout()
        
        # Create frequency table
        self.freq_table = QTableWidget()
        self.freq_table.setColumnCount(2)
        self.freq_table.setHorizontalHeaderLabels(['Frequency', 'Unit'])
        self.freq_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.freq_table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: white;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: white;
                padding: 5px;
                border: none;
            }
        """)
        freq_layout.addWidget(self.freq_table)
        
        # Frequency input controls
        input_layout = QHBoxLayout()
        
        self.freq_input = ModernSlider(0.1, 1000, 100, 0.1, " MHz")
        input_layout.addWidget(self.freq_input)
        
        add_freq_btn = ModernButton("Add")
        add_freq_btn.clicked.connect(self.add_frequency)
        input_layout.addWidget(add_freq_btn)
        
        remove_freq_btn = ModernButton("Remove")
        remove_freq_btn.clicked.connect(self.remove_frequency)
        input_layout.addWidget(remove_freq_btn)
        
        freq_layout.addLayout(input_layout)
        
        # Add frequency presets
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Presets:")
        preset_label.setStyleSheet("color: white;")
        preset_layout.addWidget(preset_label)
        
        presets = {
            "5G": 28,
            "WiFi": 2.4,
            "Ultrasound": 5,
            "RADAR": 10
        }
        
        for name, freq in presets.items():
            preset_btn = ModernButton(name)
            preset_btn.setFixedWidth(60)
            preset_btn.clicked.connect(lambda checked, f=freq: self.freq_input.setValue(f))
            preset_layout.addWidget(preset_btn)
        
        preset_layout.addStretch()
        freq_layout.addLayout(preset_layout)
        
        freq_group.setLayout(freq_layout)
        unit_layout.addRow("", freq_group)


        unit_controls.setLayout(unit_layout)
        units_layout.addWidget(unit_controls)

        units_widget.setLayout(units_layout)
        units_dock.setWidget(units_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, units_dock)


    def on_geometry_changed(self, geometry_type):
        """Handle geometry type changes"""
        self.curvature_widget.setVisible(geometry_type == "Curved")
        self.update_unit_parameters()


    def add_frequency(self):
        freq = self.freq_input.value()
        row = self.freq_table.rowCount()
        self.freq_table.insertRow(row)
        
        freq_item = QTableWidgetItem(f"{freq}")
        unit_item = QTableWidgetItem("MHz")
        
        self.freq_table.setItem(row, 0, freq_item)
        self.freq_table.setItem(row, 1, unit_item)
        
        # Update unit if one is selected
        current_item = self.units_list.currentItem()
        if current_item:
            unit_id = current_item.data(Qt.UserRole)
            unit = next((u for u in self.array_units if u.id == unit_id), None)
            if unit:
                unit.operating_freqs.append(freq)
                self.update_pattern()

    def remove_frequency(self):
        """Remove selected frequency with validation"""
        current_row = self.freq_table.currentRow()
        if current_row >= 0:
            # Don't allow removal of last frequency
            if self.freq_table.rowCount() <= 1:
                QMessageBox.warning(self, "Warning", 
                                "Cannot remove last frequency.\nAt least one frequency is required.")
                return
                
            self.freq_table.removeRow(current_row)
            
            # Update unit if one is selected
            current_item = self.units_list.currentItem()
            if current_item:
                unit_id = current_item.data(Qt.UserRole)
                unit = next((u for u in self.array_units if u.id == unit_id), None)
                if unit and len(unit.operating_freqs) > current_row:
                    unit.operating_freqs.pop(current_row)
                    self.update_pattern()



    def toggle_edit_mode(self):
        if self.editing_mode:
            # Exit edit mode
            self.editing_mode = False
            self.add_edit_button.setText("Add Unit")
            self.units_list.clearSelection()
            self.clear_unit_controls()
        else:
            # Enter add mode
            self.editing_mode = True
            self.add_edit_button.setText("Exit Edit Mode")
            self.add_array_unit()

    def clear_unit_controls(self):
        """Reset all unit control values to defaults"""
        self.unit_x.setValue(0)
        self.unit_y.setValue(0)
        self.unit_elements.setValue(16)
        self.unit_spacing.setValue(0.5)
        self.unit_steering.setValue(0)
        self.unit_curvature.setValue(1)
        self.freq_table.setRowCount(0)

    def on_unit_selected(self, current, previous):
        if current:
            unit_id = current.data(Qt.UserRole)
            unit = next((u for u in self.array_units if u.id == unit_id), None)
            if unit:
                # Block signals temporarily
                for control in [self.unit_x, self.unit_y, self.unit_elements, 
                                self.unit_spacing, self.unit_steering, 
                                self.unit_curvature, self.geometry_type]:
                    control.blockSignals(True)
                
                # Update control values
                self.unit_x.setValue(unit.x_pos)  
                self.unit_y.setValue(unit.y_pos)
                self.unit_elements.setValue(unit.num_elements)
                self.unit_spacing.setValue(unit.element_spacing)
                self.unit_steering.setValue(unit.steering_angle)
                self.unit_curvature.setValue(unit.curvature_factor)
                self.geometry_type.setCurrentText(unit.geometry_type)
                self.curvature_widget.setVisible(unit.geometry_type == "Curved")
                
                # Re-enable signals
                for control in [self.unit_x, self.unit_y, self.unit_elements,
                                self.unit_spacing, self.unit_steering, 
                                self.unit_curvature, self.geometry_type]:
                    control.blockSignals(False)
                    
                # Update frequency table
                self.freq_table.setRowCount(0)
                for freq in unit.operating_freqs:
                    row = self.freq_table.rowCount()
                    self.freq_table.insertRow(row)
                    self.freq_table.setItem(row, 0, QTableWidgetItem(f"{freq}"))
                    self.freq_table.setItem(row, 1, QTableWidgetItem("MHz"))
                
                self.add_edit_button.setText("Exit Edit Mode")
                self.editing_mode = True


    def update_unit_parameters(self):
        """Update selected unit parameters in real-time with frequency validation"""
        current_item = self.units_list.currentItem()
        if current_item and self.array_units and self.editing_mode:
            unit_id = current_item.data(Qt.UserRole)
            unit = next((u for u in self.array_units if u.id == unit_id), None)
            if unit:
                # Get frequencies from table
                frequencies = []
                for i in range(self.freq_table.rowCount()):
                    try:
                        freq = float(self.freq_table.item(i, 0).text())
                        frequencies.append(freq)
                    except (ValueError, AttributeError):
                        continue
                
                # Ensure at least one frequency exists
                if not frequencies:
                    frequencies = [self.freq_input.value()]
                    self.add_frequency()  # Add default frequency to table
                
                # Update unit parameters
                unit.num_elements = self.unit_elements.value()
                unit.element_spacing = self.unit_spacing.value()
                unit.steering_angle = self.unit_steering.value()
                unit.geometry_type = self.geometry_type.currentText()
                unit.curvature_factor = self.unit_curvature.value()
                unit.operating_freqs = frequencies
                
                self.update_pattern()

    def update_unit_position(self):
        current_item = self.units_list.currentItem()
        if current_item and self.array_units:
            unit_id = current_item.data(Qt.UserRole)
            unit = next((u for u in self.array_units if u.id == unit_id), None)
            if unit:
                unit.x_pos = self.unit_x.value()
                unit.y_pos = self.unit_y.value()
                self.update_pattern()

    def update_unit_phase(self):
        current_item = self.units_list.currentItem()
        if current_item and self.array_units:
            unit_id = current_item.data(Qt.UserRole)
            unit = next((u for u in self.array_units if u.id == unit_id), None)
            if unit:
                self.update_pattern()

    def remove_selected_unit(self):
        current_item = self.units_list.currentItem()
        if current_item:
            unit_id = current_item.data(Qt.UserRole)
            self.remove_array_unit(unit_id)
            self.units_list.takeItem(self.units_list.row(current_item))

    def add_array_unit(self):
        # Get current frequencies from table
        frequencies = []
        for row in range(self.freq_table.rowCount()):
            freq_item = self.freq_table.item(row, 0)
            if freq_item:
                frequencies.append(float(freq_item.text()))
                
        if not frequencies:  # If no frequencies, use default
            frequencies = [self.freq_input.value()]
            
        # Create dialog for unit name
        name, ok = QInputDialog.getText(self, "New Unit", "Enter unit name:")
        if ok and name:
            unit = ArrayUnit(
                id=self.current_unit_id,
                name=name,
                x_pos=self.unit_x.value(),
                y_pos=self.unit_y.value(),
                num_elements=self.unit_elements.value(),
                element_spacing=self.unit_spacing.value(),
                steering_angle=self.unit_steering.value(),
                geometry_type=self.geometry_type.currentText(),
                curvature_factor=self.unit_curvature.value(),
                operating_freqs=frequencies,
                enabled=True
            )
            self.array_units.append(unit)
            self.current_unit_id += 1
            
            self.editing_mode = False
            self.add_edit_button.setText("Add Unit")
            self.clear_unit_controls()
            
            self.update_units_list()
            self.update_pattern()

    def update_units_list(self):
        self.units_list.clear()
        for unit in self.array_units:
            item = QListWidgetItem(f"{unit.name}")  # Show unit name instead of "Unit {id}"
            item.setData(Qt.UserRole, unit.id)
            self.units_list.addItem(item)

    def remove_array_unit(self, unit_id: int):
        self.array_units = [u for u in self.array_units if u.id != unit_id]
        self.update_pattern()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BeamformingSimulator()
    window.show()
    sys.exit(app.exec_())
