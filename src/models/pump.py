"""
Pompes liées aux relations d'agitation :
    - Émulsion de R1 (EmuR1 : émulsion de l'estomac)
    - Pompe va-et-vient de R3 / T3

Débits des pompes de dosage et de transfert : 
    - Pompe de solutions digestives : A3, A4, B1, C1, C2, C3, E1
    - Pompe de transfert T1, T2

Note : les pompes de dosage des solutions digestives et les pompes de transfert T1/T2 (débits variables selon un profil temporel)
seront ajoutées plus tard. Ce module ne couvre que les deux pompes décrites dans la section "Relation d'agitation" du cahier des charges.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from src.simulation.experiment_configuration import ExperimentConfiguration

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
    Émulsion de R1

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

    def __init__(self, config: ExperimentConfiguration):
        self.config = config
        super().__init__("Pompe seringue R1")
        self.flow_rate_ml_per_s = config.digestion_profile.emulsion_mixing_speed # Remplacer le speed par débit + période

    def draw_volume(self, stomach_volume_ml: float) -> float:
        """Volume aspiré pour le cycle courant (10 % du volume réel)"""
        return self.DRAW_FRACTION * stomach_volume_ml

    def cycle_duration_s(self, stomach_volume_ml: float) -> float:
        """
        Durée totale d'un cycle (aspiration + pause + poussée), en secondes.
        Les temps d'aspiration et de poussée dépendent du volume tiré, à débit constant.
        """
        draw_ml = self.draw_volume(stomach_volume_ml)
        move_time_s = draw_ml / self.flow_rate_ml_per_s
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

    def __init__(self, config : ExperimentConfiguration):
        self.config = config
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
    
"""Heures, minutes et secondes en secondes"""
def hms_to_seconds(hms: str) -> float:
    """Convertit une durée sous format 'hh:mm:ss' en secondes"""
    h, m, s = hms.split(":") # Permet de diviser le temps
    return int(h) * 3600 + int(m) * 60 + int(s)


@dataclass
class FlowSegment:
    """
    Segment de débit constant sur un intervalle de temps donné
 
    start_time_s / end_time_s : bornes de l'intervalle (secondes depuis le
                                 début de la digestion)
    flow_rate_ml_min : débit constant sur cet intervalle (mL/min)
    expected_final_volume_ml : volume final attendu sur ce segment, fourni à titre de référence/validation dans le cahier des charges (débit x durée)
    """
    start_time_s: float
    end_time_s: float
    flow_rate_ml_min: float
    expected_final_volume_ml: Optional[float] = None
 
    # Retourne la durée d'activation du segment en minute
    @property
    def duration_min(self) -> float:
        return (self.end_time_s - self.start_time_s) / 60.0
 
    # Retourne vraie/faux selon si le temps t_s est compris dans l'intervalle de fonctionnement du segment
    def contains(self, t_s: float) -> bool:
        return self.start_time_s <= t_s < self.end_time_s
 
    # Volume délivré sur ce segment (débit x durée)
    def computed_volume_ml(self) -> float:
        return self.flow_rate_ml_min * self.duration_min
 

class FlowPump(Pump):
    """
    Pompe fonctionnant selon un profil de débit constant par morceaux/segments comme défini dans le cahier des charges. 
    En dehors des segments définis, le débit est nul (pompe à l'arrêt).
    """
 
    def __init__(self, name: str, segments: Optional[List[FlowSegment]] = None, hold_last_segment: bool = False):
        super().__init__(name)
        self.segments: List[FlowSegment] = sorted(
            segments or [], key=lambda seg: seg.start_time_s
        )
        self.hold_last_segment = hold_last_segment

 
    @classmethod
    def from_hms_table(cls, name: str, rows: List[tuple], hold_last_segment: bool = False) -> "FlowPump":
        """
        Construit une pompe à partir d'une liste de tuples
        (temps_debut 'HH:MM:SS', temps_fin 'HH:MM:SS', debit_mL_min, volume_final_mL),
        directement transcrits des tableaux 2.4 / 2.5 du cahier des charges.
        """
        segments = [
            FlowSegment(
                start_time_s=hms_to_seconds(start),
                end_time_s=hms_to_seconds(end),
                flow_rate_ml_min=flow,
                expected_final_volume_ml=vol,
            )
            for start, end, flow, vol in rows
        ]
        return cls(name, segments, hold_last_segment=hold_last_segment)
 
    
    # Débit instantané (mL/min) au temps t_s; 0 si aucun segment actif
    def flow_rate_at(self, t_s: float) -> float:
        for seg in self.segments:
            if seg.contains(t_s):
                return seg.flow_rate_ml_min
 
        if self.hold_last_segment and self.segments:
            last_seg = self.segments[-1]
            if t_s >= last_seg.end_time_s:
                return last_seg.flow_rate_ml_min
 
        return 0.0
 
    # Retourne vrai/faux selon si la pompe est active (débit > 0) au temps t_s
    def is_active_at(self, t_s: float) -> bool:
        return self.flow_rate_at(t_s) > 0.0
 
    # Volume total délivré depuis le début de la digestion jusqu'à t_s 
    # (intègre le débit constant par morceaux sur les segments écoulés)
    def cumulative_volume_at(self, t_s: float) -> float:
        total = 0.0
        for seg in self.segments:
            if t_s <= seg.start_time_s:
                continue
            end = min(t_s, seg.end_time_s)
            elapsed_min = max(0.0, (end - seg.start_time_s) / 60.0)
            total += seg.flow_rate_ml_min * elapsed_min
        return total
 
    #Somme des volumes finaux attendus (référence du cahier des charges)
    def total_expected_volume_ml(self) -> float:
        return sum(seg.expected_final_volume_ml or 0.0 for seg in self.segments)
 
    #Vérification de la cohérence entre volume attendu et volume calculé pour chaque segment (tolérance par défaut : 0.01 mL)
    def validate_against_expected(self, tol_ml: float = 1e-2) -> bool:
        for seg in self.segments:
            if seg.expected_final_volume_ml is None:
                continue
            if abs(seg.computed_volume_ml() - seg.expected_final_volume_ml) > tol_ml:
                return False
        return True

# Pompes de dosage des solutions digestives
def build_digestive_solution_pumps() -> dict:
    """
    Instancie les pompes de dosage des solutions digestives, avec leurs
    profils de débit tels que transcrits du tableau 2.4.

    On a donc [temps_debut, temps_fin, debit_mL_min, volume_final_mL] pour chaque segment de débit constant.
    """
    tables = {
        "A3": [("00:00:00", "00:04:00", 10.00, 40)],
        "A4": [
            ("00:03:00", "00:04:00", 5.00, 5),
            ("00:09:00", "02:04:00", 0.5, 57.5),
        ],
        "B1": [
            ("00:15:00", "00:39:00", 0.80, 19.2),
            ("00:39:00", "00:54:00", 1.00, 15),
            ("00:54:00", "01:24:00", 0.80, 24),
            ("01:24:00", "02:04:00", 0.67, 26.8),
        ],
        "B3": [("00:05:00", "01:14:00", 0.40, 27.6)],
        "C1": [
            ("00:39:00", "00:54:00", 0.40, 6),
            ("00:54:00", "01:54:00", 1.00, 60),
            ("01:54:00", "02:24:00", 0.40, 12),
        ],
        "C2": [("00:04:00", "02:34:00", 0.20, 30)],
        "C3": [("00:00:00", "00:04:00", 5.00, 20)],
        "E1": [("00:24:00", "03:34:00", 0.30, 57)],
    }
    return {
        name: FlowPump.from_hms_table(f"Pompe {name}", rows)
        for name, rows in tables.items()
    }
 
 
""" Pompes de transfert T1 et T2 : Tableau du cahier des charges """
# Instanciation des pompes de transfert selon le tableau du CDC
def build_transfer_pumps() -> dict:
    
    tables = {
        "T1": [
            ("00:03:00", "00:09:00", 4, 24),
            ("00:09:00", "01:14:00", 7, 455),
            ("01:14:00", "01:44:00", 4, 120),
            ("01:44:00", "02:04:00", 3, 60),
        ],
        "T2": [
            ("00:18:00", "00:43:00", 9, 225),
            ("00:43:00", "01:13:00", 7, 210),
            ("01:13:00", "04:30:00", 5, 985),
        ],
    }
    return {
        name: FlowPump.from_hms_table(f"Pompe de transfert {name}", rows, hold_last_segment=True)
        for name, rows in tables.items()
    }
 