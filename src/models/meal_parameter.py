from dataclasses import dataclass

@dataclass
class MealParameter:
    meal_flow: float
    meal_entry_period: float
    particle_size: float
    particle_density: float
    viscosity: float