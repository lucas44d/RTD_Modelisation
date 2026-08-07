"""
    Auteur : Lucas Durand
    Définition des paramètres de simulation qui sont importés via le fichier Excel de configuration.
"""
from dataclasses import dataclass

""""Classe qui définit ce que sont les paramètres de simulation"""
@dataclass
class SimulationParameter:
    config_name : str 
    enzyme_volume : float
    enzyme_flow: float
    enzyme_entry_period: float
    simulation_duration: float
    time_step: float
    transition_flow: float