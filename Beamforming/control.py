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
from gui import ModernButton, ModernSlider
from array_unit import ArrayUnit

class UnitControlPanel:
    def __init__(self, parent):
        self.parent = parent
        self.editing_mode = False
        self.current_unit_id = 0
        self.array_units = []

    def create_array_units_panel(self):
        # Create dock widget for unit management
        units_dock = QDockWidget("Array Units Manager", self.parent)
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
        self.parent.addDockWidget(Qt.RightDockWidgetArea, units_dock)


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
                self.parent.update_pattern()

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
                    self.parent.update_pattern()



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

    def has_active_units(self):
        return any(u.enabled for u in self.array_units)
    
    def get_active_units(self):
        return [u for u in self.array_units if u.enabled]
    
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
                
                self.parent.update_pattern()

    def update_unit_position(self):
        current_item = self.units_list.currentItem()
        if current_item and self.array_units:
            unit_id = current_item.data(Qt.UserRole)
            unit = next((u for u in self.array_units if u.id == unit_id), None)
            if unit:
                unit.x_pos = self.unit_x.value()
                unit.y_pos = self.unit_y.value()
                self.parent.update_pattern()

    def update_unit_phase(self):
        current_item = self.units_list.currentItem()
        if current_item and self.array_units:
            unit_id = current_item.data(Qt.UserRole)
            unit = next((u for u in self.array_units if u.id == unit_id), None)
            if unit:
                self.parent.update_pattern()

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
        name, ok = QInputDialog.getText(self.parent, "New Unit", "Enter unit name:")
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
            self.parent.update_pattern()

    def update_units_list(self):
        self.units_list.clear()
        for unit in self.array_units:
            item = QListWidgetItem(f"{unit.name}")  # Show unit name instead of "Unit {id}"
            item.setData(Qt.UserRole, unit.id)
            self.units_list.addItem(item)

    def remove_array_unit(self, unit_id: int):
        self.array_units = [u for u in self.array_units if u.id != unit_id]
        self.parent.update_pattern()

    def get_array_positions(self):
        return [(u.x_pos, u.y_pos) for u in self.array_units if u.enabled]
    
    def get_steering_angles(self):
        return [u.steering_angle for u in self.array_units if u.enabled]
    
    def set_edit_mode(self, enabled: bool):
        """Update UI elements for edit mode"""
        self.edit_button.setEnabled(not enabled)
        self.save_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)
        self.add_button.setEnabled(not enabled)
        self.remove_button.setEnabled(not enabled)
        
    def disable_unit_selection(self):
        """Disable unit selection during edit mode"""
        self.units_list.setEnabled(False)
        
    def enable_unit_selection(self):
        """Enable unit selection after edit mode"""
        self.units_list.setEnabled(True)
    
    def clear_selection(self):
        """Clear current unit selection"""
        self.units_list.clearSelection()
        self.current_unit = None
    
    def get_selected_unit(self):
        """Return currently selected unit"""
        current_item = self.units_list.currentItem()
        if current_item:
            unit_id = current_item.data(Qt.UserRole)
            return next((u for u in self.array_units if u.id == unit_id), None)
        return None