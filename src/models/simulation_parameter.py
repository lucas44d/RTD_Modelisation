from dataclasses import dataclass

""""Classe qui définit ce que sont les paramètres de simulation"""
@dataclass
class SimulationParameter:
    enzyme_flow: float
    enzyme_entry_period: float
    simulation_duration: float
    time_step: float
    transition_flow: float