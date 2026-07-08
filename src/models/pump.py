"""
Pompes liées aux relations d'agitation :
    - Pompe seringue de R1 (émulsion de l'estomac)
    - Pompe va-et-vient de R3 / T3

Note : les pompes de dosage des solutions digestives et les pompes de transfert T1/T2 (débits variables selon un profil temporel)
seront ajoutées plus tard. Ce module ne couvre que les deux pompes décrites dans la section "Relation d'agitation" du cahier des charges.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

"""Enumération des états possibles d'une pompe"""
class PumpState(Enum):
    IDLE = "arrêtée"
    DRAWING = "aspiration"
    PAUSED = "pause"
    PUSHING = "poussée / injection"


@dataclass
class PumpStatus:
    state: PumpState
    flow_rate_ml_per_min: float = 0.0

    def __repr__(self) -> str:
        return f"{self.state.value} ({self.flow_rate_ml_per_min:.2f} mL/min)"


class Pump:
    """Classe de base pour toutes les pompes du système"""

    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name}'>"


class SyringePump(Pump):
    """
    Pompe seringue de R1

    Fonctionnement : à un débit constant de 10 mL / 6 s, la pompe :
        1. Tire (aspire) 10 % du volume réel de l'estomac
        2. S'arrête 3 s (temps de créer l'émulsion avec la valve)
        3. Repousse le liquide dans l'estomac
    Ce cycle se répète en continu tant que le volume de l'estomac est supérieur ou égal au seuil des 100 mL
    """

    FLOW_RATE_ML_PER_S = 10.0 / 6.0 # 10 mL / 6 s
    DRAW_FRACTION = 0.10 # 10 % du volume réel de l'estomac
    PAUSE_DURATION_S = 3.0
    MIN_ACTIVE_VOLUME_ML = 100.0

    def __init__(self):
        super().__init__("Pompe seringue R1")

    def draw_volume(self, stomach_volume_ml: float) -> float:
        """Volume aspiré pour le cycle courant (10 % du volume réel)"""
        return self.DRAW_FRACTION * stomach_volume_ml

    def cycle_duration_s(self, stomach_volume_ml: float) -> float:
        """
        Durée totale d'un cycle (aspiration + pause + poussée), en secondes.
        Les temps d'aspiration et de poussée dépendent du volume tiré, à débit constant.
        """
        draw_ml = self.draw_volume(stomach_volume_ml)
        move_time_s = draw_ml / self.FLOW_RATE_ML_PER_S
        return 2 * move_time_s + self.PAUSE_DURATION_S

    def status(self, stomach_volume_ml: float, t_in_cycle_s: float) -> PumpStatus:
        """
        Statut de la pompe seringue à un instant donné du cycle courant.
        `t_in_cycle_s` : temps écoulé depuis le début du cycle en cours
        Retourne IDLE si le volume de l'estomac est sous le seuil des 100 mL
        """
        if stomach_volume_ml < self.MIN_ACTIVE_VOLUME_ML:
            return PumpStatus(PumpState.IDLE, 0.0)

        draw_ml = self.draw_volume(stomach_volume_ml)
        move_time_s = draw_ml / self.FLOW_RATE_ML_PER_S
        flow_ml_per_min = self.FLOW_RATE_ML_PER_S * 60.0

        if t_in_cycle_s < move_time_s:
            return PumpStatus(PumpState.DRAWING, flow_ml_per_min)
        elif t_in_cycle_s < move_time_s + self.PAUSE_DURATION_S:
            return PumpStatus(PumpState.PAUSED, 0.0)
        else:
            return PumpStatus(PumpState.PUSHING, flow_ml_per_min)


class ReciprocatingPump(Pump):
    """
    Pompe va-et-vient de R3 (T3) 

    Fonctionne à 45 rpm selon un cycle fixe : 1 s d'aspiration ou de poussée, suivie de 2 s d'attente entre chaque action. 
    Le cycle complet (aspiration - attente - poussée - attente) dure donc 6 s tout au long de la digestion, indépendamment du volume.
    """

    RPM = 45.0
    ACTION_DURATION_S = 1.0
    WAIT_DURATION_S = 2.0
    CYCLE_DURATION_S = 2 * ACTION_DURATION_S + 2 * WAIT_DURATION_S  # 6 s

    def __init__(self):
        super().__init__("Pompe va-et-vient R3 (T3)")

    def status(self, t_s: float) -> PumpStatus:
        """
        Statut de la pompe au temps `t_s` (secondes depuis le début de la digestion). 
        Séquence répétée toutes les 6 s : aspiration (1 s) -> pause (2 s) -> poussée (1 s) -> pause (2 s)
        """
        t_in_cycle = t_s % self.CYCLE_DURATION_S

        if t_in_cycle < self.ACTION_DURATION_S:
            return PumpStatus(PumpState.DRAWING)
        t_in_cycle -= self.ACTION_DURATION_S

        if t_in_cycle < self.WAIT_DURATION_S:
            return PumpStatus(PumpState.PAUSED)
        t_in_cycle -= self.WAIT_DURATION_S

        if t_in_cycle < self.ACTION_DURATION_S:
            return PumpStatus(PumpState.PUSHING)

        return PumpStatus(PumpState.PAUSED)