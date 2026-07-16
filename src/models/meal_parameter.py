from dataclasses import dataclass,field
from .particle_type import ParticleType

""""Classe qui définit ce que sont les paramètres de repas"""
@dataclass
class MealParameter:
    meal_flow: float
    meal_entry_period: float
    viscosity: float
    total : int
    particles : list[ParticleType] = field(default_factory=list)
    

    """Fonction qui permet de rendre l'affichage plus propre"""
    def __str__(self):
        particles_str = "\n".join(
            f"  - {particle}" for particle in self.particles
        )

        return (
            f"Débit d'entrée des repas : {self.meal_flow}\n"
            f"Période d'entrée des repas : {self.meal_entry_period}\n"
            f"Viscosité : {self.viscosity}\n"
            f"Particules :\n{particles_str}\n"
            f"Total des particules : {int(self.total)}"
        )