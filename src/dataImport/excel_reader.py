from fileinput import filename

import pandas as pd

"""Classe qui permet la gestion de la lecture des fichiers excel"""
class ExcelReader:    

    """Ouverture d'un fichier excel avec Pandas"""
    def read_sheet(self, filename, sheet):
        return pd.read_excel(filename, sheet)