import pandas as pd

from src.models.digestion_profile import DigestionProfile
from src.models.simulation_parameter import SimulationParameter
from src.models.meal_parameter import MealParameter
from src.models.particle_type import ParticleType
from src.simulation.experiment_configuration import ExperimentConfiguration


"""classe qui permet de charger les données d'un fichier excel dans les classes respectives"""
class ExcelLoader:
    """Fonction qui permet de charger les données de simulation"""
    def load_simulation_parameter(self, filename: str, sheet: str) -> SimulationParameter:
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename, sheet)

        row = df.iloc[0]
        
        return SimulationParameter(
            config_name = row["Nom de la config"],
            enzyme_volume = row["Volume enzyme (ml)"],
            enzyme_flow=row["Débit d'entrée enzyme"],
            enzyme_entry_period=row["Période d'entrée enzyme"],                
            simulation_duration=row["Durée totale de simulation"],
            time_step=row["Pas de temps"],
            transition_flow=row["Débit de transition"]
        )
            
 
    """Fonction pour charger les données d'un profil de digestion"""
    def load_digestion_profile(self, filename: str, sheet: str) -> list[DigestionProfile]: 
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename, sheet)
                    
        row = df.iloc[0]

        return DigestionProfile(
            profile_name = row["Nom du profil"],
            reciprocating_flow = row ["Débit du va et vient"], 
            reciprocating_period = row ["Période du va et vient"], 
            mixing_speed_R1 = row ["Vitesse de brassage dans R1"],
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
            meal_flow = row ["Débit d'entrée de repas"],
            meal_entry_period = row ["Période d'entrée de repas"],
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
                    particle_size=row["Taille (pouce)"],
                    count=row["Nombre"],
                )
            )
        #Retour de la liste des particules
        return particles
    
    def load_configuration(self, filename: str) -> ExperimentConfiguration :
        digestion = self.load_digestion_profile(filename,"Profil digestion")
        simulation = self.load_simulation_parameter(filename, "Parametres simulation")
        meal = self.load_meal_parameters(filename, "Parametres repas","Particules")

        return ExperimentConfiguration(
            digestion_profile=digestion,
            simulation_parameter=simulation,
            meal_parameter=meal
        )