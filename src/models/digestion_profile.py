from dataclasses import dataclass

@dataclass
class DigestionProfile:
    profile_name : str
    reciprocating_flow : float
    reciprocating_period : float
    stiring_speed_R1 : float
    stiring_speed_R2 : float
    emulsion_mixing_speed : float
    emulsion_mixing_period : float
    reciprocating_stiring_speed : float
    reciprocation_striring_period : float
