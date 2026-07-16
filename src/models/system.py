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
from .pump import (
    SyringePump, 
    ReciprocatingPump,
    build_digestive_solution_pumps,
    build_transfer_pumps,
    )
from .operating_conditions import OperatingConditions
from src.dataImport.excel_loader import ExcelLoader
from src.simulation.experiment_configuration import ExperimentConfiguration

class DigestionSystem:
    """Représente le système de digestion in vitro dynamique (IViDiS)"""

    def __init__(self,config: ExperimentConfiguration, use_stomie: bool = False, initial_stomach_volume_ml: float = 0.0, initial_preduodenum_volume_ml: float = 0.0, operating_conditions: OperatingConditions = None,):
        self.config = config
        self.r1_stomach = StomachReactor(initial_volume_ml=initial_stomach_volume_ml)
        self.r2_preduodenum = PreduodenumReactor(config, initial_volume_ml=initial_preduodenum_volume_ml)
        self.r3_duodenum = DuodenumReactor()
        self.r4_jejunum = JejunumReactor()
        # On peut choisir entre R5 = Iléon ou R5 = Stomie selon la configuration du système.
        self.r5_ileon_or_stomie = StomieReactor() if use_stomie else IleonReactor() 

        #Pompes liées à l'agitation
        self.syringe_pump = SyringePump(config)
        self.reciprocating_pump_t3 = ReciprocatingPump(config)
        
        #Pompes de dosage et de transfert
        self.digestive_pumps = build_digestive_solution_pumps()  
        self.transfer_pumps = build_transfer_pumps()  

        # Conditions de fonctionnement du système IViDiS
        self.operating_conditions = operating_conditions or OperatingConditions() 
        
    @property
    def reactors(self):
        return [
            self.r1_stomach,
            self.r2_preduodenum,
            self.r3_duodenum,
            self.r4_jejunum,
            self.r5_ileon_or_stomie,
        ]


    """Fonctions pour retourner des infos sur le système complet à un instant donné"""
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
            "Émulsion de R1": self.syringe_pump.status(self.r1_stomach.volume, t_in_syringe_cycle_s),
            "Barreau magnétique R2": self.r2_preduodenum.magnetic_stirrer_status(),
            "Pompe va-et-vient T3": self.reciprocating_pump_t3.status(t_s),
        }
    
    #Débit instantané (mL/min) de toutes les pompes de dosage et de transfert au temps t_s
    def flow_rates_summary(self, t_s: float) -> dict:       
        summary = {}
        for name, pump in self.digestive_pumps.items():
            summary[name] = pump.flow_rate_at(t_s)
        for name, pump in self.transfer_pumps.items():
            summary[name] = pump.flow_rate_at(t_s)
        return summary
 