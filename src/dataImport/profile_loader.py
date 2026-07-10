import pandas as pd

from src.models.digestion_profile import DigestionProfile


class ProfileLoader:
 def load(self, filename: str) -> list[DigestionProfile]:

        df = pd.read_excel(filename)

        profiles = []

        for _, row in df.iterrows():

            profile = DigestionProfile(
                profile_name=row["Nom du profil"],
                enzyme_flow=row["Débit d'entrée enzyme"],
                enzyme_entry_period=row["Période d'entrée enzyme"],
                simulation_duration=row["Durée totale de simulation"],
                time_step=row["Pas de temps"],
                transition_flow=row["Débit de transition"]
            )

            profiles.append(profile)
        return profiles