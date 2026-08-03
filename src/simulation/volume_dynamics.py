"""
Suivi dynamique du volume des réacteurs agités R1 (Estomac) et R2 (Préduodénum) au cours du temps, par bilan de matière 
(débit entrant - débit sortant), 
"""

from __future__ import annotations

from models.system import DigestionSystem
from models.meal_parameter import MealParameter


# Pompes de dosage qui alimentent directement R1
R1_INFLOW_PUMPS = ["A3", "A4", "B1", "B3"]

# Pompes de dosage qui alimentent directement R2 
R2_INFLOW_PUMPS = ["C1", "C2", "C3"]


def update_reactor_volumes(system: DigestionSystem, t_s: float, dt_s: float) -> None:
    """
    Met à jour les volumes de R1 et R2 pour ce pas de temps, par bilan de matière : volume += (débit entrant - débit sortant) * dt.

    À appeler une fois par pas de temps, avant de faire avancer les particules, pour que les décisions d'agitation et de
    sortie stochastique (Q/V) utilisent un volume à jour
    """
    # R1 : Estomac 
    r1_in_ml_min = sum(system.digestive_pumps[name].flow_rate_at(t_s) for name in R1_INFLOW_PUMPS)
    r1_out_ml_min = system.transfer_pumps["T1"].flow_rate_at(t_s)
    net_r1_ml_min = r1_in_ml_min - r1_out_ml_min
    system.r1_stomach.add_volume(net_r1_ml_min / 60.0 * dt_s)

    # R2 : Préduodénum
    r2_in_ml_min = system.transfer_pumps["T1"].flow_rate_at(t_s) + sum(
        system.digestive_pumps[name].flow_rate_at(t_s) for name in R2_INFLOW_PUMPS
    )
    r2_out_ml_min = system.transfer_pumps["T2"].flow_rate_at(t_s)
    net_r2_ml_min = r2_in_ml_min - r2_out_ml_min
    system.r2_preduodenum.add_volume(net_r2_ml_min / 60.0 * dt_s)


def inject_meal_into_stomach(system: DigestionSystem, meal: MealParameter, t_s: float, dt_s: float, meal_start_time_s: float = 0.0) -> None:
    """
    Ajoute le volume du repas au volume de R1, réparti sur la période d'entrée du repas (meal.meal_entry_period), au débit meal.meal_flow.

    Fonction séparée de update_reactor_volumes() car le volume du repas n'est pas une pompe de dosage, mais un apport ponctuel
    défini par les paramètres du repas lui-même. À appeler une fois par pas de temps, en plus de update_reactor_volumes().
    """
    meal_end_time_s = meal_start_time_s + meal.meal_entry_period
    
    if meal_start_time_s <= t_s < meal_end_time_s:
        system.r1_stomach.add_volume(meal.meal_flow / 60.0 * dt_s)

def total_particle_volume_ml(meal: MealParameter) -> float:
    """
    Volume total occupé par les particules solides du repas (mL), calculé à partir du diamètre et du 
    nombre de chaque type de particule (somme des volumes sphériques individuels)
    """
    import math
    total_m3 = 0.0
    for pt in meal.particles:
        volume_one_m3 = (4.0 / 3.0) * math.pi * (pt.particle_size/2) ** 3
        total_m3 += volume_one_m3 * pt.count
    return total_m3 * 1e6  # m^3 -> mL


def water_volume_to_add_ml(meal: MealParameter, total_meal_volume_ml: float) -> float:
    """
    Volume d'eau à ajouter (mL) pour compléter le volume des particules jusqu'au volume total de repas souhaité
    """
    return max(0.0, total_meal_volume_ml - total_particle_volume_ml(meal))


def update_tubular_reactor_volumes(system: DigestionSystem, t_s: float, dt_s: float) -> float:
    """
    Fait progresser le remplissage des réacteurs tubulaires R3, R4, R5 au fil du temps 
 
    Retourne le volume (mL) qui a fini par sortir du système via R5 sur ce
    pas de temps (utile pour un futur suivi du débit de sortie global).
    """
    inflow_r3_ml = system.transfer_pumps["T2"].flow_rate_at(t_s) / 60.0 * dt_s
    overflow_r3_ml = system.r3_duodenum.add_inflow(inflow_r3_ml)
 
    inflow_r4_ml = overflow_r3_ml + system.digestive_pumps["E1"].flow_rate_at(t_s) / 60.0 * dt_s
    overflow_r4_ml = system.r4_jejunum.add_inflow(inflow_r4_ml)
 
    overflow_r5_ml = system.r5_ileon_or_stomie.add_inflow(overflow_r4_ml)
 
    return overflow_r5_ml