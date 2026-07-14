from dataclasses import dataclass,field
from .particle_type import ParticleType

""""Classe qui définit ce que sont les paramètres de repas"""
@dataclass
class MealParameter:
    meal_flow: float
    meal_entry_period: float
    viscosity: float
    particles : list[ParticleType] = field(default_factory=list)