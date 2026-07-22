import sys
from src.dataImport.excel_loader import ExcelLoader

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QDoubleSpinBox, QProgressBar, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from src.models.system import DigestionSystem
from src.models.operating_conditions import OperatingConditions


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loader = ExcelLoader()
        config = loader.load_configuration("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx")
        # Instantier le modèle
        self.system = DigestionSystem(config, initial_stomach_volume_ml=400.0, initial_preduodenum_volume_ml=150.0)

        # Configuration de la fenêtre principale
        self.setWindowTitle("Simulation Système Digestif In Vitro")
        self.resize(700, 450)

        # Initialiser l'UI
        self._init_ui()

    def _init_ui(self):
        # Widget central obligatoire dans une QMainWindow
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Disposition principale (Horizontale : Panneau Contrôle | Panneau Affichage)
        main_layout = QHBoxLayout(central_widget)

        # Panneau de Contrôle (Gauche)
        control_group = QGroupBox("Paramètres & Contrôle")
        control_layout = QVBoxLayout(control_group)

        # Spinbox pour le pH
        control_layout.addWidget(QLabel("pH de départ :"))
        self.ph_input = QDoubleSpinBox()
        self.ph_input.setRange(0.0, 14.0)
        self.ph_input.setSingleStep(0.1)
        control_layout.addWidget(self.ph_input)

        # Boutons Lancer / Pause / Reset
        self.btn_start = QPushButton("Démarrer Simulation")
        self.btn_start.clicked.connect(self._toggle_simulation)
        control_layout.addWidget(self.btn_start)

        self.btn_reset = QPushButton("Réinitialiser")
        self.btn_reset.clicked.connect(self._reset_simulation)
        control_layout.addWidget(self.btn_reset)

        control_layout.addStretch()  # Empousse les éléments vers le haut

        # 2. Panneau de Visualisation / Status (Droite)
        display_group = QGroupBox("État du Recteur / Organe")
        display_layout = QVBoxLayout(display_group)

        self.label_ph = QLabel(f"pH actuel : {self.system.operating_conditions.pH}")
        self.label_ph.setStyleSheet("font-size: 16px; font-weight: bold;")
        display_layout.addWidget(self.label_ph)

        display_layout.addWidget(QLabel("Progression de la digestion :"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        display_layout.addWidget(self.progress_bar)

        display_layout.addStretch()

        # Ajouter les deux panneaux à la vue principale
        main_layout.addWidget(control_group, stretch=1)
        main_layout.addWidget(display_group, stretch=2)

    # -----------------------------------------------------------------
    # Slots / Logique de liaison
    # -----------------------------------------------------------------
    def _toggle_simulation(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_start.setText("Reprendre Simulation")
        else:
            # Appliquer le pH configuré avant de démarrer
            self.system.operating_conditions.pH = self.ph_input.value()
            self.timer.start(500)  # Exécute un pas toutes les 500ms
            self.btn_start.setText("Pause")

    def _executer_etape_simulation(self):
        # Faire avancer le modèle d'une étape
        #self.estomac.simuler_etape(temps_ecoule_min=1)

        # Mettre à jour l'interface
        #self.progress_bar.setValue(int(self.estomac.taux_digestion))
        self.label_ph.setText(f"pH actuel : {self.estomac.ph:.2f}")

        # Arrêt automatique à 100%
        """if self.estomac.taux_digestion >= 100:
            self.timer.stop()
            self.btn_start.setText("Terminé")
        """

    def _reset_simulation(self):
        self.timer.stop()
        #self.estomac.taux_digestion = 0.0
        self.progress_bar.setValue(0)
        self.btn_start.setText("Démarrer Simulation")
        self.label_ph.setText(f"pH actuel : {self.ph_input.value():.2f}")