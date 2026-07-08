#import sys

#import numpy as np
#import pandas as pd

#from scipy import interpolate
#from scipy import optimize

#import matplotlib.pyplot as plt

#from openpyxl import load_workbook

#from PySide6.QtWidgets import (
#    QApplication,
#    QMainWindow,
# )

from src.models.system import DigestionSystem

def main():
    system = DigestionSystem()


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

#va et vient sur cycle complet
    print("\nCycle pompe va et vient T3 sur 6s : ")
    for t in range(0, 7):   
        print(f"  t={t}s : {system.reciprocating_pump_t3.status(float(t))}")


if __name__ == "__main__":
    main()