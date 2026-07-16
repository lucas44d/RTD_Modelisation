"""
simulation/topology.py

Câblage de la topologie du système (quelle pompe alimente quel réacteur),
d'après le PID fourni par l'utilisateur. Les VALEURS de débit restent
celles du cahier des charges (section 2.4, 2.5, déjà implémentées dans
models/pump.py) ; seule la STRUCTURE des connexions provient du schéma.

Topologie confirmée par le PID :

    R1 (Estomac)     --[T1, transfert]--> R2 (Préduodénum)
    R2 (Préduodénum) --[T2, transfert]--> R3 (Duodénum)
                                        --(même débit)--> R4 (Jéjunum)
                                        --(même débit)--> R5 (Iléon / Stomie)

    T3 (pompe va-et-vient, cf. 2.2.5) agite localement la jonction R2/R3
    mais ne pilote PAS le débit net : elle est décrite en rpm (cycle
    aspiration/poussée), pas en débit, cf. models/pump.py::ReciprocatingPump.

    Les pompes C1/C2/C3 (solutions pancréatiques/biliaires) et E1 (solution
    de BBM) injectent également de la matière dans le train tubulaire
    R3/R4/R5 (cf. PID), mais leur point d'injection exact reste une
    hypothèse de lecture du schéma manuscrit (pas de certitude absolue) :
    C1/C2/C3 sont supposées injecter au niveau de R3 (Duodénum, pH #3),
    E1 au niveau de R4/R5 (vers l'Iléon). Ces contributions ne sont PAS
    incluses par défaut dans le calcul de vitesse ci-dessous ; utilisez
    `additional_inflows` pour les ajouter explicitement une fois confirmées.
    C4 est exclue (« pas en fonction dans le profil actuel », cf. annotation
    du PID), tout comme B2/B4 (déjà absentes du tableau 2.4).
"""

from __future__ import annotations
from typing import Optional, List

from src.simulation.flow import fluid_velocity_tubular
from src.models.reactor import TubularReactor
from src.models.system import DigestionSystem


# Hypothèse de lecture du PID pour les points d'injection secondaires.
# À utiliser via `additional_inflows=DEFAULT_ADDITIONAL_INFLOWS.get(reactor.name)`
# une fois la position confirmée (pas appliqué par défaut).
DEFAULT_ADDITIONAL_INFLOWS = {
    "R3 - Duodénum": ["C1", "C2", "C3"],
    "R4 - Jéjunum": ["E1"],
}


def reactor_inflow_rate(system: DigestionSystem, reactor_name: str, t_s: float,
                         additional_inflows: Optional[List[str]] = None) -> float:
    """
    Débit volumique net (mL/min) entrant dans un réacteur donné au temps
    t_s, selon la topologie confirmée par le PID.

    additional_inflows : noms de pompes de dosage (ex: "C1", "E1") dont le
                          débit doit être ajouté au débit de transfert
                          principal (cf. DEFAULT_ADDITIONAL_INFLOWS).
    """
    if reactor_name == "R2 - Préduodénum":
        base = system.transfer_pumps["T1"].flow_rate_at(t_s)
    elif reactor_name in ("R3 - Duodénum", "R4 - Jéjunum", "R5 - Iléon", "R5 - Stomie"):
        base = system.transfer_pumps["T2"].flow_rate_at(t_s)
    else:
        base = 0.0

    if additional_inflows:
        for pump_name in additional_inflows:
            base += system.digestive_pumps[pump_name].flow_rate_at(t_s)

    return base


def tubular_velocity_at(system: DigestionSystem, reactor: TubularReactor, t_s: float,
                         additional_inflows: Optional[List[str]] = None) -> float:
    """
    Vitesse d'advection (m/s) dans un réacteur tubulaire (cf. increment 3.1),
    en utilisant le débit fourni par la pompe de transfert appropriée selon
    la topologie du PID.
    """
    q = reactor_inflow_rate(system, reactor.name, t_s, additional_inflows)
    return fluid_velocity_tubular(q, reactor)


def cstr_outflow_rate(system: DigestionSystem, reactor_name: str, t_s: float) -> float:
    """
    Débit net (mL/min) sortant d'un réacteur agité (CSTR), pilotant son
    taux de renouvellement (cf. flow.cstr_renewal_rate / simulation 3.2,
    sortie stochastique) :
        R1 -> R2 : pompe de transfert T1
        R2 -> R3 : pompe de transfert T2
    """
    if reactor_name == "R1 - Estomac":
        return system.transfer_pumps["T1"].flow_rate_at(t_s)
    elif reactor_name == "R2 - Préduodénum":
        return system.transfer_pumps["T2"].flow_rate_at(t_s)
    return 0.0