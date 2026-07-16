from pathlib import Path

from src.dataImport.excel_loader import ExcelLoader
from src.models.system import DigestionSystem
from src.models.pump import build_transfer_pumps, build_digestive_solution_pumps, hms_to_seconds
from src.models.particle_type import ParticleType
from src.simulation.topology import tubular_velocity_at, cstr_outflow_rate
from src.simulation.particle_motion import (
    generate_particles_from_meal,
    update_position_tubular,
    has_exited_tubular_reactor,
    transition_to_reactor,
    mark_particle_exit,
    attempt_cstr_exit,
)

# Ordre des réacteurs tubulaires (R3 -> R4 -> R5), utilisé pour les transitions
TUBULAR_CHAIN_NAMES = ["R3 - Duodénum", "R4 - Jéjunum", "R5 - Iléon"]


def simulate_particle(particle, system, dt_s, max_t_s) -> None:
    """
    Fait avancer une particule dans le temps, à travers tout le système, en gérant les 3 types de transitions :
        - Sortie stochastique de R1 (Estomac) -> R2 (Préduodénum)
        - Sortie stochastique de R2 (Préduodénum) -> R3 (Duodénum)
        - Advection déterministe R3 -> R4 -> R5 -> sortie du système
    Met à jour `particle` en place (exit_time_s rempli une fois sorti).
    """
    reactors_by_name = {r.name: r for r in system.reactors}
    t = particle.entry_time_s
 
    while particle.active and t < max_t_s:
        t += dt_s
 
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
            update_position_tubular(particle, u_m_s=u, operating_conditions=system.operating_conditions, dt_s=dt_s)
 
            if has_exited_tubular_reactor(particle, reactor):
                idx = TUBULAR_CHAIN_NAMES.index(particle.current_reactor)
                if idx + 1 < len(TUBULAR_CHAIN_NAMES):
                    transition_to_reactor(particle, TUBULAR_CHAIN_NAMES[idx + 1])
                else:
                    mark_particle_exit(particle, t)

def main():
    """Importation des paramètres de simulation"""
    loader = ExcelLoader()
    config = loader.load_configuration("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx")
    
    system = DigestionSystem(config, initial_stomach_volume_ml=400.0, initial_preduodenum_volume_ml=150.0)
 
    meal =  config.meal_parameter
 
    particles = generate_particles_from_meal(meal, entry_time_s=0.0, starting_reactor="R1 - Estomac")
    print(f"Population simulee : {len(particles)} particules\n")
 
    # Simulation de chaque particule
    for i, particle in enumerate(particles):
        simulate_particle(particle, system, config.simulation_parameter.time_step, config.simulation_parameter.simulation_duration)
        statut = f"tau = {particle.residence_time_s:.1f} s" if particle.residence_time_s else "N'a PAS termine sa traversee (augmenter max_t_s)"
        print(f"  Particule {i+1:2d} (rho={particle.particle_type.particle_density} kg/m3) : {statut}")
 
    # Résumé
    temps_residence = [p.residence_time_s for p in particles if p.residence_time_s is not None]
    if temps_residence:
        moyenne = sum(temps_residence) / len(temps_residence)
        print(f"\nTemps de residence moyen : {moyenne:.1f} s ({moyenne/60:.1f} min)")
        print(f"Particules ayant termine : {len(temps_residence)} / {len(particles)}")
    else:
        print("\nAucune particule n'a termine sa traversee dans la fenetre testee.")
    
    """
#Volumes tubulaires fixe (incrément 1.1)
    system = DigestionSystem(initial_stomach_volume_ml=400.0,initial_preduodenum_volume_ml=150.0)
    print("Volumes des différents réacteurs :")
    for name, v in system.volumes_summary().items():
        print(f"  {name}: {v:.2f} mL")
    
    print(f"\n Volume total : {system.total_volume():.2f} mL")
    
#Relation d'agitation (incrément 1.2)
    print("\nAgitation à T=0s :")
    for name, status in system.agitation_summary(t_s=0.0, t_in_syringe_cycle_s=0.0).items():
        print(f"  {name}: {status}")

#Conditions Opératoires (incrément 1.3)
    print("\nConditions opératoires du système IViDiS :")
    print(system.operating_conditions)

#Débits des pompes de dosage et de transfert (incrément 1.4)
    all_ok = True #Variable qui permet de valdier le débit des pompes
    for name, pump in {**system.digestive_pumps, **system.transfer_pumps}.items():
        ok = pump.validate_against_expected()
        all_ok &= ok
        print(f" {name}: {'OK' if ok else 'ECHEC'} (volume total attendu = {pump.total_expected_volume_ml():.2f} ml)")
    print(f"\n -> Toutes les pompes cohérentes avec le CDC : {all_ok}")

    print("\n Débits à t = 00:20:00 (1200s)")
    t = hms_to_seconds("00:20:00")
    for name, rate in system.flow_rates_summary(t).items():
        if rate > 0:
            print(f"  {name}: {rate:.2f} mL/min")

    print("\n Volume cumulé délivré par T1 à t = 00:30:00 (1800s)")
    t2 = hms_to_seconds("00:30:00")
    print(f" T1 : {system.transfer_pumps['T1'].cumulative_volume_at(t2):.2f} ml")

#Test seuils d'arrêt pour les réacteurs (R1 et R2)
    print("\nTest des seuils estomac à 30ml")
    system.r1_stomach.set_volume(30.0)
    print(f"Barreau magnétique : {system.r1_stomach.magnetic_stirrer_status()}")
    print(f"Agitateur à pale : {system.r1_stomach.paddle_stirrer_status()}")
    print(f"Pompe seringue : {system.r1_stomach.is_syringe_pump_active}")

    print("\nTest des seuils préduodénum à 30ml")
    system.r2_preduodenum.set_volume(30.0)
    print(f"Barreau magnétique : {system.r2_preduodenum.magnetic_stirrer_status()}")
    print(f"Agitateur à pale : {system.r2_preduodenum.magnetic_stirrer_status()}")

#test de débordement
    print("\nTest de débordement à 1000ml")
    overflow = system.r1_stomach.add_volume(1000.0)
    print(f"Volume actuel : {system.r1_stomach.volume:.2f} ml, débordement : {overflow:.2f} ml")

    print("\nTest de débordement à 1000ml")
    overflow = system.r2_preduodenum.add_volume(1000.0)
    print(f"Volume actuel : {system.r2_preduodenum.volume:.2f} ml, débordement : {overflow:.2f} ml")
"""
"""
#va et vient sur cycle complet
    print("\nCycle pompe va et vient T3 sur 6s : ")
    for t in range(0, 7):   
        print(f"  t={t}s : {system.reciprocating_pump_t3.status(float(t))}")
"""
if __name__ == "__main__": 
    main()