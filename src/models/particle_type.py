from dataclasses import dataclass


"""Classe définissant les particules"""
@dataclass
class ParticleType : 
    particle_density : float
    particle_size : float
    count : int 

    def __str__(self):
        return (
            f"Densité={self.particle_density}, "
            f"Taille={self.particle_size}, "
            f"Nombre={int(self.count)}"
        )
