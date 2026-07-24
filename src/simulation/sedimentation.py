"""
Implémente la vitesse de sédimentation d'une particule sphérique dans le fluide de digestion, 
à partir de la force nette de flottaison calculée à l'increment 3.3 

Deux fonctions sont fournies :

1. stokes_settling_velocity() : la loi de Stokes donnée par le cahier des charges :

        v_s = (2/9) * r^2 * (rho_p - rho_f) * g / mu

    Cette formule n'est physiquement valide qu'en régime laminaire autour de la particule, ce qui correspond à l'hypothèse 2.7 du cdc.
    C'est la fonction utilisée par défaut dans particle_motion.py, pour rester fidèle au cahier des charges.

    
2.  corrected_settling_velocity() : une extension du cdc (celui-ci ne fournit pas de formule pour Re_p >= 1). Ajoutée
    parce que certaines particules (grosses et/ou denses) donnent un Re_p bien supérieur à 1 avec la vitesse de Stokes, 
    ce qui rend la loi de Stokes pure physiquement incorrecte pour elles.
    
   Si Re_p < 1, corrected_settling_velocity() redonne le même résultat que stokes_settling_velocity().
"""

from __future__ import annotations
import math

from src.models.particle_type import ParticleType
from src.models.operating_conditions import OperatingConditions
from .buoyancy import effective_density_difference, GRAVITY_M_S2

INCH_TO_M = 0.0254

""" Vitesse de sédimentation de Stokes """
def stokes_settling_velocity(particle_type: ParticleType, operating_conditions: OperatingConditions) -> float:
    """
    Vitesse de sédimentation de Stokes (m/s), du cdc :

        v_s = (2/9) * r^2 * (rho_p - rho_f) * g / mu

    Valide uniquement en régime laminaire
    Utilise effective_density_difference()

    NOTE : particle_type.particle_size est interprété comme le rayon r (m).
    v_s > 0 signifie que la particule sédimente (rho_p > rho_f), v_s < 0 qu'elle flotte.
    """
    r = (particle_type.particle_size * INCH_TO_M)/2
    delta_rho = effective_density_difference(particle_type, operating_conditions)
    mu = operating_conditions.fluid_viscosity

    if mu <= 0:
        raise ValueError("La viscosité du fluide doit être strictement positive.")

    return (2.0 / 9.0) * (r ** 2) * delta_rho * GRAVITY_M_S2 / mu


"""Validité du régime de Stokes"""
def particle_reynolds_number(velocity_m_s: float, particle_type: ParticleType, operating_conditions: OperatingConditions) -> float:
    """
    Nombre de Reynolds particulaire : Re_p = rho_f * |v| * diam / mu

    Utilisé pour vérifier la validité de la loi de Stokes et pour choisir la corrélation de coefficient de traînée appropriée
    """
    diameter =(particle_type.particle_size * INCH_TO_M)
    rho_f = operating_conditions.fluid_density
    mu = operating_conditions.fluid_viscosity
    if mu <= 0:
        raise ValueError("La viscosité du fluide doit être strictement positive.")
    return rho_f * abs(velocity_m_s) * diameter / mu


def is_stokes_regime_valid(velocity_m_s: float, particle_type: ParticleType, operating_conditions: OperatingConditions, re_threshold: float = 1.0) -> bool:
    """
    Indique si la loi de Stokes est physiquement valide pour cette particule, c'est-à-dire si Re_p < re_threshold
    """
    re = particle_reynolds_number(velocity_m_s, particle_type, operating_conditions)
    return re < re_threshold


""" Coefficient de traînée et vitesse corrigée """
def _drag_coefficient(re: float) -> float:
    """
    Coefficient de traînée Cd(Re_p) d'une sphère :
        Re_p < 1          : Cd = 24 / Re_p  
        1 <= Re_p < 1000  : Cd = (24/Re_p) * (1 + 0.15 * Re_p^0.687) 
        Re_p >= 1000      : Cd = 0.44   
    """
    if re <= 0:
        return float("inf")
    if re < 1.0:
        return 24.0 / re
    elif re < 1000.0:
        return (24.0 / re) * (1.0 + 0.15 * re ** 0.687)
    else:
        return 0.44


def corrected_settling_velocity(particle_type: ParticleType, operating_conditions: OperatingConditions,  max_iterations: int = 50, tolerance: float = 1e-9) -> float:
    """
    Vitesse de sédimentation corrigée, valable au-delà du régime de Stokes pur. Résout itérativement l'équilibre des forces à la vitesse terminale :
        (rho_p - rho_f) * V * g = Cd(Re_p) * 0.5 * rho_f * A * v^2

    où V est le volume de la particule (sphère) et A = pi*r^2 sa surface projetée.
    Se réduit à la formule de Stokes du cdc lorsque Re_p < 1.

    Retourne une vitesse signée (positive = sédimente, négative = flotte), par cohérence avec stokes_settling_velocity().
    """
    r = (particle_type.particle_size * INCH_TO_M)/2
    delta_rho = effective_density_difference(particle_type, operating_conditions)
    rho_f = operating_conditions.fluid_density
    mu = operating_conditions.fluid_viscosity

    if mu <= 0:
        raise ValueError("La viscosité du fluide doit être strictement positive.")
    if delta_rho == 0:
        return 0.0

    sign = 1.0 if delta_rho > 0 else -1.0
    abs_delta_rho = abs(delta_rho)
    area = math.pi * r ** 2
    volume = (4.0 / 3.0) * math.pi * r ** 3

    # Estimation initiale : vitesse de Stokes (exacte si Re_p < 1)
    v = abs((2.0 / 9.0) * (r ** 2) * abs_delta_rho * GRAVITY_M_S2 / mu)

    for _ in range(max_iterations):
        re = rho_f * v * (2.0 * r) / mu
        cd = _drag_coefficient(re)
        if cd == float("inf") or cd <= 0:
            break
        v_new = math.sqrt((2.0 * abs_delta_rho * volume * GRAVITY_M_S2) / (cd * rho_f * area))
        if abs(v_new - v) < tolerance:
            v = v_new
            break
        v = v_new

    return sign * v