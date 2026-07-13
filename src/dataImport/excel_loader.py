import pandas as pd

from src.models.digestion_profile import DigestionProfile
from src.models.simulation_parameter import SimulationParameter
from src.models.meal_parameter import MealParameter


"""classe qui permet de charger les données d'un fichier excel dans les classes respectives"""
class ExcelLoader:
    """Fonction qui permet de charger les données de simulation"""
    def load_simulation_parameter(self, filename: str) -> list[SimulationParameter]:
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename)
        #Instanciation d'une liste pour rentrer différents paramètres de simulation
        simulation_parameters = []

        #Parcours de la df pour récupérer chaque donnée et les injecter dans la classe adéquate
        for _, row in df.iterrows():

            simulation_parameter = SimulationParameter(
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
    def load_digestion_profile(self, filename: str) -> list[DigestionProfile]: 
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename)
        #Instanciation d'une liste pour rentrer chaque profil de digestion du tableau
        digestion_profiles = []

        #Parcours de la df pour récupérer chaque donnée et les injecter dans la classe adéquate
        for _, row in df.iterrows():
            digestion_profile = DigestionProfile(
                profile_name = row["Nom du profil"],
                reciprocating_flow = row ["débit du va-et-vient"], 
                reciprocating_period = row ["période du va-et-vient"], 
                mixing_speed_R1 = row ["vitesse de brassage dans R1"],
                mixing_speed_R2 = row ["vitesse de brassage dans R2"],
                emulsion_mixing_speed = row ["vitesse de brassage de l'émulsion"],
                emulsion_mixing_period = row ["période de brassage de l'émulsion"],
                reciprocating_stiring_speed = row ["vitesse d'agitation du va-et-vient de R1"],
                reciprocation_striring_period = row ["période d'agitation du va-et-vient de R1"],
            )  
            #Ajout du profil à la liste des profils de digestion
            digestion_profiles.append(digestion_profile)
                    
        #retour de la liste des profils de digestion
        return digestion_profiles             

    """Fonction pour charger les données d'entrée d'un repas"""
    def load_meal_parameters(self, filename: str) -> list[MealParameter]:
        #Charge les données du fichier excel dans un dataFrame python
        df = pd.read_excel(filename)
        #Instanciation d'une liste pour rentrer différents paramètres de repas
        meal_parameters = []

        #Parcours de la df pour récupérer chaque donnée et les injecter dans la classe adéquate
        for _, row in df.iterrows():
            meal_parameter = MealParameter(
                meal_flow = row ["débit d'entrée de repas"],
                meal_entry_period = row ["péridoe d'entrée de repas"],
                particle_size = row ["taille des particules"],
                particle_density = row ["densité des particules"],
                viscosity = row ["viscosité"],
            )
            #Ajout des paramètres de repas à une liste contenant différents paramètres de repas
            meal_parameters.append(meal_parameter)

        #retour de la liste paramètres de repas
        return meal_parameters