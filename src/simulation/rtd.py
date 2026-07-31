"""
    Ce fichier implémente les calculs pour la distribution des temps de résidence, la fonction cumulée, et la variance

    Il permet d'aider à l'analyse des résultats expérimentaux grâce aux formules de la section 5 du cahier des charges
"""

from __future__ import annotations
import math
from collections import Counter
from typing import List, Dict, Tuple, Optional
 
from .particle_motion import Particle

""" 
    Permet d'extraire les temps de résidence individuelle des particules ayant traversé le système à la fin de la simulation 
    On ne prend pas en compte les particules n'ayant pas terminé la traversée (si temps de résidence = nulle)
"""
def collect_residence_times(particles: List[Particle]) -> List[float]:
    return [p.residence_time_s for p in particles if p.residence_time_s is not None]

"""
    Calcul le temps de résidence moyen, retourne NaN (Not a Number) si aucune particule n'a terminé (taus est vide)
"""
def mean_residence_time(taus: List[float]) -> float:
    if not taus:
        return float("nan")
    return sum(taus) / len(taus)

"""
    Calcul de la variance des temps de résidence
    retourne NaN (Not a Number) si aucune particule n'a terminé (taus vide)
"""
def variance_residence_time(taus: List[float]) -> float : 
    if not taus :
        return float ("nan")
    tau_bar = mean_residence_time(taus)
    return sum((t - tau_bar)**2 for t in taus)/len(taus)

"""
    Résumé complet des temps de résidence pour la population simulée : 
        -nombre total
        -nombre ayant terminé et nombre encore active
        -taux de complétion
        -moyenne
        -variance
        -écart-type
"""
def residence_time_summary(particles: List[Particle])-> Dict[str, float] :
    taus = collect_residence_times(particles)
    n_total = len(particles)
    n_completed = len(taus)
    n_active = n_total - n_completed

    tau_bar = mean_residence_time(taus)
    sigma2 = variance_residence_time(taus)
    sigma = math.sqrt(sigma2) if not math.isnan(sigma2) else float("nan")

    return{
        "taus": taus,
        "n_total": n_total,
        "n_completed": n_completed,
        "n_active": n_active,
        "completion_rate": (n_completed / n_total) if n_total else float("nan"),
        "mean_residence_time_s": tau_bar,
        "variance_s2": sigma2,
        "std_dev_s": sigma
    }

"""
    Calcul l'histogramme de densité de la probabilité E(t)
    Retourne (bin_centers, E_values). L'intégrale de E(t) sur tout le domaine (somme des E_values*bin_width) vaut 1
"""
def compute_E_t(taus: List[float], n_bins: int = 30) -> Tuple[List[float], List[float]]:
    if not taus:
        return [], []

    """ Tous les tau sont identiques : pic ponctuel de largeur 1s (on évite une division par 0)"""
    t_min, t_max = min(taus), max(taus)
    if t_min == t_max:
        return [t_min],[1.0]

    bin_width = (t_max - t_min)/ n_bins
    counts=[0]*n_bins
    for tau in taus:
        idx=int((tau-t_min)/bin_width)
        idx=min(idx,n_bins-1) 
        counts[idx] += 1

    n_total = len(taus)
    bin_centers = [t_min + (i + 0.5) * bin_width for i in range(n_bins)]
    e_values = [c / (n_total * bin_width) for c in counts]

    return bin_centers, e_values


"""
    Calcul de la fonction cumulée F(t)
    Si t_values n'est pas fourni, génère n_points valeurs régulièrement espacées entre min(taus) et max(taus).
    Retourne (t_values, F_values)
"""
def compute_F_t(taus: List[float], t_values: Optional[List[float]] = None, n_points: int = 100) -> Tuple[List[float], List[float]]:    
    if not taus:
        return [], []

    n_total = len(taus)
    sorted_taus = sorted(taus)

    if t_values is None :
        t_min, t_max = sorted_taus[0], sorted_taus[-1]
        if t_min == t_max :
            t_values = [t_min]
        else :
            step = (t_max - t_min)/(n_points - 1)
            t_values = [t_min + i * step for i in range(n_points)]

    f_values = []
    for t in t_values:
        count = sum(1 for tau in sorted_taus if tau <= t)
        f_values.append(count/n_total)

    return list(t_values), f_values


"""
    Nombre brut de particules sorties par intervalle de temps 
 
    Retourne (bin_starts, counts) où bin_starts[i] est le début de l'intervalle i
    et counts[i] le nombre de particules dont tau_i tombe dans cet intervalle
"""
def compute_exit_count_histogram(taus: List[float], n_bins: int = 20) -> Tuple[List[float], List[int]]:
    if not taus:
        return [], []
 
    t_min, t_max = min(taus), max(taus)
    if t_min == t_max:
        return [t_min], [len(taus)]
 
    bin_width = (t_max - t_min) / n_bins
    counts = [0] * n_bins
    for tau in taus:
        idx = int((tau - t_min) / bin_width)
        idx = min(idx, n_bins - 1)  # inclut la valeur max dans le dernier bin
        counts[idx] += 1
 
    bin_starts = [t_min + i * bin_width for i in range(n_bins)]
    return bin_starts, counts

