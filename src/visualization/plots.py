"""
    Fonctions de génération de graphiques matplotlib pour les résultats de simulation RTD

    Retourne des objets figure matplotlib, destinés à être intégrés dans l'interface PySide6
"""

from __future__ import annotations
from typing import List, Optional
import math

import matplotlib
matplotlib.use("QtAgg")  # backend compatible PySide6
from matplotlib.figure import Figure

""" Trace l'histogramme de la distribution des temps de résidence E(t) """
def plot_residence_time_distribution(bin_centers: List[float], e_values: List[float]) -> Figure:
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)

    if bin_centers:
        width = (bin_centers[1] - bin_centers[0]) if len(bin_centers) > 1 else 1.0
        ax.bar(bin_centers, e_values, width=width, alpha=0.7, label="E(t) simulé", color="#3b82f6", edgecolor="white")

    ax.set_xlabel("Temps (s)")
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

    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("F(t)")
    ax.set_title("Fonction cumulée des temps de résidence")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig