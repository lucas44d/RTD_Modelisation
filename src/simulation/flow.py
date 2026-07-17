"""
Implémente le calcul de la vitesse du fluide dans les différentes parties du
système IViDiS, nécessaire à l'advection des particules :

    - Dans les réacteurs tubulaires R3/R4/R5 (écoulement piston) : 
      la vitesse moyenne du fluide est donnée par u = Q / A, où Q est le débit volumique et A la section transversale interne du tube.

    - Dans les réacteurs agités R1/R2 (CSTR, bien mélangé) : il n'y a pas de direction d'écoulement unique. On utilise plutôt le taux de
      renouvellement du fluide (Q/V), qui correspond à l'inverse du temps de séjour moyen τ = V/Q (cf. 5.6), et sert à modéliser la probabilité de
      sortie d'une particule à chaque pas de temps (cf. particle_motion.py).
"""

from __future__ import annotations
import math

from src.models.reactor import TubularReactor, INCH_TO_M


ML_PER_MIN_TO_M3_PER_S = 1e-6 / 60.0  # 1 mL/min = 1e-6 m^3, divisé par 60 s


def cross_section_area_m2(inner_diameter_in: float) -> float:
    """Section transversale interne d'un tube (m²), à partir de son diamètre (po)."""
    diameter_m = inner_diameter_in * INCH_TO_M
    return math.pi * (diameter_m / 2) ** 2


def fluid_velocity_tubular(flow_rate_ml_min: float, reactor: TubularReactor) -> float:
    """
    Vitesse moyenne du fluide (m/s) dans un réacteur tubulaire, pour un débit volumique donné.

    flow_rate_ml_min : débit volumique entrant dans le réacteur (mL/min)
    reactor : TubularReactor concerné (fournit le diamètre interne)
    """
    area_m2 = cross_section_area_m2(reactor.inner_diameter_in)
    if area_m2 == 0:
        return 0.0
    flow_m3_s = flow_rate_ml_min * ML_PER_MIN_TO_M3_PER_S
    return flow_m3_s / area_m2


def cstr_renewal_rate(flow_rate_ml_min: float, volume_ml: float) -> float:
    """
    Taux de renouvellement du fluide (1/s) dans un réacteur agité (CSTR) : Q/V.
    Correspond à l'inverse du temps de séjour moyen τ = V/Q
    Retourne 0 si le volume est nul ou négatif
    """
    if volume_ml <= 0:
        return 0.0
    flow_ml_s = flow_rate_ml_min / 60.0
    return flow_ml_s / volume_ml


def mean_residence_time_cstr(flow_rate_ml_min: float, volume_ml: float) -> float:
    """
    Temps de séjour moyen τ = V/Q (s) d'un réacteur agité, référence théorique CSTR, utile pour valider qualitativement le comportement du modèle.
    """
    rate = cstr_renewal_rate(flow_rate_ml_min, volume_ml)
    if rate == 0:
        return float("inf")
    return 1.0 / rate