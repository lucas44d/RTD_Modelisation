"""
On distingue deux familles de réacteurs, conformément aux hypothèses :

- Réacteurs agités (CSTR) à volume variable: R1 (Estomac) et R2 (Préduodénum).
  Leur volume évolue dans le temps selon les débits entrants/sortants et ils comportent un système d'agitation dont la vitesse dépend parfois du volume courant.

- Réacteurs tubulaires à volume fixe : R3 (Duodénum), R4 (Jéjunum),
  R5 (Iléon / Stomie). Conformément à l'hypothèse de régime permanent dans la partie tubulaire,
  leur volume est constant et calculé à partir de leur géométrie interne (longueur, diamètre interne).

Note : Il est mentionné dans le CDC un diamètre interne 1/4 de pouce pour les tubulures de racords de plusieurs pompes, 
doit-on prendre en compte ce diamètre pour le calcul du volume total du système ? 
Si oui -> Quelle est la longueur de ces tubulures ? (pas trouvé dans le cdc)  
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import math

from src.simulation.experiment_configuration import ExperimentConfiguration

# Constantes de conversion d'unités 
FEET_TO_M = 0.3048
INCH_TO_M = 0.0254
M3_TO_ML = 1e6  # 1 mètre cube = 1 000 000ml

"""Enumération des états possibles d'un système d'agitation"""
class AgitationState(Enum):
    STOPPED = "arrêté"
    RUNNING = "en marche"


@dataclass
class StirrerStatus:
    """État instantané d'un système d'agitation"""
    rpm: float
    state: AgitationState

    def __repr__(self) -> str:
        return f"{self.rpm:.1f} rpm ({self.state.value})"


# Classe de base
class Reactor:
    """Classe de base pour tous les bioréacteurs du système IViDiS"""

    def __init__(self, name: str, volume_ml: float):
        self.name = name
        self._volume_ml = volume_ml  # volume courant (mL)

    @property
    def volume(self) -> float:
        """Volume courant du réacteur (mL)"""
        return self._volume_ml

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name}' V={self._volume_ml:.2f} mL>"



# Réacteurs tubulaires (R3, R4, R5) — volume fixe, régime permanent
class TubularReactor(Reactor):
    """
    Réacteur tubulaire à volume fixe. 
    Le volume interne est calculé comme un cylindre : V = pi * (d_int / 2)^2 * L
    """

    def __init__(self, name: str, length_ft: float, inner_diameter_in: float):
        self.length_ft = length_ft
        self.inner_diameter_in = inner_diameter_in

        length_m = length_ft * FEET_TO_M
        diameter_m = inner_diameter_in * INCH_TO_M
        volume_m3 = math.pi * (diameter_m / 2) ** 2 * length_m
        volume_ml = volume_m3 * M3_TO_ML

        super().__init__(name, volume_ml)

    @property
    def volume(self) -> float:
        # Volume fixe
        return self._volume_ml


# Réacteurs agités (R1, R2), volume variable + agitation
class StirredReactor(Reactor):
    """
    Réacteur de type CSTR (bien mélangé) à volume variable, borné par un
    volume minimal (en dessous duquel l'agitation s'arrête) et un volume
    maximal (au-delà duquel il y a débordement).
    """

    def __init__(self, name: str, initial_volume_ml: float,
                 max_volume_ml: float, min_agitation_volume_ml: float):
        super().__init__(name, initial_volume_ml)
        self.max_volume_ml = max_volume_ml
        self.min_agitation_volume_ml = min_agitation_volume_ml
        self._overflowed_ml_total = 0.0  # volume cumulé perdu par débordement

    def set_volume(self, new_volume_ml: float) -> float:
        """
        Met à jour le volume du réacteur en respectant la contrainte de
        débordement. Retourne le volume effectivement perdu (0 si aucun)
        """
        if new_volume_ml > self.max_volume_ml:
            overflow = new_volume_ml - self.max_volume_ml
            self._overflowed_ml_total += overflow
            self._volume_ml = self.max_volume_ml
            return overflow
        self._volume_ml = max(new_volume_ml, 0.0)
        return 0.0

    def add_volume(self, delta_ml: float) -> float:
        """Ajoute (ou retire, si négatif) un volume et gère le débordement"""
        return self.set_volume(self._volume_ml + delta_ml)

    @property
    def is_agitation_active(self) -> bool:
        """L'agitation est coupée sous le seuil de volume minimal"""
        return self._volume_ml >= self.min_agitation_volume_ml

    @property
    def total_overflow(self) -> float:
        return self._overflowed_ml_total


"""Classes pour chaque réacteur spécifique (R1 à R5) et leurs caractéristiques propres (volumes, agitation, etc.)"""

