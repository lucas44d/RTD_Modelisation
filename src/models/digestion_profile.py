"""
    Auteur : Lucas Durand
    Définition de la classe DigestionProfile, qui représente le profil de digestion du système IViDiS.
    Implémentée grâce au fichier Excel de configuration.
"""
from dataclasses import dataclass

""""Classe qui définit ce qu'est un profil de digestion"""
@dataclass
class DigestionProfile:
    profile_name : str
    reciprocating_flow : float
    reciprocating_action_duration : float
    reciprocating_wait_duration : float
    mixing_speed_R1 : dict
    mixing_speed_R2 : float
    emulsion_mixing_speed : float 
    emulsion_mixing_period : float 
    reciprocating_stiring_speed : float # Vitesse d'agitation de l'agitateur à pâle
    reciprocation_striring_period : float # Période d'agitation de l'agitateur à pâle
