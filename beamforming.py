import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import json
from matplotlib import style
import matplotlib as mpl
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from beam_style import PLOT_STYLE, STYLE_SHEET

@dataclass
class ArrayUnit:
    id: int
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
        self.x_field = np.linspace(-10, 10, 200)
        self.y_field = np.linspace(0, 20, 200)
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
        
    def create_visualization_area(self):
        viz_widget = QWidget()
        viz_layout = QVBoxLayout()
        viz_layout.setSpacing(15)
        
        # Title label with modern styling
        title_label = QLabel("Beamforming Visualization")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
                background-color: #2d2d2d;
                border-radius: 5px;
            }
        """)
        viz_layout.addWidget(title_label)
        
        # Create horizontal layout for side-by-side plots
        plot_layout = QHBoxLayout()
        
        # Left side - Pattern and Array plots
        left_plots = QVBoxLayout()
        
        # Beam pattern plot with toolbar
        pattern_container = QWidget()
        pattern_layout = QVBoxLayout(pattern_container)
        self.pattern_fig = Figure(figsize=(6, 4))
        self.pattern_fig.patch.set_facecolor('#1e1e1e')
        self.pattern_canvas = FigureCanvasQTAgg(self.pattern_fig)
        pattern_layout.addWidget(self.pattern_canvas)
        
        # Add navigation toolbar
        pattern_toolbar = NavigationToolbar2QT(self.pattern_canvas, pattern_container)
        pattern_toolbar.setStyleSheet("background-color: #2d2d2d; color: white;")
        pattern_layout.addWidget(pattern_toolbar)
        left_plots.addWidget(pattern_container)
        
        # Array geometry plot with toolbar
        array_container = QWidget()
        array_layout = QVBoxLayout(array_container)
        self.array_fig = Figure(figsize=(6, 2))
        self.array_fig.patch.set_facecolor('#1e1e1e')
        self.array_canvas = FigureCanvasQTAgg(self.array_fig)
        array_layout.addWidget(self.array_canvas)
        
        array_toolbar = NavigationToolbar2QT(self.array_canvas, array_container)
        array_toolbar.setStyleSheet("background-color: #2d2d2d; color: white;")
        array_layout.addWidget(array_toolbar)
        left_plots.addWidget(array_container)
        
        plot_layout.addLayout(left_plots)
        
        # Right side - Interference map
        interference_container = QWidget()
        interference_layout = QVBoxLayout(interference_container)
        self.interference_fig = Figure(figsize=(6, 6))
        self.interference_fig.patch.set_facecolor('#1e1e1e')
        self.interference_canvas = FigureCanvasQTAgg(self.interference_fig)
        interference_layout.addWidget(self.interference_canvas)
        
        interference_toolbar = NavigationToolbar2QT(self.interference_canvas, interference_container)
        interference_toolbar.setStyleSheet("background-color: #2d2d2d; color: white;")
        interference_layout.addWidget(interference_toolbar)
        plot_layout.addWidget(interference_container)
        
        viz_layout.addLayout(plot_layout)
        
        # Add colormap selector
        colormap_layout = QHBoxLayout()
        colormap_label = QLabel("Colormap:")
        colormap_label.setStyleSheet("color: white;")
        self.colormap_selector = QComboBox()
        self.colormap_selector.addItems(['RdBu_r', 'viridis', 'plasma', 'magma', 'inferno'])
        self.colormap_selector.currentTextChanged.connect(self.update_colormap)
        colormap_layout.addWidget(colormap_label)
        colormap_layout.addWidget(self.colormap_selector)
        colormap_layout.addStretch()
        
        viz_layout.addLayout(colormap_layout)
        viz_widget.setLayout(viz_layout)
        self.layout.addWidget(viz_widget)
    
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
        viz_layout.setSpacing(10)
        
        # Create horizontal layout for side-by-side plots
        plot_layout = QHBoxLayout()
        
        # Left side - Pattern and Array plots
        left_plots = QVBoxLayout()
        
        # Beam pattern plot
        self.pattern_fig = Figure(figsize=(6, 4))
        self.pattern_fig.patch.set_facecolor('#1e1e1e')
        self.pattern_canvas = FigureCanvasQTAgg(self.pattern_fig)
        left_plots.addWidget(self.pattern_canvas)
        
        # Array geometry plot
        self.array_fig = Figure(figsize=(6, 2))
        self.array_fig.patch.set_facecolor('#1e1e1e')
        self.array_canvas = FigureCanvasQTAgg(self.array_fig)
        left_plots.addWidget(self.array_canvas)
        
        plot_layout.addLayout(left_plots)
        
        # Right side - Interference map
        self.interference_fig = Figure(figsize=(6, 6))
        self.interference_fig.patch.set_facecolor('#1e1e1e')
        self.interference_canvas = FigureCanvasQTAgg(self.interference_fig)
        plot_layout.addWidget(self.interference_canvas)
        
        viz_layout.addLayout(plot_layout)
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

    def calculate_single_pattern(self, unit):
        k = 2 * np.pi
        x, y = self.calculate_array_geometry(unit)
        theta = np.linspace(-np.pi/2, np.pi/2, 1000)
        pattern = np.zeros_like(theta, dtype=np.complex128)
        interference = np.zeros_like(self.X, dtype=np.complex128)
        
        # Calculate for each frequency
        for freq in unit.operating_freqs:
            k_freq = k * freq  # Scale wavenumber by frequency
            theta_steer = np.radians(unit.steering_angle)
            
            # Add beam pattern contribution
            for i in range(len(theta)):
                phase = k_freq * (x * np.sin(theta[i]) + y * np.cos(theta[i]))
                steer_phase = k_freq * x * np.sin(theta_steer)
                pattern[i] += np.sum(np.exp(1j * (phase - steer_phase)))
                
            # Add interference contribution
            for i in range(len(x)):
                r = np.sqrt((self.X - x[i])**2 + (self.Y - y[i])**2)
                phase = k_freq * r
                steer_phase = k_freq * x[i] * np.sin(theta_steer)
                interference += np.exp(1j * (phase - steer_phase))
        
        pattern = np.abs(pattern) / len(unit.operating_freqs)
        pattern = pattern / np.max(pattern)
        
        interference = np.abs(interference) / len(unit.operating_freqs)
        interference = interference / np.max(interference)
        
        self.update_pattern_plot(theta, pattern)
        self.update_array_plot(x, y)
        self.update_interference_plot(self.x_field, self.y_field, interference)

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
        theta = np.linspace(-np.pi/2, np.pi/2, 1000)
        pattern = np.zeros_like(theta, dtype=np.complex128)
        interference = np.zeros_like(self.X, dtype=np.complex128)
        
        # Normalize operating frequencies relative to the highest frequency
        max_freq = max([max(unit.operating_freqs) for unit in self.array_units if unit.enabled])
        
        for unit in self.array_units:
            if not unit.enabled:
                continue
                
            x, y = self.calculate_array_geometry(unit)
            theta_steer = np.radians(unit.steering_angle)
            
            # Calculate for each frequency
            for freq in unit.operating_freqs:
                # Normalized wavenumber calculation
                k = 2 * np.pi * (freq/max_freq)
                wavelength = 1/freq
                
                # Calculate critical distance (near-field to far-field transition)
                array_size = unit.num_elements * unit.element_spacing
                critical_distance = 2 * array_size**2 / wavelength
                
                # Add to beam pattern (far-field)
                for i in range(len(theta)):
                    if unit.geometry_type == "Linear":
                        phase = k * (x * np.sin(theta[i]) + y * np.cos(theta[i]))
                        steer_phase = k * (x * np.sin(theta_steer))
                    else:  # Curved array
                        # Improved phase calculation for curved arrays
                        r_points = np.sqrt((x * np.sin(theta[i]))**2 + (y * np.cos(theta[i]))**2)
                        phase = k * r_points
                        r_steer = np.sqrt((x * np.sin(theta_steer))**2 + (y * np.cos(theta_steer))**2)
                        steer_phase = k * r_steer
                    
                    pattern[i] += np.sum(np.exp(1j * (phase - steer_phase)))
                
                # Calculate interference field with near-field/far-field transitions
                for i in range(len(x)):
                    r = np.sqrt((self.X - x[i])**2 + (self.Y - y[i])**2)
                    phase = k * r
                    
                    # Improved amplitude calculation
                    if unit.geometry_type == "Linear":
                        steer_phase = k * (x[i] * np.sin(theta_steer))
                    else:
                        r_steer = np.sqrt((x[i] * np.sin(theta_steer))**2 + (y[i] * np.cos(theta_steer))**2)
                        steer_phase = k * r_steer
                    
                    # Near-field/far-field transition
                    transition_factor = np.clip(r / critical_distance, 0, 1)
                    
                    # Enhanced amplitude calculation
                    amplitude = np.where(
                        r < critical_distance,
                        1.0 / (r + wavelength/10),  # Near-field
                        1.0 / np.sqrt(r + wavelength/10)  # Far-field
                    )
                    
                    # Frequency-dependent scaling
                    freq_scale = np.sqrt(freq/max_freq)
                    
                    # Add contribution with transition
                    interference += (amplitude * freq_scale * 
                                np.exp(1j * (phase - steer_phase)) * 
                                transition_factor)
        
        # Normalize pattern
        pattern = np.abs(pattern)
        pattern = pattern / np.max(pattern) if np.max(pattern) > 0 else pattern
        
        # Process interference field with improved dynamic range
        interference_mag = np.abs(interference)
        interference_max = np.max(interference_mag)
        
        if interference_max > 0:
            # Convert to dB with enhanced dynamic range
            interference_db = 20 * np.log10(interference_mag / interference_max + 1e-10)
            interference_db = np.clip(interference_db, -60, 0)
        else:
            interference_db = np.zeros_like(interference_mag) - 60
        
        # Update visualizations
        self.update_pattern_plot(theta, pattern)
        self.update_array_plot(
            np.array([x for unit in self.array_units if unit.enabled 
                    for x in self.calculate_array_geometry(unit)[0]]),
            np.array([y for unit in self.array_units if unit.enabled 
                    for y in self.calculate_array_geometry(unit)[1]])
        )
        self.update_interference_plot(self.x_field, self.y_field, interference_db)

    def update_interference_plot(self, x, y, interference, cmap='RdBu_r'):
        self.last_interference_data = interference
        self.interference_fig.clear()
        ax = self.interference_fig.add_subplot(111)
        
        # Plot interference pattern
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
        
        # Add colorbar
        cbar = self.interference_fig.colorbar(im)
        cbar.ax.set_ylabel('Relative Power (dB)', color='white')
        cbar.ax.tick_params(colors='white')
        
        # Add grid and style
        ax.grid(True, color='#404040', alpha=0.5, linestyle='--')
        ax.tick_params(colors='white')
        ax.set_facecolor('#1e1e1e')
        
        self.interference_canvas.draw()

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
        
        # Add colorbar with dB scale
        cbar = self.interference_fig.colorbar(im, label='Relative Power (dB)')
        cbar.ax.yaxis.label.set_color('white')
        cbar.ax.tick_params(colors='white')
        
        # Add grid
        ax.grid(True, color='#404040', alpha=0.5, linestyle='--')
        ax.tick_params(colors='white')
        
        self.interference_canvas.draw()

    def update_pattern_plot(self, theta, pattern):
        self.pattern_fig.clear()
        ax = self.pattern_fig.add_subplot(111, projection='polar')
        
        # Convert to dB with better dynamic range
        pattern_db = 20 * np.log10(np.clip(pattern, 1e-10, None))
        pattern_db = np.clip(pattern_db, -40, 0)
        normalized_pattern = pattern_db + 40  # Shift to positive values
        
        # Main beam pattern with gradient color
        points = ax.plot(theta, normalized_pattern, linewidth=3, 
                        color='#2196f3', label='Main Beam')
        
        # Fill regions with transparency for better visualization
        main_lobe_mask = pattern_db >= -3
        side_lobe_mask = (pattern_db < -3) & (pattern_db >= -20)
        
        ax.fill_between(theta, 0, normalized_pattern, 
                    where=main_lobe_mask,
                    color='#2196f3', alpha=0.3, 
                    label='Main Lobe (-3dB)')
        ax.fill_between(theta, 0, normalized_pattern, 
                    where=side_lobe_mask,
                    color='#ff9800', alpha=0.2, 
                    label='Side Lobes')
        
        # Add dB circles with clear annotations
        db_levels = [-3, -6, -10, -20, -30, -40]
        for db in db_levels:
            circle = plt.Circle((0, 0), 40 + db,
                            fill=False,
                            color='white',
                            linestyle='--',
                            alpha=0.3)
            ax.add_artist(circle)

            if db in [-3, -10, -20]:
                ax.text(np.pi/4, 40 + db,
                    f'{db} dB',
                    color='white',
                    ha='left',
                    va='bottom',
                    bbox=dict(facecolor='#2d2d2d',
                            alpha=0.7,
                            edgecolor='none'))
        
        #display key metrics
        half_power = -3
        idx_above = np.where(pattern_db > half_power)[0]
        if len(idx_above) > 0:
            beam_width = np.abs(np.degrees(theta[idx_above[-1]] - theta[idx_above[0]]))
            metrics_text = (
                f'Key Metrics:\n'
                f'• Beam Width]: {beam_width:.1f}°\n'
                f'• Directivity: {10*np.log10(1/beam_width*180/np.pi):.1f} dB'
            )
            ax.text(np.pi/2, 45, metrics_text,
                    color='white',
                    ha='left',
                    va='top',
                    bbox=dict(facecolor='#2d2d2d',
                            alpha=0.9,
                            edgecolor='#404040',
                            boxstyle='round,pad=0.5'))
            
            # Add beam width annotation
            ax.annotate('',
                    xy=(theta[idx_above[0]], normalized_pattern[idx_above[0]]),
                    xytext=(theta[idx_above[-1]], normalized_pattern[idx_above[-1]]),
                    arrowprops=dict(arrowstyle='<->',
                                    color='white',
                                    alpha=0.7))
        
        # Enhanced angle markers
        angles = np.arange(0, 360, 15)
        ax.set_xticks(np.radians(angles))
        ax.set_xticklabels([f'{int(ang)}°' for ang in angles],
                        fontsize=10,
                        color='white')
        
        # Mark steering angles with clear indicators
        for unit in self.array_units:
            if unit.enabled and unit.steering_angle != 0:
                angle = np.radians(unit.steering_angle)
                # Add steering line
                ax.plot([angle, angle], [0, 40],
                    color='#ff9800',
                    linestyle='--',
                    linewidth=2,
                    alpha=0.7,
                    label=f'Steering {unit.steering_angle}°')
                # Add steering arc indicator
                arc = np.linspace(angle-np.pi/12, angle+np.pi/12, 100)
                ax.plot(arc, np.ones_like(arc)*40,
                    color='#ff9800',
                    alpha=0.3)
        
        # Enhanced grid with better visibility
        ax.grid(True, color='white', alpha=0.1, linestyle=':')
        
        # Set plot limits and title
        ax.set_ylim(0, 45)
        ax.set_title('Beam Pattern Analysis',
                    color='white',
                    pad=20,
                    fontsize=14,
                    fontweight='bold')
    
        # Final styling
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white')
        
        self.pattern_canvas.draw()
        
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
        self.array_fig.tight_layout(pad=1.5)
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
                            "num_elements": 64,
                            "element_spacing": 0.5,
                            "steering_angle": 0,
                            "geometry_type": "Linear",
                            "curvature_factor": 1.0,
                            "operating_freqs": [28000],
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
                            "num_elements": 128,
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
            },
            ScenarioType.ABLATION: {
                "description": "Focused Ultrasound Ablation (1 MHz)",
                "params": {
                    "units": [
                        {
                            "num_elements": 32,
                            "element_spacing": 1.0,
                            "steering_angle": -30,
                            "geometry_type": "Linear",
                            "curvature_factor": 1.0,
                            "operating_freqs": [1],
                            "x_pos": -5,
                            "y_pos": 0,
                            
                        },
                        {
                            "num_elements": 32,
                            "element_spacing": 1.0,
                            "steering_angle": 30,
                            "geometry_type": "Linear",
                            "curvature_factor": 1.0,
                            "operating_freqs": [1],
                            "x_pos": 5,
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

        # Add geometry type control
        self.geometry_type = QComboBox()
        self.geometry_type.addItems(["Linear", "Curved"])
        self.geometry_type.currentTextChanged.connect(self.update_unit_parameters)
        unit_layout.addRow("Array Type:", self.geometry_type)

        # Position controls
        self.unit_x = QDoubleSpinBox()
        self.unit_x.setRange(-20, 20)
        self.unit_x.valueChanged.connect(self.update_unit_position)
        unit_layout.addRow("X Position:", self.unit_x)

        self.unit_y = QDoubleSpinBox()
        self.unit_y.setRange(-20, 20)
        self.unit_y.valueChanged.connect(self.update_unit_position)
        unit_layout.addRow("Y Position:", self.unit_y)

        # Unit parameters
        self.unit_elements = QSpinBox()
        self.unit_elements.setRange(1, 128)
        self.unit_elements.setValue(16)  # Set default value
        self.unit_elements.valueChanged.connect(self.update_unit_parameters)
        unit_layout.addRow("Elements:", self.unit_elements)

        self.unit_spacing = QDoubleSpinBox()
        self.unit_spacing.setRange(0.1, 10.0)
        self.unit_spacing.setValue(0.5)  # Set default value
        self.unit_spacing.valueChanged.connect(self.update_unit_parameters)
        unit_layout.addRow("Spacing:", self.unit_spacing)

        self.unit_steering = QDoubleSpinBox()
        self.unit_steering.setRange(-90, 90)
        self.unit_steering.valueChanged.connect(self.update_unit_parameters)
        unit_layout.addRow("Steering:", self.unit_steering)


        # Replace curvature with curvature factor
        self.unit_curvature = QDoubleSpinBox()
        self.unit_curvature.setRange(0, 2)
        self.unit_curvature.setValue(1)
        self.unit_curvature.setSingleStep(0.1)
        self.unit_curvature.valueChanged.connect(self.update_unit_parameters)
        unit_layout.addRow("Curvature Factor:", self.unit_curvature)

        # Add frequency controls
        freq_group = QGroupBox("Frequencies")
        freq_layout = QVBoxLayout()
        
        self.freq_list = QListWidget()
        self.freq_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                min-height: 100px;
            }
        """)
        freq_layout.addWidget(self.freq_list)
        
        freq_controls = QHBoxLayout()
        
        self.freq_input = QDoubleSpinBox()
        self.freq_input.setRange(1, 1000)
        self.freq_input.setValue(100)
        self.freq_input.setSuffix(" MHz")
        freq_controls.addWidget(self.freq_input)
        
        add_freq_btn = ModernButton("+")
        add_freq_btn.setFixedWidth(40)
        add_freq_btn.clicked.connect(self.add_frequency)
        freq_controls.addWidget(add_freq_btn)
        
        remove_freq_btn = ModernButton("-")
        remove_freq_btn.setFixedWidth(40)
        remove_freq_btn.clicked.connect(self.remove_frequency)
        freq_controls.addWidget(remove_freq_btn)
        
        freq_layout.addLayout(freq_controls)
        freq_group.setLayout(freq_layout)
        unit_layout.addRow("Operating Frequencies:", freq_group)

        unit_controls.setLayout(unit_layout)
        units_layout.addWidget(unit_controls)

        units_widget.setLayout(units_layout)
        units_dock.setWidget(units_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, units_dock)


    def add_frequency(self):
        freq = self.freq_input.value()
        self.freq_list.addItem(f"{freq} MHz")
        
        # Update unit if one is selected
        current_item = self.units_list.currentItem()
        if current_item:
            unit_id = current_item.data(Qt.UserRole)
            unit = next((u for u in self.array_units if u.id == unit_id), None)
            if unit:
                unit.operating_freqs.append(freq)
                self.update_pattern()

    def remove_frequency(self):
        current_row = self.freq_list.currentRow()
        if current_row >= 0:
            self.freq_list.takeItem(current_row)
            
            # Update unit if one is selected
            current_item = self.units_list.currentItem()
            if current_item:
                unit_id = current_item.data(Qt.UserRole)
                unit = next((u for u in self.array_units if u.id == unit_id), None)
                if unit:
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
        self.freq_list.clear()
        self.geometry_type.setCurrentText("Linear")

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
                
                # Re-enable signals
                for control in [self.unit_x, self.unit_y, self.unit_elements,
                                self.unit_spacing, self.unit_steering, 
                                self.unit_curvature, self.geometry_type]:
                    control.blockSignals(False)
                    
                # Update frequency list
                self.freq_list.clear()
                for freq in unit.operating_freqs:
                    self.freq_list.addItem(f"{freq} MHz")
                
                self.add_edit_button.setText("Exit Edit Mode")
                self.editing_mode = True

    def update_unit_parameters(self):
        """Update selected unit parameters in real-time"""
        current_item = self.units_list.currentItem()
        if current_item and self.array_units and self.editing_mode:
            unit_id = current_item.data(Qt.UserRole)
            unit = next((u for u in self.array_units if u.id == unit_id), None)
            if unit:
                # Update all unit parameters
                unit.num_elements = self.unit_elements.value()
                unit.element_spacing = self.unit_spacing.value()
                unit.steering_angle = self.unit_steering.value()
                unit.geometry_type = self.geometry_type.currentText()
                unit.curvature_factor = self.unit_curvature.value()
                # Update frequencies
                unit.operating_freqs = [float(self.freq_list.item(i).text().replace(" MHz", "")) 
                                        for i in range(self.freq_list.count())]
                # Always update pattern
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

    def update_units_list(self):
        self.units_list.clear()
        for unit in self.array_units:
            item = QListWidgetItem(f"Unit {unit.id}")
            item.setData(Qt.UserRole, unit.id)
            self.units_list.addItem(item)

    def add_array_unit(self):
        # Get current frequencies from list
        frequencies = [float(self.freq_list.item(i).text().replace(" MHz", "")) 
                    for i in range(self.freq_list.count())]
        if not frequencies:  # If no frequencies, use default
            frequencies = [self.freq_input.value()]
            
        unit = ArrayUnit(
            id=self.current_unit_id,
            x_pos=self.unit_x.value(),
            y_pos=self.unit_y.value(),
            num_elements=self.unit_elements.value(),
            element_spacing=self.unit_spacing.value(),
            steering_angle=self.unit_steering.value(),
            geometry_type=self.geometry_type.currentText(),
            curvature_factor=self.unit_curvature.value(),
            operating_freqs=frequencies.copy(),  # Make a copy of frequencies
            enabled=True
        )
        self.array_units.append(unit)
        self.current_unit_id += 1
        #exit edit mode
        self.editing_mode = False
        self.add_edit_button.setText("Add Unit")
        self.clear_unit_controls()


        self.update_units_list()
        self.update_pattern()

    def remove_array_unit(self, unit_id: int):
        self.array_units = [u for u in self.array_units if u.id != unit_id]
        self.update_pattern()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BeamformingSimulator()
    window.show()
    sys.exit(app.exec_())
