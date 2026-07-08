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

from src.models.reactor import Reactor


def main():

    stomach = Reactor("Estomac")

    intestine = Reactor("Intestin")

    print(stomach)

    print(intestine)


if __name__ == "__main__":
    main()