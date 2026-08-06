"""
    Auteur : Lucas Durand
    Définition de la classe ExperimentConfiguration, qui regroupe les paramètres de digestion, de simulation et de repas. 
    Implémentée grâce au fichier Excel de configuration et utilisée pour initialiser la simulation plus simplement.
"""
from dataclasses import dataclass

from src.models.digestion_profile import DigestionProfile
from src.models.simulation_parameter import SimulationParameter
from src.models.meal_parameter import MealParameter

@dataclass
class ExperimentConfiguration:
    digestion_profile: DigestionProfile
    simulation_parameter: SimulationParameter
    meal_parameter: MealParameter