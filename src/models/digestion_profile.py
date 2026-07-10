from dataclasses import dataclass

@dataclass
class DigestionProfile:
    profile_name: str
    enzyme_flow: float
    enzyme_entry_period: float
    simulation_duration: float
    time_step: float
    transition_flow: float