"""
    Fonctions de génération de graphiques matplotlib pour les résultats de simulation RTD

    Retourne des objets figure matplotlib, destinés à être intégrés dans l'interface PySide6
"""

from __future__ import annotations
from typing import List, Dict
import random

import matplotlib
matplotlib.use("QtAgg")  # backend compatible PySide6
from matplotlib.figure import Figure

# Palette de couleurs distinctes pour comparer plusieurs groupes de particules
_GROUP_COLORS = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]
 

""" Trace l'histogramme de la distribution des temps de résidence E(t) """
def plot_residence_time_distribution(bin_centers: List[float], e_values: List[float]) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)

    if bin_centers:
        width = (bin_centers[1] - bin_centers[0]) if len(bin_centers) > 1 else 1.0
        ax.bar(bin_centers, e_values, width=width, alpha=0.7, label="E(t) simulé", color="#3b82f6", edgecolor="white")

    ax.set_xlabel("Temps (min)")
    ax.set_ylabel("E(t)")
    ax.set_title("Distribution des temps de résidence")
    if bin_centers:
        ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


"""Trace la fonction cumulée F(t)"""
def plot_cumulative_distribution(t_values: List[float], f_values: List[float]) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)

    if t_values:
        ax.plot(t_values, f_values, color="#10b981", linewidth=2)
        ax.fill_between(t_values, f_values, alpha=0.1, color="#10b981")

    ax.set_xlabel("Temps (min)")
    ax.set_ylabel("F(t)")
    ax.set_title("Fonction cumulée des temps de résidence")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


"""
    Trace le nombre brut de particules sorties par intervalle de temps
"""
def plot_exit_count_histogram(bin_starts: List[float], counts: List[int]) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
 
    if bin_starts:
        width = (bin_starts[1] - bin_starts[0]) if len(bin_starts) > 1 else 1.0
        ax.bar(bin_starts, counts, width=width, align="edge", alpha=0.8,
               color="#f59e0b", edgecolor="white")
 
    ax.set_xlabel("Temps (min)")
    ax.set_ylabel("Nombre de particules sorties")
    ax.set_title("Particules sorties par intervalle de temps")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig

 
"""
    Trace le nombre cumulé de particules sorties au fil du temps
"""
def plot_cumulative_exit_counts(t_values: List[float], counts: List[int]) -> Figure:
    
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
 
    if t_values:
        ax.step(t_values, counts, where="post", color="#8b5cf6", linewidth=2)
        ax.fill_between(t_values, counts, step="post", alpha=0.1, color="#8b5cf6")
 
    ax.set_xlabel("Temps (min)")
    ax.set_ylabel("Nombre cumulé de particules sorties")
    ax.set_title("Sorties cumulées du système")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig

def plot_volume_history(volume_history: Dict[str, List[float]]) -> Figure:
    """
    Trace l'évolution du volume de chaque réacteur (R1 à R5) au fil du
    temps, cf. simulation.simulation.SimulationResult.volume_history.
 
    R1/R2 : volume réel (bilan de matière, vidange/remplissage, cf.
            simulation/volume_dynamics.py::update_reactor_volumes).
    R3/R4/R5 : volume de remplissage (démarre à 0, tube vide, se remplit
            jusqu'à la capacité maximale au fur et à mesure que le liquide
            est poussé depuis l'amont)
    """
    fig = Figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
 
    t_values = [t / 60 for t in volume_history.get("t", [])]
    reactor_names = [k for k in volume_history.keys() if k != "t"]
 
    for i, name in enumerate(reactor_names):
        color = _GROUP_COLORS[i % len(_GROUP_COLORS)]
        ax.plot(t_values, volume_history[name], color=color, linewidth=2, label=name)
 
    ax.set_xlabel("Temps (min)")
    ax.set_ylabel("Volume (mL)")
    ax.set_title("Suivi des volumes du système")
    if reactor_names:
        ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


"""
    Superpose les courbes de sorties cumulées de plusieurs types de particules sur un même graphique, 
    pour comparer visuellement leur effet sur la vitesse de sortie du système.
 
    grouped_data : {label: (t_values, counts)}, 
"""
def plot_cumulative_exit_counts_by_group(grouped_data: Dict[str, tuple]) -> Figure:
    
    fig = Figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
 
    for i, (label, (t_values, counts)) in enumerate(sorted(grouped_data.items())):
        color = _GROUP_COLORS[i % len(_GROUP_COLORS)]
        if t_values:
            ax.step(t_values, counts, where="post", color=color, linewidth=2, label=label)
 
    ax.set_xlabel("Temps (min)")
    ax.set_ylabel("Nombre cumulé de particules sorties")
    ax.set_title("Comparaison des sorties cumulées par type de particule")
    if grouped_data:
        ax.legend(fontsize=8, loc="lower right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig

def plot_active_particles_by_reactor(counts: Dict[str, int]) -> Figure:
    """
    Histogramme du nombre de particules encore actives (non sorties du système) par réacteur 
    Montre où les particules restent bloquées à la fin de la simulation.
    """
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
 
    if counts:
        names = sorted(counts.keys())
        values = [counts[n] for n in names]
        colors = [_GROUP_COLORS[i % len(_GROUP_COLORS)] for i in range(len(names))]
        ax.bar(names, values, color=colors, edgecolor="white")
        ax.tick_params(axis="x", rotation=20)
 
    ax.set_ylabel("Nombre de particules actives (non sorties)")
    ax.set_title("Particules non sorties, par réacteur")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    return fig


def plot_active_particle_positions(positions_by_reactor: Dict[str, List[float]]) -> Figure:
    """
    Position d'avancement des particules actives dans les réacteurs tubulaires R3/R4/R5: une ligne par réacteur, 
    chaque particule représentée comme un point (fraction du réacteur parcourue, 0=entrée, 1=sortie)
    """
    fig = Figure(figsize=(7, 4))
    ax = fig.add_subplot(111)
 
    reactor_names = sorted(positions_by_reactor.keys())
    rng = random.Random(0)  # jitter reproductible d'un affichage à l'autre
 
    for i, name in enumerate(reactor_names):
        fractions = positions_by_reactor[name]
        if not fractions:
            continue
        y_jitter = [i + rng.uniform(-0.15, 0.15) for _ in fractions]
        color = _GROUP_COLORS[i % len(_GROUP_COLORS)]
        ax.scatter(fractions, y_jitter, alpha=0.6, s=20, color=color, label=name)
 
    ax.set_yticks(range(len(reactor_names)))
    ax.set_yticklabels(reactor_names)
    ax.set_ylim(-0.5, len(reactor_names) - 0.5 if reactor_names else 0.5)
    ax.set_xlabel("Fraction du réacteur parcourue (0 = entrée, 1 = sortie)")
    ax.set_xlim(-0.05, 1.05)
    ax.set_title("Position des particules actives dans les réacteurs tubulaires")
    ax.grid(True, alpha=0.3, axis="x")
    fig.tight_layout()
    return fig