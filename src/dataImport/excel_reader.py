from fileinput import filename

import pandas as pd

class ExcelReader:
    
    def read_sheet(self, filename, sheet):
        xls = pd.ExcelFile(filename)
        print("\n\n\n\n==========================================\nVoici le fichier excel : ",xls.sheet_names)
        return pd.read_excel(filename, sheet_name="Feuil1")