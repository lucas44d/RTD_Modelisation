from __future__ import annotations
from typing import List, Dict

from src.models.system import DigestionSystem
from src.models.particle_type import ParticleType
from src.models.meal_parameter import MealParameter

from .topology import tubular_velocity_at, cstr_outflow_rate
from .particle_motion import (
    Particle,
    generate_particles_from_meal,
    update_position_tubular,
    has_exited_tubular_reactor,
    transition_to_reactor,
    mark_particle_exit,
    attempt_cstr_exit,
)
from .sedimentation import stokes_settling_velocity, is_stokes_regime_valid

# Ordre des réacteurs tubulaires (R3 -> R4 -> R5), utilisé pour les transitions
TUBULAR_CHAIN_NAMES = ["R3 - Duodénum", "R4 - Jéjunum", "R5 - Iléon"]

"""
    Détermine, pour chaque type de particule, s'il faut utiliser la vitesse de sédimentation corrigée 
    plutôt que la loi de Stokes pure, selon la validité du régime 
 
    Retourne {id(particle_type): bool} (True = utiliser la version corrigée).
"""
def compute_settling_velocity_choices(particle_types: List[ParticleType], operating_conditions) -> Dict[int, bool]:
    choices = {}
    for pt in particle_types:
        vs = stokes_settling_velocity(pt, operating_conditions)
        valide = is_stokes_regime_valid(vs, pt, operating_conditions)
        choices[id(pt)] = not valide
    return choices
 

"""Fait avancer une particule d'un pas de temps dt_s, au temps t"""
def step_particle(particle: Particle, system: DigestionSystem, t: float, dt_s: float, use_corrected_by_type: Dict[int, bool], reactors_by_name: dict) -> None:
    if not particle.active or t < particle.entry_time_s:
        return
 
    if particle.current_reactor == "R1 - Estomac":
        q_out = cstr_outflow_rate(system, "R1 - Estomac", t)
        if attempt_cstr_exit(particle, q_out, system.r1_stomach.volume, dt_s):
            transition_to_reactor(particle, "R2 - Préduodénum")
 
    elif particle.current_reactor == "R2 - Préduodénum":
        q_out = cstr_outflow_rate(system, "R2 - Préduodénum", t)
        if attempt_cstr_exit(particle, q_out, system.r2_preduodenum.volume, dt_s):
            transition_to_reactor(particle, "R3 - Duodénum")
 
    elif particle.current_reactor in TUBULAR_CHAIN_NAMES:
        reactor = reactors_by_name[particle.current_reactor]
        u = tubular_velocity_at(system, reactor, t)
        use_corrected = use_corrected_by_type.get(id(particle.particle_type), False)
        update_position_tubular(
            particle, u_m_s=u, operating_conditions=system.operating_conditions,
            dt_s=dt_s, use_corrected_velocity=use_corrected,
        )
 
        if has_exited_tubular_reactor(particle, reactor):
            idx = TUBULAR_CHAIN_NAMES.index(particle.current_reactor)
            if idx + 1 < len(TUBULAR_CHAIN_NAMES):
                transition_to_reactor(particle, TUBULAR_CHAIN_NAMES[idx + 1])
            else:
                mark_particle_exit(particle, t)
 
 
def run_population_simulation(system: DigestionSystem, meal: MealParameter, dt_s: float, max_t_s: float, entry_time_s: float = 0.0, starting_reactor: str = "R1 - Estomac") -> List[Particle]:
    """
    Simule toute la population de particules d'un repas à travers le système, depuis entry_time_s jusqu'à leur sortie ou max_t_s
 
    Structure : à chaque pas de temps, toutes les particules actives sont mises à jour nécessaire pour 
    calculer des statistiques d'ensemble à un instant t donné
 
    Retourne la liste des Particle (residence_time_s rempli pour celles qui ont terminé leur traversée, None pour celles encore dans le système).
    """
    use_corrected_by_type = compute_settling_velocity_choices(meal.particles, system.operating_conditions)
    particles = generate_particles_from_meal(meal, entry_time_s=entry_time_s, starting_reactor=starting_reactor)
    reactors_by_name = {r.name: r for r in system.reactors}
 
    t = entry_time_s
    while t < max_t_s and any(p.active for p in particles):
        t += dt_s
        for particle in particles:
            step_particle(particle, system, t, dt_s, use_corrected_by_type, reactors_by_name)
 
    return particles