"""
    Nombre cumulé de particules sorties au fil du temps, ex : 10 particules sorties à t=8000s, puis 15 au total à t=8500s, etc.
 
    Retourne (t_values, cumulative_counts), triés par temps de sortie croissant.
    cumulative_counts[i] = nombre de particules avec tau_j <= t_values[i]
"""
def compute_cumulative_exit_counts(taus: List[float]) -> Tuple[List[float], List[int]]:
    
    if not taus:
        return [], []
    sorted_taus = sorted(taus)
    cumulative_counts = list(range(1, len(sorted_taus) + 1))
    return sorted_taus, cumulative_counts

"""
    Regroupe une population de particules par type (densité, taille), pour comparer l'effet de ces propriétés sur le temps de résidence
 
    Retourne {label: [particules de ce type]}, où label est une chaîne lisible générée à partir de la densité et du rayon (en mm).
"""
def group_particles_by_type(particles: List[Particle],label_format: str = "ρ={density:.0f} kg/m³, d={diameter_mm:.4f} mm") -> Dict[str, List[Particle]]:
    groups: Dict[str, List[Particle]] = {}
    for p in particles:
        label = label_format.format(
            density=p.particle_type.particle_density,
            diameter_mm=p.particle_type.particle_size * 1000.0,
        )
        groups.setdefault(label, []).append(p)
    return groups
 

"""
    Calcule la courbe de sorties cumulées séparément pour chaque type de particule, afin de les superposer sur un même graphique et 
    comparer visuellement leur effet sur la vitesse de sortie du système
 
    Retourne {label: (t_values, cumulative_counts)}.
"""
def compute_cumulative_exit_counts_by_group(particles: List[Particle]) -> Dict[str, Tuple[List[float], List[int]]]:
   
    groups = group_particles_by_type(particles)
    result = {}
    for label, group_particles in groups.items():
        taus = collect_residence_times(group_particles)
        result[label] = compute_cumulative_exit_counts(taus)
    return result
 

"""
    Résumé statistique (moyenne, nombre terminé/total) par type de particule, pour un tableau ou une légende récapitulative
"""
def mean_residence_time_by_group(particles: List[Particle]) -> Dict[str, Dict[str, float]]:
    groups = group_particles_by_type(particles)
    result = {}
    for label, group_particles in groups.items():
        taus = collect_residence_times(group_particles)
        result[label] = {
            "n_total": len(group_particles),
            "n_completed": len(taus),
            "mean_residence_time_s": mean_residence_time(taus),
        }
    return result


"""
    Fonction alternative pour afficher les billes sorties cumulées via excel
"""
def compute_cumulative_exit_counts_excel(taus: List[float],) -> Tuple[List[float], List[int]]:
    if not taus:
        return [], []

    # On compte combien de billes sortent à chaque pas de temps exact
    counts_per_time = Counter(taus)

    # On trie les temps uniques
    unique_sorted_taus = sorted(counts_per_time.keys())

    # On calcule le cumul sur ces temps uniques
    cumulative_counts = []
    total_so_far = 0

    for t in unique_sorted_taus:
        total_so_far += counts_per_time[t]
        cumulative_counts.append(total_so_far)

    return unique_sorted_taus, cumulative_counts


def count_active_particles_by_reactor(particles: List[Particle]) -> Dict[str, int]:
    """
    Compte le nombre de particules encore actives (non sorties du système) par réacteur où elles se trouvent actuellement
    Utile pour voir où les particules restent bloquées à la fin de la fenêtre de simulation
    """
    counts: Dict[str, int] = {}
    for p in particles:
        if p.active:
            counts[p.current_reactor] = counts.get(p.current_reactor, 0) + 1
    return counts
 
 
def active_particle_positions_in_tubular(particles: List[Particle], reactor_lengths_m: Dict[str, float]) -> Dict[str, List[float]]:
    """
    Pour les particules encore actives dans un réacteur tubulaire (R3/R4/R5), retourne leur position x (fraction du réacteur parcourue : 0 = entrée, 1 = sortie), regroupée par réacteur.
 
    reactor_lengths_m : {nom_reacteur: longueur_m}
    """
    positions: Dict[str, List[float]] = {}
    for p in particles:
        if p.active and p.current_reactor in reactor_lengths_m:
            length = reactor_lengths_m[p.current_reactor]
            fraction = (p.x / length) if length > 0 else 0.0
            positions.setdefault(p.current_reactor, []).append(min(max(fraction, 0.0), 1.0))
    return positions
 
 
def get_tubular_reactor_lengths_m(system) -> Dict[str, float]:
    """
    Construit {nom_reacteur: longueur_m} pour les réacteurs tubulaires (R3, R4, R5) d'un DigestionSystem, à passer à active_particle_positions_in_tubular().
    """
    from models.reactor import FEET_TO_M
    tubular_reactors = [system.r3_duodenum, system.r4_jejunum, system.r5_ileon_or_stomie]
    return {r.name: r.length_ft * FEET_TO_M for r in tubular_reactors}