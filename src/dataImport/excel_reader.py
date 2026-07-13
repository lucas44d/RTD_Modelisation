from fileinput import filename

import pandas as pd

class ExcelReader:
    
    def read_sheet(self, filename, sheet):
        xls = pd.ExcelFile(filename)
        return pd.read_excel(filename, sheet)