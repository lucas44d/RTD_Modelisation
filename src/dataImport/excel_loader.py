import pandas as pd

from src.models.digestion_profile import DigestionProfile
from src.models.simulation_parameter import SimulationParameter
from src.models.meal_parameter import MealParameter
from src.models.particle_type import ParticleType


"""classe qui permet de charger les données d'un fichier excel dans les classes respectives"""
class ExcelLoader:
    """Fonction qui permet de charger les données de simulation"""
    def load_simulation_parameter(self, filename: str, sheet: str) -> list[SimulationParameter]:
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename, sheet)
        #Instanciation d'une liste pour rentrer différents paramètres de simulation
        simulation_parameters = []

        #Parcours de la df pour récupérer chaque donnée et les injecter dans la classe adéquate
        for _, row in df.iterrows():

            simulation_parameter = SimulationParameter(
                config_name = row["Nom de la config"],
                enzyme_flow=row["Débit d'entrée enzyme"],
                enzyme_entry_period=row["Période d'entrée enzyme"],
                simulation_duration=row["Durée totale de simulation"],
                time_step=row["Pas de temps"],
                transition_flow=row["Débit de transition"]
            )
            #Ajout du profil à la liste des paramètres de simulation
            simulation_parameters.append(simulation_parameter)

        #retour de la liste des paramètres de simulation
        return simulation_parameters
 
    """Fonction pour charger les données d'un profil de digestion"""
    def load_digestion_profile(self, filename: str, sheet: str) -> list[DigestionProfile]: 
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename, sheet)
        #Instanciation d'une liste pour rentrer chaque profil de digestion du tableau
        digestion_profiles = []

        #Parcours de la df pour récupérer chaque donnée et les injecter dans la classe adéquate
        for _, row in df.iterrows():
            digestion_profile = DigestionProfile(
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
            #Ajout du profil à la liste des profils de digestion
            digestion_profiles.append(digestion_profile)
                    
        #retour de la liste des profils de digestion
        return digestion_profiles             

    """Fonction pour charger les données d'entrée d'un repas"""
    def load_meal_parameters(self, filename: str, sheet: str, particle_sheet : str) :
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename, sheet)

        #Instanciation de la liste des particules pour ce repas
        particles = self._load_particles(filename, particle_sheet)

        #Parcours de la df pour récupérer chaque donnée et les injecter dans la classe adéquate
        for _, row in df.iterrows():
            meal_parameter = MealParameter(
                meal_flow = row ["Débit d'entrée de repas"],
                meal_entry_period = row ["Période d'entrée de repas"],
                viscosity = row ["Viscosité"],
                particles = particles.copy()
            )

        #retour des paramètres de repas
        return meal_parameter
    
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
                    count=row["Nombre"]
                )
            )
        #Retour de la liste des particules
        return particles