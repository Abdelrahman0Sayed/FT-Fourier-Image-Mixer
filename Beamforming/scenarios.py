from enum import Enum
from typing import Dict, List, Optional
import json
from dataclasses import dataclass
from array_unit import ArrayUnit

class ScenarioType(Enum):
    FiveG = "5G Communications"
    ULTRASOUND = "Medical Ultrasound"  
    ABLATION = "Tumor Ablation"

@dataclass
class Scenario:
    name: str
    description: str
    units: List[Dict]

class ScenarioManager:
    def __init__(self):
        self.scenarios: Dict[ScenarioType, Scenario] = self._setup_preset_scenarios()
        self.current_scenario: Optional[Scenario] = None
        self.current_unit_id = 0

    def save_scenario(self, filename: str, scenario: Scenario) -> None:
        """Save a scenario to a JSON file"""
        scenario_data = {
            "name": scenario.name,
            "description": scenario.description, 
            "units": [
                {
                    "name": unit.name,
                    "num_elements": unit.num_elements,
                    "element_spacing": unit.element_spacing,
                    "steering_angle": unit.steering_angle,  
                    "geometry_type": unit.geometry_type,
                    "curvature_factor": unit.curvature_factor,
                    "operating_freqs": unit.operating_freqs,
                    "x_pos": unit.x_pos,
                    "y_pos": unit.y_pos
                }
                for unit in scenario.units
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(scenario_data, f, indent=4)

    def load_scenario(self, filename: str) -> Scenario:
        """Load a scenario from a JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
            
        scenario = Scenario(
            name=data["name"],
            description=data["description"],
            units=[{
                "name": unit["name"],
                "num_elements": unit["num_elements"], 
                "element_spacing": unit["element_spacing"],
                "steering_angle": unit["steering_angle"],
                "geometry_type": unit["geometry_type"],
                "curvature_factor": unit["curvature_factor"],
                "operating_freqs": unit["operating_freqs"],
                "x_pos": unit["x_pos"],
                "y_pos": unit["y_pos"]
            } for unit in data["units"]]
        )
        return scenario

    def load_preset_scenario(self, scenario_type: ScenarioType) -> List[ArrayUnit]:
        """Load a preset scenario and return array units"""
        if scenario_type not in self.scenarios:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
            
        scenario = self.scenarios[scenario_type]
        array_units = []
        
        for unit_data in scenario.units:
            array_unit = ArrayUnit(
                id=self.current_unit_id,
                name=unit_data["name"],
                num_elements=unit_data["num_elements"],
                element_spacing=unit_data["element_spacing"], 
                steering_angle=unit_data["steering_angle"],
                geometry_type=unit_data["geometry_type"],
                curvature_factor=unit_data["curvature_factor"],
                operating_freqs=unit_data["operating_freqs"],
                x_pos=unit_data["x_pos"],
                y_pos=unit_data["y_pos"],
                enabled=True
            )
            array_units.append(array_unit)
            self.current_unit_id += 1
            
        return array_units

    def _setup_preset_scenarios(self) -> Dict[ScenarioType, Scenario]:
        """Initialize preset scenarios"""
        return {
            ScenarioType.FiveG: Scenario(
                name="5G Communications",
                description="5G Beamforming Array (28 GHz)",
                units=[{
                    "name": "5G Base Station",
                    "num_elements": 16,
                    "element_spacing": 0.5,
                    "steering_angle": 0,
                    "geometry_type": "Linear",
                    "curvature_factor": 1.0,
                    "operating_freqs": [2.8],
                    "x_pos": 0,
                    "y_pos": 0
                }]
            ),
            ScenarioType.ULTRASOUND: Scenario(
                name="Medical Ultrasound",
                description="Medical Ultrasound Scanner (5 MHz)",
                units=[{
                    "name": "Ultrasound Probe",
                    "num_elements": 16,
                    "element_spacing": 0.06,
                    "steering_angle": 0,
                    "geometry_type": "Curved", 
                    "curvature_factor": 1.5,
                    "operating_freqs": [0.5],
                    "x_pos": 0,
                    "y_pos": 0
                }]
            ),
            ScenarioType.ABLATION: Scenario(
                name="Tumor Ablation",
                description="Medical Ultrasound Scanner (5 MHz)",
                units=[{
                    "name": "Ultrasound Probe",
                    "num_elements": 20,
                    "element_spacing": 0.25,
                    "steering_angle": 0,
                    "geometry_type": "Curved",
                    "curvature_factor": 1.5,
                    "operating_freqs": [5],
                    "x_pos": 0,
                    "y_pos": 0
                }]
            )
        }