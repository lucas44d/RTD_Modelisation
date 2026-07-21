"""
Câblage de la topologie du système (quelle pompe alimente quel réacteur)

Topologie confirmée par le PID :

    R1 (Estomac)     --[T1, transfert]--> R2 (Préduodénum)
    R2 (Préduodénum) --[T2, transfert]--> R3 (Duodénum)
                     --(même débit)--> R4 (Jéjunum)
                     --(même débit)--> R5 (Iléon / Stomie)

    T3 (pompe va-et-vient) agite localement la jonction R2/R3 mais ne pilote PAS le débit net (cycle aspiration/poussée)
"""

from __future__ import annotations
from typing import Optional, List

from src.simulation.flow import fluid_velocity_tubular
from src.models.reactor import TubularReactor
from src.models.system import DigestionSystem

DEFAULT_ADDITIONAL_INFLOWS = {
    "R2 - Préduodénum": ["C1", "C2", "C3"],
    "R4 - Jéjunum": ["E1"],
    "R5 - Iléon": ["E1"],
    "R5 - Stomie": ["E1"],
}


def reactor_inflow_rate(system: DigestionSystem, reactor_name: str, t_s: float, extra_inflows: Optional[List[str]] = None, use_default_additional_inflows: bool = True) -> float:
    """
    Débit volumique net (mL/min) entrant dans un réacteur donné au temps t_s, selon la topologie confirmée par le PID.

    extra_inflows : noms de pompes de dosage supplémentaires à ajouter, en plus des injections par défaut
    
    use_default_additionnal_inflows : Si False, ignore les injections secondaires par défaut 
    (par exemple pour isoler l'effet des seules pompes de transfert T1/T2 lors des tests)
    
    """
    if reactor_name == "R2 - Préduodénum":
        base = system.transfer_pumps["T1"].flow_rate_at(t_s)
    elif reactor_name in ("R3 - Duodénum", "R4 - Jéjunum", "R5 - Iléon", "R5 - Stomie"):
        base = system.transfer_pumps["T2"].flow_rate_at(t_s)
    else:
        base = 0.0

    inflow_pumps : List[str] = []
    if use_default_additional_inflows:
        inflow_pumps += DEFAULT_ADDITIONAL_INFLOWS.get(reactor_name, [])
    if extra_inflows:
        inflow_pumps += extra_inflows
    
    for pump_name in inflow_pumps:
        base += system.digestive_pumps[pump_name].flow_rate_at(t_s)

    return base


def tubular_velocity_at(system: DigestionSystem, reactor: TubularReactor, t_s: float, extra_inflows: Optional[List[str]] = None, use_default_additional_inflows: bool = True) -> float:
    """
    Vitesse d'advection (m/s) dans un réacteur tubulaire, en utilisant le débit fourni par la pompe de transfert appropriée selon le PID
    """
    q = reactor_inflow_rate(system, reactor.name, t_s, extra_inflows, use_default_additional_inflows)
    return fluid_velocity_tubular(q, reactor)


def cstr_outflow_rate(system: DigestionSystem, reactor_name: str, t_s: float) -> float:
    """
    Débit net (mL/min) sortant d'un réacteur CSTR, pilotant son
    taux de renouvellement :
        R1 -> R2 : pompe de transfert T1
        R2 -> R3 : pompe de transfert T2
    """
    if reactor_name == "R1 - Estomac":
        return system.transfer_pumps["T1"].flow_rate_at(t_s)
    elif reactor_name == "R2 - Préduodénum":
        return system.transfer_pumps["T2"].flow_rate_at(t_s)
    return 0.0