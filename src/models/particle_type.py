from dataclasses import dataclass

"""Classe définissant les particules"""
@dataclass
class ParticleType : 
    particle_density : float
    particle_size : float
    count : int 