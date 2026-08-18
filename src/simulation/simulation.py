"""
    Auteur : Lucas Durand
    Logique de simulation complète du système IViDiS, avec suivi des volumes et des particules.
    Implémente la simulation de la population de particules d'un repas à travers le système
"""
from __future__ import annotations
from typing import List, Dict
from dataclasses import dataclass, field

from src.models.system import DigestionSystem
from src.models.particle_type import ParticleType
from src.models.meal_parameter import MealParameter

from .topology import tr3_position_delta_m, tubular_velocity_at, cstr_outflow_rate, reactor_inflow_rate
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
from simulation.volume_dynamics import (
    apply_tr3_volume_oscillation,
    update_reactor_volumes,
    inject_meal_into_stomach,
    update_tubular_reactor_volumes,
)

# Ordre des réacteurs tubulaires (R3 -> R4 -> R5), utilisé pour les transitions
TUBULAR_CHAIN_NAMES = ["R3 - Duodénum", "R4 - Jéjunum", "R5 - Iléon"]


@dataclass
class SimulationResult:
    """
    Résultat d'une simulation complète : population de particules (avec
    leurs temps de résidence, cf. increment 3.5) et historique des volumes
    de chaque réacteur au fil du temps (cf. demande utilisateur : courbe
    de suivi des volumes du système).
 
    volume_history : {"t": [...], "R1 - Estomac": [...], ...}, une entrée
    par pas de temps simulé, pour chacun des 5 réacteurs.
    """
    particles: List[Particle]
    volume_history: Dict[str, List[float]] = field(default_factory=dict)



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


"""
    Indique si un débit non nul existe encore quelque part dans le système à l'instant t_s 
    (R1->R2 via T1, R2->R3/R4/R5 via T2, ou injections secondaires comme E1 dans R4/R5)
 
    Sert à détecter que le système a atteint un état stagnant : dans cet
    état, aucune particule active ne peut plus jamais bouger, donc
    continuer la simulation jusqu'à max_t_s ne changerait plus rien
    """
def _system_is_flowing(system: DigestionSystem, t_s: float) -> bool:
    if cstr_outflow_rate(system, "R1 - Estomac", t_s) > 0:
        return True
    if cstr_outflow_rate(system, "R2 - Préduodénum", t_s) > 0:
        return True
    for reactor_name in TUBULAR_CHAIN_NAMES:
        if reactor_inflow_rate(system, reactor_name, t_s) > 0:
            return True
    return False


"""Fait avancer une particule d'un pas de temps dt_s, au temps t"""
def step_particle(particle: Particle, system: DigestionSystem, t: float, dt_s: float, use_corrected_by_type: Dict[int, bool], reactors_by_name: dict) -> None:
    if not particle.active or t < particle.entry_time_s:
        return
 
    if particle.current_reactor == "R1 - Estomac":
        q_out = cstr_outflow_rate(system, "R1 - Estomac", t)
        if attempt_cstr_exit(q_out, system.r1_stomach.volume, dt_s):
            transition_to_reactor(particle, "R2 - Préduodénum")
 
    elif particle.current_reactor == "R2 - Préduodénum":
        q_out = cstr_outflow_rate(system, "R2 - Préduodénum", t)
        if attempt_cstr_exit(q_out, system.r2_preduodenum.volume, dt_s):
            transition_to_reactor(particle, "R3 - Duodénum")
 
    elif particle.current_reactor in TUBULAR_CHAIN_NAMES:
        reactor = reactors_by_name[particle.current_reactor]
        u = tubular_velocity_at(system, reactor, t)
        use_corrected = use_corrected_by_type.get(id(particle.particle_type), False)
        update_position_tubular(
            particle, u_m_s=u, operating_conditions=system.operating_conditions,
            dt_s=dt_s, use_corrected_velocity=use_corrected,
        )

        particle.x += tr3_position_delta_m(system, reactor, t, dt_s)
        particle.x = max(0.0, particle.x)  # ne peut pas reculer avant l'entrée du réacteur
 
 
        if has_exited_tubular_reactor(particle, reactor):
            idx = TUBULAR_CHAIN_NAMES.index(particle.current_reactor)
            if idx + 1 < len(TUBULAR_CHAIN_NAMES):
                transition_to_reactor(particle, TUBULAR_CHAIN_NAMES[idx + 1])
            else:
                mark_particle_exit(particle, t)
 
 
 
def run_population_simulation(system: DigestionSystem, meal: MealParameter, dt_s: float, max_t_s: float,
                               entry_time_s: float = 0.0, starting_reactor: str = "R1 - Estomac",
                               inject_meal_volume: bool = False,
                               record_volume_history: bool = True) -> SimulationResult:
    """
    Simule toute la population de particules d'un repas à travers le système, depuis entry_time_s jusqu'à leur sortie ou max_t_s
 
    Structure : à chaque pas de temps, toutes les particules actives sont mises à jour nécessaire pour 
    calculer des statistiques d'ensemble à un instant t donné
 
    Retourne la liste des Particle (residence_time_s rempli pour celles qui ont terminé leur traversée, None pour celles encore dans le système).
    """
    use_corrected_by_type = compute_settling_velocity_choices(meal.particles, system.operating_conditions)
    particles = generate_particles_from_meal(meal, entry_time_s=entry_time_s, starting_reactor=starting_reactor)
    reactors_by_name = {r.name: r for r in system.reactors}
 
    volume_history: Dict[str, List[float]] = {"t": []}
    if record_volume_history:
        for r in system.reactors:
            volume_history[r.name] = []
 
    def _record_volumes(t_val: float) -> None:
        volume_history["t"].append(t_val)
        for r in system.reactors:
            current = r.current_volume_ml if hasattr(r, "current_volume_ml") else r.volume
            volume_history[r.name].append(current)
 
    if record_volume_history:
        _record_volumes(entry_time_s)
 
    t = entry_time_s
    system_has_flowed = False
    while t < max_t_s and any(p.active for p in particles):
        t += dt_s
 
        # Mise à jour des volumes de R1/R2 (bilan de matière), et
        # remplissage en cascade de R3->R4->R5 (poussé par R1/R2), une fois par pas de temps (pas par particule) 
        update_reactor_volumes(system, t, dt_s)
        if inject_meal_volume:
            inject_meal_into_stomach(system, meal, t, dt_s, meal_start_time_s=entry_time_s)
        update_tubular_reactor_volumes(system, t, dt_s)
        apply_tr3_volume_oscillation(system, t, dt_s)
 
        for particle in particles:
            step_particle(particle, system, t, dt_s, use_corrected_by_type, reactors_by_name)
 
        if record_volume_history:
            _record_volumes(t)

        
        # Arrêt anticipé si le système est devenu stagnant
        if _system_is_flowing(system, t):
            system_has_flowed = True
        elif system_has_flowed:
            break
        
 
    return SimulationResult(particles=particles, volume_history=volume_history)