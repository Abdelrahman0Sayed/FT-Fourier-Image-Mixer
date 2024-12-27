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
from array_unit import ArrayUnit
from gui import ModernButton, ModernSlider
from scenarios import ScenarioType, ScenarioManager
from control import UnitControlPanel
from visualization import VisualizationManager, VisualizationData
from calc import FieldCalculator
from plot_manager import PlotConfig, PatternPlot, InterferencePlot, ArrayGeometryPlot


class BeamformingSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Beamforming Simulator")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(STYLE_SHEET)
        self.editing_mode = False
        self.edited_unit = None  # Track currently edited unit
        
        
        # Initialize field variables
        self.x_field = np.linspace(-30, 30, 200)
        self.y_field = np.linspace(-30, 30, 200)
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
        self.scenario_manager = ScenarioManager()
        self.array_units: List[ArrayUnit] = []
        self.current_unit_id = 0
        
        self.units_panel = UnitControlPanel(self)
        self.units_panel.create_array_units_panel()

        plot_config = PlotConfig()
        self.visualization_manager = VisualizationManager(
            PatternPlot(self.pattern_fig, plot_config),
            InterferencePlot(self.interference_fig, plot_config),
            ArrayGeometryPlot(self.array_fig, plot_config)
        )
        
        self.field_calculator = FieldCalculator(
            np.linspace(-30, 30, 200),
            np.linspace(-30, 30, 200)
        )

    
    
    ###########################################1.UI Creation##############################################
        
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
        self.pattern_fig = Figure(figsize=(6, 6))
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
        self.interference_fig = Figure(figsize=(6, 6))
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
        
        self.array_fig = Figure(figsize=(12, 6))  # Wider figure
        self.array_fig.patch.set_facecolor('#1e1e1e')
        self.array_canvas = FigureCanvasQTAgg(self.array_fig)
        array_layout.addWidget(self.array_canvas)
        
        array_toolbar = NavigationToolbar2QT(self.array_canvas, array_container)
        array_toolbar.setStyleSheet("background-color: #2d2d2d; color: white;")
        array_layout.addWidget(array_toolbar)

        # Add checkbox for pattern shape
        pattern_controls = QHBoxLayout()
        self.full_pattern_checkbox = QCheckBox("Show Full Pattern")
        self.full_pattern_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border: 2px solid #3a3a3a;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #2196f3;
                border: 2px solid #1976d2;
                border-radius: 4px;
            }
        """)
        self.full_pattern_checkbox.toggled.connect(self.update_pattern)
        pattern_controls.addWidget(self.full_pattern_checkbox)
        pattern_layout.addLayout(pattern_controls)
        
        array_container.setLayout(array_layout)
        array_row.addWidget(array_container, stretch=1)  # Add stretch factor
        
        viz_layout.addLayout(array_row)
        viz_widget.setLayout(viz_layout)
        self.layout.addWidget(viz_widget)

    ###########################################2.Scenario Management##############################################

    def load_preset_scenario(self, scenario_type: ScenarioType):
        """Load a preset scenario"""
        try:
            # Clear existing
            self.array_units.clear()
            self.visualization_manager.clear_all()
            
            # Load and validate new units
            self.array_units = self.scenario_manager.load_preset_scenario(scenario_type)
            if not self.array_units:
                print("No units loaded")
                return
                
            print(f"Loaded {len(self.array_units)} units")
            
            # Update unit panel
            self.current_unit_id = len(self.array_units)
            self.units_panel.array_units = self.array_units  # Ensure panel has reference
            self.units_panel.update_units_list()
            
            # Activate units
            for unit in self.array_units:
                unit.enabled = True
                
            # Force position update
            positions = self.units_panel.get_array_positions()
            if not positions:
                print("Failed to get array positions")
                return
                
            # Get active units
            active_units = self.units_panel.get_active_units()
            if not active_units:
                print("No active units found")
                return
                
            print(f"Processing {len(active_units)} active units")
            
            # Calculate field data
            pattern = self.field_calculator.calculate_pattern(active_units)
            interference = self.field_calculator.calculate_interference(active_units)
            steering_angles = self.units_panel.get_steering_angles()
            
            # Create and validate visualization data
            vis_data = VisualizationData(
                pattern=pattern,
                interference=interference, 
                array_positions=positions,
                theta=np.linspace(-np.pi/2, np.pi/2, 1000),
                x_field=self.x_field,
                y_field=self.y_field,
                steering_angles=steering_angles
            )
            
            # Update plots
            self.visualization_manager.update_all(vis_data)
            
            # Force immediate redraw with flush
            self.pattern_canvas.draw()
            self.pattern_canvas.flush_events()
            
            self.interference_canvas.draw()
            self.interference_canvas.flush_events()
            
            self.array_canvas.draw()
            self.array_canvas.flush_events()
            
            print("Visualization complete")
            
        except Exception as e:
            print(f"Error in scenario loading: {str(e)}")
            import traceback
            traceback.print_exc()

    def update_pattern(self):
        """Update visualization with current array configuration"""
        if not self.units_panel.has_active_units():
            print("No active units found")
            self.visualization_manager.clear_all()
            return

        # Get active units
        active_units = self.units_panel.get_active_units()
        print(f"Active units: {len(active_units)}")
        
        # Calculate patterns
        pattern = self.field_calculator.calculate_pattern(active_units)
        interference = self.field_calculator.calculate_interference(active_units)
        positions = self.units_panel.get_array_positions()
        steering_angles = self.units_panel.get_steering_angles()
        
        print(f"Calculated data:")
        print(f"- Pattern: {pattern.shape if pattern is not None else None}")
        print(f"- Interference: {interference.shape if interference is not None else None}")
        print(f"- Positions: {len(positions) if positions else 0}")
        print(f"- Steering angles: {steering_angles}")
        
        # Create visualization data
        vis_data = VisualizationData(
            pattern=pattern,
            interference=interference,
            array_positions=positions,
            theta=np.linspace(-np.pi/2, np.pi/2, 1000),
            x_field=self.x_field,
            y_field=self.y_field,
            steering_angles=steering_angles
        )
        
        # Update plots
        try:
            self.visualization_manager.update_all(vis_data)
            print("Plots updated successfully")
        except Exception as e:
            print(f"Error updating plots: {str(e)}")

    def save_scenario(self):
        """Save current scenario to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Scenario", "", "JSON Files (*.json)"
        )
        if filename:
            self.scenario_manager.save_scenario(filename, self.array_units)

    def load_scenario(self):
        """Load scenario from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Scenario", "", "JSON Files (*.json)"
        )
        if filename:
            self.array_units = self.scenario_manager.load_scenario(filename)
            self.current_unit_id = len(self.array_units)
            self.units_panel.update_units_list()
            self.update_pattern()

    ###########################################3.Visualization Updates##############################################

    def update_pattern(self):
        if not self.units_panel.has_active_units():
            self.visualization_manager.clear_all()
            return
                
        # Add debug prints    
        pattern = self.field_calculator.calculate_pattern(
            self.units_panel.get_active_units()
        )
        print(f"Pattern shape: {pattern.shape if pattern is not None else None}")
            
        interference = self.field_calculator.calculate_interference(
            self.units_panel.get_active_units()
        )
        print(f"Interference shape: {interference.shape if interference is not None else None}")
            
        positions = self.units_panel.get_array_positions()
        print(f"Number of positions: {len(positions) if positions else 0}")
            
        vis_data = VisualizationData(
            pattern=pattern,
            interference=interference,
            array_positions=positions,
            theta=np.linspace(-np.pi/2, np.pi/2, 1000),
            x_field=self.x_field,
            y_field=self.y_field,
            steering_angles=self.units_panel.get_steering_angles()
        )
            
        self.visualization_manager.update_all(vis_data)
        
        # Force redraw all canvases
        self.pattern_canvas.draw()
        self.interference_canvas.draw()
        self.array_canvas.draw()

    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BeamformingSimulator()
    window.show()
    sys.exit(app.exec_())
