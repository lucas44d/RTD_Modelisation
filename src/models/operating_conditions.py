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
    #TODO : Tenir compte du profil de pH dans le temps.


    def __str__(self):
        return (
            f"Température : {self.temperature} °C\n"
            f"Pression : {self.pressure/1000:.1f} kPa\n"
            f"Densité : {self.fluid_density} kg/m³\n"
            f"Viscosité : {self.fluid_viscosity} Pa.s\n"
            f"pH : {self.pH}"
        )