# R1 — Estomac
class StomachReactor(StirredReactor):
    """
    R1 - Estomac

    Volumes :
        - Volume maximal avant débordement : 700 mL
        - Volume minimal avant arrêt de l'agitation : 50 mL
        (la pompe seringue et l'agitateur à pale s'arrêtent eux sous 100 mL, seuil distinct de celui du barreau magnétique)

    Agitation :
        - Barreau magnétique : Vitesse(rpm) = 0.5 * Volume + 200, arrêté < 50 mL
        - Agitateur à pale : 60 rpm, oscille jusqu'à 15° de la chicane avant de s'inverser, arrêté < 100 mL
    """

    MAX_VOLUME_ML = 700.0
    MIN_STIRRER_VOLUME_ML = 50.0
    MIN_PADDLE_AND_SYRINGE_VOLUME_ML = 100.0

    PADDLE_RPM = 60.0
    PADDLE_ANGLE_DEG = 15.0

    def __init__(self, initial_volume_ml: float = 0.0):
        super().__init__(
            name="R1 - Estomac",
            initial_volume_ml=initial_volume_ml,
            max_volume_ml=self.MAX_VOLUME_ML,
            min_agitation_volume_ml=self.MIN_STIRRER_VOLUME_ML,
        )

    """Relation d'agitation du barreau magnétique de R1"""
    def magnetic_stirrer_status(self) -> StirrerStatus:
        """Si le volume < 50ml, l'agitation est arretée : on retourne état stopped"""
        if self._volume_ml < self.MIN_STIRRER_VOLUME_ML:
            return StirrerStatus(0.0, AgitationState.STOPPED)
        rpm = 0.5 * self._volume_ml + 200.0
        return StirrerStatus(rpm, AgitationState.RUNNING)
    
    """Relation d'agitation de l'agitateur à pale de R1"""
    def paddle_stirrer_status(self) -> StirrerStatus:
        """Si le volume < 100ml, l'agitation est arretée : on retourne état stopped"""
        if self._volume_ml < self.MIN_PADDLE_AND_SYRINGE_VOLUME_ML:
            return StirrerStatus(0.0, AgitationState.STOPPED)
        return StirrerStatus(self.PADDLE_RPM, AgitationState.RUNNING)

    @property
    def is_syringe_pump_active(self) -> bool:
        """La pompe seringue s'arrête sous le seuil des 100 mL"""
        return self._volume_ml >= self.MIN_PADDLE_AND_SYRINGE_VOLUME_ML


# R2 — Préduodénum
class PreduodenumReactor(StirredReactor):
    """
    R2 - Préduodénum.

    Volumes :
        - Volume maximal avant débordement : 300 mL
        - Volume minimal avant arrêt de l'agitation : 50 mL

    Agitation :
        - Barreau magnétique à vitesse constante de 200 rpm (bien mélangé),arrêté sous 50 mL.
    """

    MAX_VOLUME_ML = 300.0
    MIN_STIRRER_VOLUME_ML = 50.0
    CONSTANT_RPM = 200.0

    def __init__(self, config: ExperimentConfiguration, initial_volume_ml: float = 0.0):
        self.config = config
        super().__init__(
            name="R2 - Préduodénum",
            initial_volume_ml=initial_volume_ml,
            max_volume_ml=self.MAX_VOLUME_ML,
            min_agitation_volume_ml=self.MIN_STIRRER_VOLUME_ML,
        )
        self.stiring_R2 = config.digestion_profile.mixing_speed_R2

    """Relation d'agitation du barreau magnétique de R2"""
    def magnetic_stirrer_status(self) -> StirrerStatus:
        if not self.is_agitation_active:
            return StirrerStatus(0.0, AgitationState.STOPPED)
        return StirrerStatus(self.stiring_R2, AgitationState.RUNNING)


# Réacteurs tubulaires R3, R4, R5
class DuodenumReactor(TubularReactor):
    """R3 - Duodénum : L = 4.2 pi, d_int = 3/8 po"""
    def __init__(self):
        super().__init__("R3 - Duodénum", length_ft=4.2, inner_diameter_in=3 / 8)


class JejunumReactor(TubularReactor):
    """R4 - Jéjunum : L = 12.5 pi, d_int = 3/8 po"""
    def __init__(self):
        super().__init__("R4 - Jéjunum", length_ft=12.5, inner_diameter_in=3 / 8)


class IleonReactor(TubularReactor):
    """R5 - Iléon : L = 18.8 pi, d_int = 3/8 po"""
    def __init__(self):
        super().__init__("R5 - Iléon", length_ft=18.8, inner_diameter_in=3 / 8)


class StomieReactor(TubularReactor):
    """R5 - Stomie : L = 12.5 pi, d_int = 3/8 po"""
    def __init__(self):
        super().__init__("R5 - Stomie", length_ft=12.5, inner_diameter_in=3 / 8)