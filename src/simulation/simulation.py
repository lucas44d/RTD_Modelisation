from src.simulation.topology import tubular_velocity_at, cstr_outflow_rate
from src.simulation.particle_motion import (
    update_position_tubular,
    has_exited_tubular_reactor,
    transition_to_reactor,
    mark_particle_exit,
    attempt_cstr_exit,
)
from src.simulation.buoyancy import (
    gravity_force_n,
    archimedes_buoyancy_force_n,
    net_vertical_force_n,
)
from src.simulation.sedimentation import (
    stokes_settling_velocity,
    particle_reynolds_number,
    is_stokes_regime_valid,
)
from PySide6.QtWidgets import QApplication
from src.visualization.gui import MainWindow


# Ordre des réacteurs tubulaires (R3 -> R4 -> R5), utilisé pour les transitions
TUBULAR_CHAIN_NAMES = ["R3 - Duodénum", "R4 - Jéjunum", "R5 - Iléon"]

def print_particle_physics_diagnostics(particle_types, operating_conditions) -> dict:
    """
    Affiche, pour chaque type de particule du repas, les forces en jeu (poids, poussée d'Archimède, force nette) et la validité du régime de Stokes
 
    Retourne un dict {id(particle_type): bool} indiquant, pour chaque type de particule, s'il faut utiliser la vitesse de sédimentation corrigée plutôt que Stokes pur
    """
    use_corrected = {}
    print("____Diagnostic physique des particules____ ")
    for pt in particle_types:
        f_g = gravity_force_n(pt)
        f_a = archimedes_buoyancy_force_n(pt, operating_conditions)
        f_net = net_vertical_force_n(pt, operating_conditions)
        vs = stokes_settling_velocity(pt, operating_conditions)
        re = particle_reynolds_number(vs, pt, operating_conditions)
        valide = is_stokes_regime_valid(vs, pt, operating_conditions)
        use_corrected[id(pt)] = not valide
 
        comportement = "sédimente" if f_net > 0 else ("flotte" if f_net < 0 else "neutre")
        formule = "Stokes " if valide else "corrigée"
        print(f"  rho={pt.particle_density:.0f} kg/m3, r={pt.particle_size * 1000:.3f} mm : "
              f"F_g={f_g:.2e} N, F_a={f_a:.2e} N, F_net={f_net:.2e} N ({comportement}) | "
              f"Re_p={re:.1f} -> formule utilisée : {formule}")
    print()
    return use_corrected
 
 
def step_particle(particle, system, t: float, dt_s: float, use_corrected_by_type: dict, reactors_by_name: dict) -> None:
    """Fait avancer une particule d'un pas de temps dt_s, au temps t"""
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
 
 
def run_simulation(system, particles: list, use_corrected_by_type: dict, dt_s: float, max_t_s: float) -> list:
    """
    Boucle principale de simulation : à CHAQUE pas de temps, toutes les particules actives sont mises à jour 
    S'arrête dès que toutes les particules sont sorties, ou que max_t_s est atteint.
    """
    reactors_by_name = {r.name: r for r in system.reactors}
    t = 0.0
 
    while t < max_t_s and any(p.active for p in particles):
        t += dt_s
        for particle in particles:
            step_particle(particle, system, t, dt_s, use_corrected_by_type, reactors_by_name)
 
    return particles