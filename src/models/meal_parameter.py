from dataclasses import dataclass

""""Classe qui définit ce que sont les paramètres de repas"""
@dataclass
class MealParameter:
    meal_flow: float
    meal_entry_period: float
    particle_size: float
    particle_density: float
    viscosity: float