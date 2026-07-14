from src.dataImport.excel_loader import ExcelLoader
from src.models.system import DigestionSystem
from src.models.pump import build_transfer_pumps, build_digestive_solution_pumps, hms_to_seconds


def main():
    system = DigestionSystem()

    #Test importation tableau excel
    print("\nTest importation tableau excel : ")
    loader = ExcelLoader()

    """Importation des paramètres de simulation"""
    simulation_parameters = loader.load_simulation_parameter("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx", "Parametres simulation")
    #print("\nParamètres de simulation : ")
    #for p in simulation_parameters:
    #    print(p)

    digestion_profiles = loader.load_digestion_profile("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx", "Profil digestion")
    #print("\n\nProfil de digestion")
    #for p in digestion_profiles:
    #    print(p)
    
    meal_parameter = loader.load_meal_parameters("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx", "Parametres repas","Particules")
    print(meal_parameter)

    choice = int(input("\nQuelle profil voulez vous choisir : "))

    print("\nVoici le profil choisi : ", choice, "\n", digestion_profiles[choice])



    """
#Volumes tubulaires fixe (incrément 1.1)
    system = DigestionSystem(initial_stomach_volume_ml=400.0,initial_preduodenum_volume_ml=150.0)
    print("Volumes des différents réacteurs :")
    for name, v in system.volumes_summary().items():
        print(f"  {name}: {v:.2f} mL")
    
    print(f"\n Volume total : {system.total_volume():.2f} mL")
    
#Relation d'agitation (incrément 1.2)
    print("\nAgitation à T=0s :")
    for name, status in system.agitation_summary(t_s=0.0, t_in_syringe_cycle_s=0.0).items():
        print(f"  {name}: {status}")

#Conditions Opératoires (incrément 1.3)
    print("\nConditions opératoires du système IViDiS :")
    print(system.operating_conditions)

#Débits des pompes de dosage et de transfert (incrément 1.4)
    all_ok = True #Variable qui permet de valdier le débit des pompes
    for name, pump in {**system.digestive_pumps, **system.transfer_pumps}.items():
        ok = pump.validate_against_expected()
        all_ok &= ok
        print(f" {name}: {'OK' if ok else 'ECHEC'} (volume total attendu = {pump.total_expected_volume_ml():.2f} ml)")
    print(f"\n -> Toutes les pompes cohérentes avec le CDC : {all_ok}")

    print("\n Débits à t = 00:20:00 (1200s)")
    t = hms_to_seconds("00:20:00")
    for name, rate in system.flow_rates_summary(t).items():
        if rate > 0:
            print(f"  {name}: {rate:.2f} mL/min")

    print("\n Volume cumulé délivré par T1 à t = 00:30:00 (1800s)")
    t2 = hms_to_seconds("00:30:00")
    print(f" T1 : {system.transfer_pumps['T1'].cumulative_volume_at(t2):.2f} ml")

#Test seuils d'arrêt pour les réacteurs (R1 et R2)
    print("\nTest des seuils estomac à 30ml")
    system.r1_stomach.set_volume(30.0)
    print(f"Barreau magnétique : {system.r1_stomach.magnetic_stirrer_status()}")
    print(f"Agitateur à pale : {system.r1_stomach.paddle_stirrer_status()}")
    print(f"Pompe seringue : {system.r1_stomach.is_syringe_pump_active}")

    print("\nTest des seuils préduodénum à 30ml")
    system.r2_preduodenum.set_volume(30.0)
    print(f"Barreau magnétique : {system.r2_preduodenum.magnetic_stirrer_status()}")
    print(f"Agitateur à pale : {system.r2_preduodenum.magnetic_stirrer_status()}")

#test de débordement
    print("\nTest de débordement à 1000ml")
    overflow = system.r1_stomach.add_volume(1000.0)
    print(f"Volume actuel : {system.r1_stomach.volume:.2f} ml, débordement : {overflow:.2f} ml")

    print("\nTest de débordement à 1000ml")
    overflow = system.r2_preduodenum.add_volume(1000.0)
    print(f"Volume actuel : {system.r2_preduodenum.volume:.2f} ml, débordement : {overflow:.2f} ml")
"""

#va et vient sur cycle complet
    print("\nCycle pompe va et vient T3 sur 6s : ")
    for t in range(0, 5):   
        print(f"  t={t}s : {system.reciprocating_pump_t3.status(float(t))}")

if __name__ == "__main__": 
    main()