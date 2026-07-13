from dataclasses import dataclass

""""Classe qui définit ce qu'est un profil de digestion"""
@dataclass
class DigestionProfile:
    profile_name : str
    reciprocating_flow : float
    reciprocating_period : float
    mixing_speed_R1 : float
    mixing_speed_R2 : float
    emulsion_mixing_speed : float
    emulsion_mixing_period : float
    reciprocating_stiring_speed : float
    reciprocation_striring_period : float
