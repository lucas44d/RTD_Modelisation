"""
Point d'entrée du projet IViDiS (usage en ligne de commande, sans interface graphique — cf. gui_main.py pour la version PySide6)
 
toute la logique vit dans
    - simulation/simulation.py (moteur d'orchestration)
    - simulation/rtd.py (temps de résidence et distribution)
main.py se contente de construire la configuration, lancer la simulation, et afficher les résultats
"""
 
import sys
import os
 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
 
from src.models.system import DigestionSystem
from src.dataImport.excel_loader import ExcelLoader
 
from src.simulation.simulation import run_population_simulation
from src.simulation.rtd import (
    residence_time_summary,
    collect_residence_times,
    compute_E_t,
    compute_F_t,
) 
 
def main():
    loader = ExcelLoader()
    config = loader.load_configuration("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx")
    
 
    # Système et repas de test 
    system = DigestionSystem(config, initial_stomach_volume_ml=400.0, initial_preduodenum_volume_ml=150.0)
    particle_types = loader._load_particles("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx","Particules")
    meal =  config.meal_parameter
    simulation = config.simulation_parameter
    
    print(f"Population : {sum(pt.count for pt in particle_types)} particules")
    print(f"Durée de simulation : {simulation.simulation_duration} s, pas de temps : {simulation.time_step} s\n")
 
    # Simulation
    particles = run_population_simulation(system=system, meal=meal, dt_s=simulation.time_step, max_t_s=simulation.simulation_duration)
 
    # Détail par particule
    for i, particle in enumerate(particles):
        statut = (f"tau = {particle.residence_time_s:.1f} s"
                  if particle.residence_time_s is not None
                  else "N'a PAS terminé sa traversée (augmenter simulation_duration)")
        print(f"  Particule {i + 1:2d} (rho={particle.particle_type.particle_density:.0f} kg/m3) : {statut}")
 
    # Temps de résidence : moyenne, variance
    summary = residence_time_summary(particles)
    print(f"\n=== Increment 3.5 : temps de résidence ===")
    print(f"Particules ayant terminé : {summary['n_completed']} / {summary['n_total']} "
          f"({summary['completion_rate'] * 100:.0f}%)")
    if summary["n_completed"] > 0:
        print(f"Temps de résidence moyen (tau_bar) : {summary['mean_residence_time_s']:.1f} s "
              f"({summary['mean_residence_time_s'] / 60:.1f} min)")
        print(f"Variance (sigma^2) : {summary['variance_s2']:.1f} s^2")
        print(f"Écart-type : {summary['std_dev_s']:.1f} s")
 
    # Distribution E(t) / F(t)
    taus = collect_residence_times(particles)
    if taus:
        print(f"\n=== Increment 3.6 : distribution des temps de résidence ===")
        bin_centers, e_values = compute_E_t(taus, n_bins=10)
        print("Histogramme E(t) (10 classes) :")
        for center, e_val in zip(bin_centers, e_values):
            print(f"  t={center:8.1f} s : E(t)={e_val:.6f}")
 
        t_values, f_values = compute_F_t(taus, n_points=5)
        print("\nFonction cumulée F(t) (5 points) :")
        for t_val, f_val in zip(t_values, f_values):
            print(f"  t={t_val:8.1f} s : F(t)={f_val:.2f}")
 
if __name__ == "__main__":
    main()
 
