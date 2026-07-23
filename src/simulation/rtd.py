"""
    Ce fichier implémente les calculs pour la distribution des temps de résidence, la fonction cumulée, et la variance

    Il permet d'aider à l'analyse des résultats expérimentaux grâce aux formules de la section 5 du cahier des charges
"""

from __future__ import annotations
import math
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