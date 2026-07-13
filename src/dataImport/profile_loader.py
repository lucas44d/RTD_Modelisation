import pandas as pd

from src.models.digestion_profile import DigestionProfile
from src.models.simulation_parameter import SimulationParameter
from src.models.meal_parameter import MealParameter

class ProfileLoader:
    def load_simulation_parameter(self, filename: str) -> list[SimulationParameter]:

        df = pd.read_excel(filename)

        simulation_parameters = []

        for _, row in df.iterrows():

            simulation_parameter = SimulationParameter(
                enzyme_flow=row["Débit d'entrée enzyme"],
                enzyme_entry_period=row["Période d'entrée enzyme"],
                simulation_duration=row["Durée totale de simulation"],
                time_step=row["Pas de temps"],
                transition_flow=row["Débit de transition"]
            )

            simulation_parameters.append(simulation_parameter)
        return simulation_parameters
 
    def load_digestion_profile(self, filename: str) -> list[DigestionProfile]: 
        df = pd.read_excel(filename)

        digestion_profiles = []

        for _, row in df.iterrows():
            digestion_profile = DigestionProfile(
                profile_name=row["Nom du profil"],
                #faire de même avec les autres param
            )  
            digestion_profiles.append(digestion_profile)
        
        return digestion_profiles             


    def load_meal_parameters(self, filename: str) -> list[MealParameter]:
        df = pd.read_excel(filename)

        meal_parameters = []

        for _, row in df.iterrows():
            meal_parameter = MealParameter(
                #ajouter les param des repas 
            )
            meal_parameters.append(meal_parameter)

        return meal_parameters