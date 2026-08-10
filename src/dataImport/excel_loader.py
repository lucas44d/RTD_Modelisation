"""
Auteur : Lucas Durand
Fichier permettant de charger les données du fichier excel lu dans les classes respectives.
"""
import pandas as pd

from src.models.digestion_profile import DigestionProfile
from src.models.simulation_parameter import SimulationParameter
from src.models.meal_parameter import MealParameter
from src.models.particle_type import ParticleType
from src.models.experiment_configuration import ExperimentConfiguration


INCH_TO_METER = 0.0254

"""classe qui permet de charger les données d'un fichier excel dans les classes respectives"""
class ExcelLoader:
    """Fonction qui permet de charger les données de simulation"""
    def load_simulation_parameter(self, filename: str, sheet: str) -> SimulationParameter:
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename, sheet)

        row = df.iloc[0]

        transition_flow_T1 = self._load_transition_flows(filename, sheet="Pompe Transition T1")
        transition_flow_T2 = self._load_transition_flows(filename, sheet="Pompe Transition T2")

        return SimulationParameter(
            config_name = row["Nom de la config"],
            enzyme_volume = row["Volume enzyme (ml)"],
            enzyme_flow=row["Débit d'entrée enzyme"],
            enzyme_entry_period=row["Période d'entrée enzyme"],                
            simulation_duration=row["Durée totale de simulation (min)"] *60,  # converti en secondes
            time_step=row["Pas de temps"],
            transition_flow_T1=transition_flow_T1,
            transition_flow_T2=transition_flow_T2
        )
            
 
    """Fonction pour charger les données d'un profil de digestion"""
    def load_digestion_profile(self, filename: str, sheet: str) -> list[DigestionProfile]: 
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename, sheet)
                    
        row = df.iloc[0]

        reciprocating_pump = self._load_reciprocating_pump_parameters(filename, sheet="Va-et-vient tubulaire")
        mixing_speed_R1 = self._load_mixing_R1_parameters(filename, sheet="Brassage R1")

        return DigestionProfile(
            profile_name = row["Nom du profil"],
            reciprocating_flow = reciprocating_pump["flow_rate"],
            reciprocating_action_duration = reciprocating_pump["action_duration"],
            reciprocating_wait_duration = reciprocating_pump["wait_duration"],
            mixing_speed_R1 = mixing_speed_R1,
            mixing_speed_R2 = row ["Vitesse de brassage dans R2"],
            emulsion_mixing_speed = row ["Vitesse de brassage de l'émulsion"],
            emulsion_mixing_period = row ["Période de brassage de l'émulsion"],
            reciprocating_stiring_speed = row ["Vitesse d'agitation du va et vient de R1"],
            reciprocation_striring_period = row ["Période d'agitation du va et vient de R1"],
        )  
                 

    """Fonction pour charger les données d'entrée d'un repas"""
    def load_meal_parameters(self, filename: str, sheet: str, particle_sheet : str) :
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename, sheet)
        row = df.iloc[0]

        #Instanciation de la liste des particules pour ce repas
        particles = self._load_particles(filename, particle_sheet)
        
        return MealParameter(
            meal_flow = row ["Débit d'entrée de repas ml/min"],
            meal_entry_period = row ["Période d'entrée de repas (min)"] *60, # converti en secondes
            viscosity = row ["Viscosité"],
            total=row["Total particules"],
            particles = particles.copy()
        )    

    """Fonction privée qui permet d'importer les données sur les particules"""
    def _load_particles(self, filename: str, sheet: str) -> list[ParticleType]:
        #Instanciation d'une dataframe pour récupérer toutes les données de la feuille excel des particules
        df = pd.read_excel(filename, sheet_name=sheet)

        particles = []

        #Parcours de la df pour récupérer les données des particules et remplir la liste des particules
        for _, row in df.iterrows():
            particles.append(
                ParticleType(
                    particle_density=row["Densité"],
                    particle_size=row["Taille (pouce)"] * INCH_TO_METER, #Récupérée en pouce et converti directement en mètre
                    count=row["Nombre"],
                )
            )
        #Retour de la liste des particules
        return particles

    def _load_transition_flows(self, filename: str, sheet: str) -> dict:
        df = pd.read_excel(filename, sheet_name=sheet)        
        t_periods = []
        
        # Parcours de la DataFrame row par row
        for _, row in df.iterrows():
            # Conversion du temps au format HH:MM:SS
            start_time = row["Début période"]
            end_time = row["Fin période"]
            
            # Si pandas a interprété le temps comme datetime.time ou pd.Timestamp/timedelta :
            if hasattr(start_time, "strftime"):
                start_str = start_time.strftime("%H:%M:%S")
            else:
                start_str = str(start_time)
                
            if hasattr(end_time, "strftime"):
                end_str = end_time.strftime("%H:%M:%S")
            else:
                end_str = str(end_time)
            
            # Récupération et conversion du débit et du volume (en int ou float selon besoin)
            debit = int(row["Débit (ml/min)"])
            volume = int(row["volume total"])
            
            # Ajout du tuple à la liste
            t_periods.append((start_str, end_str, debit, volume))
        #Structuration dans le dictionnaire final
        if sheet == "Pompe Transition T1":
            return {"T1": t_periods}
        else :
            return {"T2": t_periods}

    def _load_reciprocating_pump_parameters(self, filename: str, sheet: str) -> dict:
        df = pd.read_excel(filename, sheet_name=sheet)
        row = df.iloc[0]
        return {
            "flow_rate": row["Débit (ml/min)"],
            "action_duration": row["Durée active"],
            "wait_duration": row["Durée pause"]
        }

    def _load_mixing_R1_parameters(self, filename: str, sheet: str) -> dict:
        df = pd.read_excel(filename, sheet_name=sheet)
        row = df.iloc[0]
        return {
            "slope": row["Coefficient de pente (a)"],
            "intercept": row["Ordonnée à l'origine (b)"]
        }

    def load_configuration(self, filename: str) -> ExperimentConfiguration :
        digestion = self.load_digestion_profile(filename,"Profil digestion")
        simulation = self.load_simulation_parameter(filename, "Parametres simulation")
        meal = self.load_meal_parameters(filename, "Parametres repas","Particules")

        return ExperimentConfiguration(
            digestion_profile=digestion,
            simulation_parameter=simulation,
            meal_parameter=meal
        )