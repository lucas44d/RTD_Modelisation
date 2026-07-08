"""
Assemble le système complet IViDiS : instancie tous les bioréacteurs (R1 à R5) et les pompes liées à l'agitation. 
Sert de point d'entrée unique pour consulter les volumes et l'état d'agitation de l'ensemble du système à un instant donné.
"""

"""Importations locales des différents bioréacteurs et pompes du système IViDiS."""
from .reactor import (
    StomachReactor,
    PreduodenumReactor,
    DuodenumReactor,
    JejunumReactor,
    IleonReactor,
    StomieReactor,
)
from .pump import SyringePump, ReciprocatingPump


class DigestionSystem:
    """Représente le système de digestion in vitro dynamique (IViDiS)"""

    def __init__(self, use_stomie: bool = False, initial_stomach_volume_ml: float = 0.0, initial_preduodenum_volume_ml: float = 0.0):
        self.r1_stomach = StomachReactor(initial_volume_ml=initial_stomach_volume_ml)
        self.r2_preduodenum = PreduodenumReactor(initial_volume_ml=initial_preduodenum_volume_ml)
        self.r3_duodenum = DuodenumReactor()
        self.r4_jejunum = JejunumReactor()

        # On peut choisir entre R5 = Iléon ou R5 = Stomie selon la configuration du système.
        self.r5_ileon_or_stomie = StomieReactor() if use_stomie else IleonReactor() 

        self.syringe_pump = SyringePump()
        self.reciprocating_pump_t3 = ReciprocatingPump()

    @property
    def reactors(self):
        return [
            self.r1_stomach,
            self.r2_preduodenum,
            self.r3_duodenum,
            self.r4_jejunum,
            self.r5_ileon_or_stomie,
        ]

    def total_volume(self) -> float:
        """Volume total instantané du système (mL), somme de tous les réacteurs"""
        return sum(r.volume for r in self.reactors)

    def volumes_summary(self) -> dict:
        """Retourne un dictionnaire {nom_réacteur: volume (mL)}"""
        return {r.name: round(r.volume, 3) for r in self.reactors}

    def agitation_summary(self, t_s: float = 0.0,t_in_syringe_cycle_s: float = 0.0) -> dict:
        """
        Résumé de l'état de tous les systèmes d'agitation à un instant donné

        t_s : temps écoulé depuis le début de la digestion (pour T3)
        t_in_syringe_cycle_s : temps écoulé dans le cycle courant de la pompe seringue de R1
        """
        return {
            "Barreau magnétique R1": self.r1_stomach.magnetic_stirrer_status(),
            "Agitateur à pale R1": self.r1_stomach.paddle_stirrer_status(),
            "Pompe seringue R1": self.syringe_pump.status(self.r1_stomach.volume, t_in_syringe_cycle_s),
            "Barreau magnétique R2": self.r2_preduodenum.magnetic_stirrer_status(),
            "Pompe va-et-vient T3": self.reciprocating_pump_t3.status(t_s),
        }