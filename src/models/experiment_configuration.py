from dataclasses import dataclass

from src.models.digestion_profile import DigestionProfile
from src.models.simulation_parameter import SimulationParameter
from src.models.meal_parameter import MealParameter

@dataclass
class ExperimentConfiguration:
    digestion_profile: DigestionProfile
    simulation_parameter: SimulationParameter
    meal_parameter: MealParameter