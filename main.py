"""
Point d'entrée du projet IViDiS (usage en ligne de commande, sans interface graphique — cf. gui_main.py pour la version PySide6)
 
toute la logique vit dans
    - simulation/simulation.py (moteur d'orchestration)
    - simulation/rtd.py (temps de résidence et distribution)
main.py se contente de construire la configuration, lancer la simulation, et afficher les résultats
"""
 
import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import matplotlib.pyplot as plt

from src.models.system import DigestionSystem
from src.dataImport.excel_loader import ExcelLoader
from src.models.system import DigestionSystem
from src.models.pump import hms_to_seconds
from src.export.excel_exporter import ExcelExporter

from src.simulation.simulation import run_population_simulation
from src.simulation.rtd import (
    residence_time_summary,
    collect_residence_times,
    compute_E_t,
    compute_F_t,
    data_summary,
    compute_cumulative_exit_counts_by_group,
    mean_residence_time_by_group,
)
from src.simulation.flow import mean_residence_time_cstr
from src.simulation.volume_dynamics import total_particle_volume_ml, water_volume_to_add_ml

INCH_TO_M = 0.0254

def main():    

    current_file = Path(__file__).resolve()
    base_dir = next(p for p in current_file.parents if (p / "resources").is_dir())
    
    excel_path = base_dir / "resources" / "Test_import.xlsx"
    loader = ExcelLoader()
    exporter = ExcelExporter()
    config = loader.load_configuration(excel_path)
    
 
    # Système et repas de test 
    system = DigestionSystem(config, initial_stomach_volume_ml=500.0, initial_preduodenum_volume_ml=40.0)
    particle_types = loader._load_particles(excel_path,"Particules")
    meal =  config.meal_parameter
    simulation = config.simulation_parameter
    
    print(f"Population : {sum(pt.count for pt in particle_types)} particules")
    print(f"Durée de simulation : {simulation.simulation_duration} s, pas de temps : {simulation.time_step} s\n")
 
    """
    # Détail par particule
    for i, particle in enumerate(particles):
        statut = (f"tau = {particle.residence_time_s:.1f} s"
                  if particle.residence_time_s is not None
                  else "N'a PAS terminé sa traversée (augmenter simulation_duration)")
        print(f"  Particule {i + 1:2d} (rho={particle.particle_type.particle_density:.0f} kg/m3) : {statut}")
    """
   
    vol_billes = total_particle_volume_ml(meal)
    vol_eau = water_volume_to_add_ml(meal, total_meal_volume_ml=500.0)
    print(f"Volume des billes : {vol_billes:.3f} mL, volume d'eau de complément : {vol_eau:.3f} mL "
          f"(total repas : {vol_billes + vol_eau:.1f} mL, déjà inclus dans les 500 mL initiaux de R1)")
    print(f"Population : {sum(pt.count for pt in particle_types)} particules")
    print(f"Durée de simulation : {simulation.simulation_duration} s, pas de temps : {simulation.time_step} s")
    print(f"Fin du protocole (pompes éteintes) : {simulation.simulation_duration} s "
          f"({simulation.simulation_duration / 3600:.1f} h)\n")
 
    # --- Simulation (increments 3.1 à 3.4) ---
    result = run_population_simulation(
        system=system, meal=meal,
        dt_s=simulation.time_step, max_t_s=simulation.simulation_duration,
        inject_meal_volume=False,
    )
    particles = result.particles

    print("=== Suivi des volumes (extrait) ===")
    vh = result.volume_history
    n_points = len(vh["t"])
    for idx in [0, n_points // 4, n_points // 2, 3 * n_points // 4, n_points - 1]:
        t_val = vh["t"][idx]
        volumes_str = ", ".join(f"{name.split(' - ')[0]}={vh[name][idx]:.1f}mL"
                                 for name in vh if name != "t")
        print(f"  t={t_val:8.0f}s : {volumes_str}")
    print()

 
    # --- Temps de résidence : moyenne, variance (increment 3.5) ---
    summary = residence_time_summary(particles)
    print(f"=== Increment 3.5 : temps de résidence ===")
    print(f"Particules ayant terminé : {summary['n_completed']} / {summary['n_total']} "
          f"({summary['completion_rate'] * 100:.0f}%)")
    if summary["n_completed"] > 0:
        print(f"Temps de résidence moyen (tau_bar) : {summary['mean_residence_time_s']:.1f} s "
              f"({summary['mean_residence_time_s'] / 3600:.1f} h)")
        print(f"Écart-type : {summary['std_dev_s']:.1f} s")

    """
    # --- Comparaison par taille de bille (effet taille/densité) ---
    print(f"\n=== Comparaison par taille de bille ===")
    for label, stats in sorted(mean_residence_time_by_group(particles).items()):
        moyenne_h = stats["mean_residence_time_s"] / 3600 if stats["n_completed"] else float("nan")
        print(f"  {label} : {stats['n_completed']}/{stats['n_total']} terminées, moyenne={moyenne_h:.2f} h")
    """
    # --- Distribution E(t) / F(t) (increment 3.6) ---
    taus = collect_residence_times(particles)
    if taus:
        print(f"\n=== Increment 3.6 : distribution des temps de résidence ===")
        bin_centers, e_values = compute_E_t(taus, n_bins=10)
        print("Histogramme E(t) (10 classes) :")
        for center, e_val in zip(bin_centers, e_values):
            print(f"  t={center:8.1f} s : E(t)={e_val:.8f}")
 
        t_values, f_values = compute_F_t(taus, n_points=5)
        print("\nFonction cumulée F(t) (5 points) :")
        for t_val, f_val in zip(t_values, f_values):
            print(f"  t={t_val:8.1f} s : F(t)={f_val:.2f}")
    else:
        print("\nAucune particule n'a terminé sa traversée : pas de distribution à calculer.")


if __name__ == "__main__":
    main()
 
