"""
Implémente le calcul de la poussée d'Archimède agissant sur une particule immergée dans le fluide de digestion

Rappel physique (particule sphérique de rayon r) :

    Poids de la particule :   F_g = rho_p * V * g  (vers le bas)
    Poussée d'Archimède :  F_a = rho_f * V * g  (vers le haut)
    Force nette (submergée) :  F_net = F_g - F_a = (rho_p - rho_f) * V * g

        F_net > 0 : la particule est plus dense que le fluide -> elle coule
        F_net < 0 : la particule est moins dense que le fluide -> elle flotte
        F_net = 0 : la particule est en suspension neutre (densité égale)
"""

from __future__ import annotations
import math

from src.models.particle_type import ParticleType
from src.models.operating_conditions import OperatingConditions


GRAVITY_M_S2 = 9.81


def sphere_volume_m3(radius_m: float) -> float:
    """Volume d'une particule sphérique (m3), à partir de son rayon (m)"""
    return (4.0 / 3.0) * math.pi * radius_m ** 3


def gravity_force_n(particle_type: ParticleType) -> float:
    """
    Poids de la particule (N) : F_g = rho_p * V * g
    Convention : valeur positive, dirigée vers le bas
    """
    volume = sphere_volume_m3(particle_type.particle_size)
    return particle_type.particle_density * volume * GRAVITY_M_S2


def archimedes_buoyancy_force_n(particle_type: ParticleType, operating_conditions: OperatingConditions) -> float:
    """
    Poussée d'Archimède (N) : F_a = rho_f * V * g
    Convention : valeur positive, dirigée vers le haut (opposée au poids)
    """
    volume = sphere_volume_m3(particle_type.particle_size)
    return operating_conditions.fluid_density * volume * GRAVITY_M_S2


def net_vertical_force_n(particle_type: ParticleType, operating_conditions: OperatingConditions) -> float:
    """
    Force verticale nette agissant sur la particule immergée (N), avant prise en compte de la résistance visqueuse :

    F_net = F_g - F_a = (rho_p - rho_f) * V * g

    F_net > 0 : la particule tend à couler (plus dense que le fluide)
    F_net < 0 : la particule tend à flotter (moins dense que le fluide)
    F_net = 0 : suspension neutre (densité égale au fluide)
    """
    return gravity_force_n(particle_type) - archimedes_buoyancy_force_n(particle_type, operating_conditions)


def effective_density_difference(particle_type: ParticleType,
                                  operating_conditions: OperatingConditions) -> float:
    """
    Différence de densité effective (kg/m3) : rho_p - rho_f
    C'est cette différence qui apparaît directement dans la loi de Stokes; elle est mathématiquement équivalente à
    net_vertical_force_n() divisée par (V * g), mais évite de refaire le calcul du volume à chaque appel
    """
    return particle_type.particle_density - operating_conditions.fluid_density