"""
Implémente :
    - La vitesse de sédimentation de Stokes
    - Le déplacement des particules par advection (direction x, réacteurs tubulaires) et par sédimentation/flottation (direction z)
    - Une modélisation simplifiée de l'agitation/turbulence dans les réacteurs agités R1/R2, et la sortie stochastique d'une particule d'un CSTR (basée sur le taux de renouvellement du fluide, cf. flow.py)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import random
import math

from src.models.particle_type import ParticleType
from src.models.meal_parameter import MealParameter
from src.models.operating_conditions import OperatingConditions
from .flow import cstr_renewal_rate
from .sedimentation import stokes_settling_velocity, corrected_settling_velocity

GRAVITY_M_S2 = 9.81
FEET_TO_M = 0.3048
INCH_TO_M = 0.0254

"""
Représentation d'une particule individuelle
"""
@dataclass
class Particle:
    """
    x, z : position longitudinale (advection) et verticale (sédimentation), en mètres, au sein du réacteur courant
    current_reactor : nom du réacteur où se trouve la particule
    entry_time_s : temps d'entrée dans le système (t_entrée,i)
    exit_time_s : temps de sortie du système (rempli une fois sortie)
    active : False une fois la particule sortie du système
    
    NOTE : Il peut être possible d'ajouter un id au particules pour les identifier plus facilement pour l'analyse des résultats
    """
    particle_type: ParticleType
    x: float = 0.0
    z: float = 0.0
    current_reactor: str = ""
    entry_time_s: float = 0.0
    exit_time_s: Optional[float] = None 
    active: bool = True

    @property
    def residence_time_s(self) -> Optional[float]:
        """Temps de résidence individuel tau_i = t_sortie - t_entrée"""
        if self.exit_time_s is None:
            return None
        return self.exit_time_s - self.entry_time_s


"""Génère les particules individuellement sans stocker toute la population en mémoire"""
def generate_particles_from_meal(meal: MealParameter, entry_time_s: float = 0.0, starting_reactor: str = "R1 - Estomac") -> List[Particle]:

    particles: List[Particle] = []
    for particle_type in meal.particles:
        for _ in range(int(particle_type.count)):
            particles.append(Particle(particle_type=particle_type, current_reactor=starting_reactor, entry_time_s=entry_time_s))
    return particles


"""Déplacement en réacteur tubulaire (advection + Stokes)"""
def update_position_tubular(particle: Particle, u_m_s: float, operating_conditions: OperatingConditions, dt_s: float, use_corrected_velocity: bool = False) -> None:
    """
    Met à jour la position d'une particule dans un réacteur tubulaire (écoulement piston) :
        x(t+dt) = x(t) + u * dt (advection longitudinale)
        z(t+dt) = z(t) - v_s * dt (sédimentation/flottation verticale)
    """
    if use_corrected_velocity:
        v_s = corrected_settling_velocity(particle.particle_type, operating_conditions)
    else:
        v_s = stokes_settling_velocity(particle.particle_type, operating_conditions)
    particle.x += u_m_s * dt_s
    particle.z -= v_s * dt_s


""" Agitation / sortie stochastique en réacteur agité (R1, R2) """
def apply_agitation_mixing(particle: Particle, rpm: float, dt_s: float, mixing_coefficient: float = 1e-4) -> None:
    """
    Modélise l'effet de l'agitation/turbulence dans un réacteur agité

    CSTR : plutôt que de résoudre un champ de vitesse turbulent complet, la position de la particule est
    perturbée aléatoirement à chaque pas de temps, avec une amplitude proportionnelle à la vitesse d'agitation (rpm).
    Ca reproduit qualitativement une redistribution rapide des particules dans le volume.

    ATTENTION : `mixing_coefficient` est un paramètre empirique sans justification physique forte —> à calibrer avec les données expérimentales une fois disponibles
    """
    kick_amplitude = mixing_coefficient * rpm * dt_s
    particle.z += random.uniform(-kick_amplitude, kick_amplitude)
    particle.x += random.uniform(-kick_amplitude, kick_amplitude)


""" Fonction qui permet de déterminer si une particule peut sortir du réacteur ou non"""
def attempt_cstr_exit(particle: Particle, flow_rate_ml_min: float, volume_ml: float, dt_s: float) -> bool:
    """
    Tire au sort si la particule sort du réacteur agité durant ce pas de temps, en cohérence avec l'hypothèse CSTR :
    la probabilité de sortie durant dt est 1 - exp(-(Q/V)*dt) (processus sans mémoire -> distribution exponentielle des temps de séjour E(t) = (1/tau) e^(-t/tau)).

    Retourne True si la particule doit sortir du réacteur à ce pas de temps.
    """
    rate = cstr_renewal_rate(flow_rate_ml_min, volume_ml)
    if rate == 0:
        return False
    exit_probability = 1.0 - math.exp(-rate * dt_s)
    return random.random() < exit_probability


""" Transitions entre réacteurs (fin de course tubulaire, sortie de CSTR, sortie définitive du système)"""
def has_exited_tubular_reactor(particle: Particle, reactor) -> bool:
    """
    Indique si une particule a atteint la fin d'un réacteur tubulaire par advection longitudinale
    reactor : TubularReactor (utilise reactor.length_ft).
    """
    length_m = reactor.length_ft * FEET_TO_M
    return particle.x >= length_m
 
""" Fait transiter une particule vers le réacteur suivant (tubulaire ->tubulaire, ou CSTR -> tubulaire) """
def transition_to_reactor(particle: Particle, new_reactor_name: str, reset_position: bool = True) -> None:
    """
    reset_position : si True (par défaut), x est remis à 0 pour le nouveau réacteur
    z (sédimentation accumulée) n'est PAS réinitialisé
    """
    particle.current_reactor = new_reactor_name
    if reset_position:
        particle.x = 0.0


""" Marque la sortie définitive d'une particule hors du système (t_sortie,i, utilisé ensuite pour calculer tau_i = t_sortie - t_entrée) """
def mark_particle_exit(particle: Particle, t_s: float) -> None:
    particle.exit_time_s = t_s
    particle.active = False
