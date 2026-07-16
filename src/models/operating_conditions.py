from dataclasses import dataclass

@dataclass
class OperatingConditions:
    """Conditions de fonctionnement du système IViDiS"""

    #conditions fixes
    temperature : float = 37.0  #°C
    pressure : float = 101300 #en Pa // Faut-il plus de précision ?

    # Propriétés des fluides digestifs (approximation : eau = fluides digestifs)
    fluid_density : float = 993.0  #kg/m3 : On assimile la densité à une masse volumique 
    fluid_viscosity : float = 0.00069 #Pa.s


    #variable de simulation 
    pH : float = 7.0
    #Faut-il prendre en compte les valeurs du pH dans les différentes parties du système digestif :
    #1.5-3.5 pour l'estomac
    #6-6.5 pour le préduodénum
    #6-7.4 pour le Duodénum
    #7-8 pour le Jéjunum
    #7-8 pour l'Iléon
    #TODO : Tenir compte du profil de pH dans le temps.


    def __str__(self):
        return (
            f"Température : {self.temperature} °C\n"
            f"Pression : {self.pressure/1000:.1f} kPa\n"
            f"Densité : {self.fluid_density} kg/m³\n"
            f"Viscosité : {self.fluid_viscosity} Pa.s\n"
            f"pH : {self.pH}"
        )
