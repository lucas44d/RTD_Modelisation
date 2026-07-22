"""
    Ce fichier implémente les calculs pour la distribution des temps de résidence, la fonction cumulée, et la variance

    Il permet d'aider à l'analyse des résultats expérimentaux.
"""
import numpy as np 

"""Fonction qui permet de calculer la probabilité de densité des temps de résidence des particules """
def probability_density_calculation (residence_time : float) :
    nb_bins =50 
    bins_since_zero = bins_since_zero = np.linspace(0,np.max(residence_time),nb_bins+1) 

    E_t, bin_edges = np.histogram(residence_time,bins_since_zero, density = True)

    return E_t, bin_edges

""" Fonction qui permet de faire la fonction cumulée de la probabilité de densité """
def cumulative_function_calcultation(E_t,bin_edges):
    dt = bin_edges[1] - bin_edges[0]

    F_t = np.cumsum(E_t) * dt
    return F_t