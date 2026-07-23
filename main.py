from pathlib import Path
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from PySide6.QtWidgets import QApplication
import sys

from src.dataImport.excel_loader import ExcelLoader
from src.models.system import DigestionSystem
from src.models.pump import build_transfer_pumps, build_digestive_solution_pumps, hms_to_seconds
from src.models.particle_type import ParticleType
from src.simulation.topology import tubular_velocity_at, cstr_outflow_rate
from src.simulation.particle_motion import generate_particles_from_meal
from src.simulation.simulation import (
    run_simulation,
    print_particle_physics_diagnostics
)
from src.simulation.rtd import (
    compute_F_t,
    compute_E_t,
    residence_time_summary)

from PySide6.QtWidgets import QApplication
from src.visualization.gui import MainWindow


def main():
    """ Importation des paramètres de simulation """
    loader = ExcelLoader()
    config = loader.load_configuration("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx")
    system = DigestionSystem(config, initial_stomach_volume_ml=400.0, initial_preduodenum_volume_ml=150.0)
    meal =  config.meal_parameter
    simulation = config.simulation_parameter

    """ Importation du repas et des particules qui constituent le repas """
    particle_type = loader._load_particles("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx","Particules")
    particles = generate_particles_from_meal(meal, entry_time_s=0.0, starting_reactor="R1 - Estomac")

    """ Permet de vérifier quelle formule utiliser selon le type de particule (sédimentation corrigée ou formule de Stokes pur)"""
    use_corrected_by_type = print_particle_physics_diagnostics(particle_type, system.operating_conditions)

    print(f"Population simulée : {len(particles)} particules")
    print(f"Durée de simulation : {simulation.simulation_duration} s, pas de temps : {simulation.time_step} s\n")

    """ Lancement de la simulation """
    run_simulation(system=system, particles=particles, use_corrected_by_type=use_corrected_by_type, dt_s=simulation.time_step, max_t_s=simulation.simulation_duration,)

    """ Résultats """ 
    for i, particle in enumerate(particles):
        statut = (f"tau = {particle.residence_time_s:.1f} s"
                  if particle.residence_time_s is not None
                  else "N'a PAS terminé sa traversée (augmenter simulation_duration)")
        print(f"  Particule {i + 1:2d} (rho={particle.particle_type.particle_density:.0f} kg/m3) : {statut}")
 
    residence_time = [p.residence_time_s for p in particles if p.residence_time_s is not None]
    if residence_time:
        residence_time_average = sum(residence_time) / len(residence_time)
        print(f"\nTemps de résidence moyen : {residence_time_average:.1f} s")
        print(f"Particules ayant terminé : {len(residence_time)} / {len(particles)}")
    else:
        print("\nAucune particule n'a terminé sa traversée dans la fenêtre testée.")
 

    #Permet de savoir où les particules qui ne sont pas sortis se sont arrêtées
    compteur = Counter()

    for p in particles:
        if p.active:
            compteur[p.current_reactor] += 1

    print(compteur)

    rtd_summary = residence_time_summary(particles)
    print("\nRésumée des temps de résidence :")
    print(f"Particules totales   : {rtd_summary['n_total']}")
    print(f"Particules sorties   : {rtd_summary['n_completed']}")
    print(f"Particules actives   : {rtd_summary['n_active']}")
    print(f"Taux de complétion   : {rtd_summary['completion_rate']:.2%}")
    print(f"Temps moyen (tau_bar): {rtd_summary['mean_residence_time_s']:.2f} s")
    print(f"Variance (sigma^2)   : {rtd_summary['variance_s2']:.2f} s²")
    print(f"Écart-type (sigma)   : {rtd_summary['std_dev_s']:.2f} s")
    

    bin_centers, E_t = compute_E_t(rtd_summary["taus"])
    t_centres, F_t = compute_F_t(rtd_summary["taus"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Graphique 1 : E(t) - Densité de probabilité
    ax1.plot(bin_centers, E_t, 'b-', lw=2, label='$E(t)$ (densité)')
    ax1.fill_between(bin_centers, E_t, color='blue', alpha=0.2)  # Remplissage sous la courbe
    ax1.set_title("Densité de temps de séjour E(t)")
    ax1.set_xlabel("Temps t (min)")
    ax1.set_ylabel("E(t) ($min^{-1}$)")
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend()

# Graphique 2 : F(t) - Fonction cumulée
    ax2.plot(t_centres, F_t, 'r-', lw=2, label='$F(t)$ (cumulé)')
    ax2.axhline(1.0, color='gray', linestyle=':', label='100% sorti')
    ax2.set_title("Fonction cumulée F(t)")
    ax2.set_xlim(left=0)
    ax2.set_xlabel("Temps t (min)")
    ax2.set_ylabel("F(t) (sans unité, 0 à 1)")
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    plt.show()
    
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

    #app = QApplication(sys.argv)
    
    #fenetre = MainWindow()
    #fenetre.show()
    
    #sys.exit(app.exec())