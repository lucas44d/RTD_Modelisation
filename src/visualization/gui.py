
"""
Interface graphique PySide6 :
    - Configurer les paramètres de simulation (durée, pas de temps, volumes initiaux) et le repas (types de particules)
    - Lancer la simulation
    - Visualiser les résultats : distribution E(t) et fonction cumulée F(t), statistiques de temps de résidence
    - TODO: Exporter les résultats vers un fichier Excel
"""
 
from __future__ import annotations
import sys
import time
 
 
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QGroupBox, QHeaderView, QMessageBox, QSplitter,
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
 
from src.models.system import DigestionSystem
from src.models.particle_type import ParticleType
from src.models.meal_parameter import MealParameter
from src.dataImport.excel_loader import ExcelLoader
 
from src.simulation.simulation import run_population_simulation
from src.simulation.rtd import (
    residence_time_summary,
    collect_residence_times,
    compute_E_t,
    compute_F_t,
)
from src.simulation.flow import mean_residence_time_cstr
 
from .plots import plot_residence_time_distribution, plot_cumulative_distribution


"""Tableau éditable des types de particules du repas"""
class ParticleTypeTable(QTableWidget):
 
    COLUMNS = ["Densité (kg/m^3)", "Rayon (mm)", "Nombre"]
 
    def __init__(self, particle_types, parent=None):
        super().__init__(0, len(self.COLUMNS), parent)

        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.setUpdatesEnabled(False)
        self.blockSignals(True)

        self.populate_table(particle_types)

    def populate_table(self, particle_types):
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        
        # Le code de remplissage qu'on a vu précédemment
        for particle in particle_types:
            self.add_row(
                particle.particle_density,
                particle.particle_size,
                particle.count
            )
            
        self.blockSignals(False)
        self.setUpdatesEnabled(True)


    def add_row(self, density: float = 1050.0, radius_mm: float = 0.4, count: int = 5) -> None:
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(str(density)))
        self.setItem(row, 1, QTableWidgetItem(str(radius_mm)))
        self.setItem(row, 2, QTableWidgetItem(str(count)))
 
    def remove_selected_row(self) -> None:
        row = self.currentRow()
        if row >= 0:
            self.removeRow(row)

    """
        Convertit le contenu du tableau en liste de ParticleType. 
        Le rayon est saisi en mm dans l'interface, converti en mètres
    """
    def to_particle_types(self) -> list[ParticleType]:
        
        particle_types = []
        for row in range(self.rowCount()):
            try:
                density = float(self.item(row, 0).text())
                radius_mm = float(self.item(row, 1).text())
                count = int(self.item(row, 2).text())
            except (ValueError, AttributeError):
                continue
            particle_types.append(ParticleType(
                particle_density=density,
                particle_size=radius_mm / 1000.0,  # mm -> m
                count=count,
            ))
        return particle_types
 
 
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IViDiS - Simulation RTD")
        self.resize(1100, 700)
 
        self._last_particles = None  # conservé pour un futur export Excel
 
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_config_panel(simulation_init = simulation_initialization()))
        splitter.addWidget(self._build_results_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
 
        self.setCentralWidget(splitter)
 
    """ Panneau de configuration """
    def _build_config_panel(self, simulation_init) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        meal = simulation_init["meal"]
        simulation_param = simulation_init["simulation_param"]
        particle_types = simulation_init["particle_types"]

        # Paramètres de simulation 
        sim_group = QGroupBox("Paramètres de simulation")
        sim_form = QFormLayout(sim_group)
 
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(1.0, 1_000_000.0)
        self.duration_spin.setValue(simulation_param.simulation_duration)
        self.duration_spin.setSuffix(" s")
        sim_form.addRow("Durée de simulation :", self.duration_spin)
 
        self.dt_spin = QDoubleSpinBox()
        self.dt_spin.setRange(0.1, 60.0)
        self.dt_spin.setValue(simulation_param.time_step)
        self.dt_spin.setSuffix(" s")
        sim_form.addRow("Pas de temps (Δt) :", self.dt_spin)
 
        self.stomach_volume_spin = QDoubleSpinBox()
        self.stomach_volume_spin.setRange(0.0, 700.0)
        self.stomach_volume_spin.setValue(400.0)
        self.stomach_volume_spin.setSuffix(" mL")
        sim_form.addRow("Volume initial R1 (Estomac) :", self.stomach_volume_spin)
 
        self.preduodenum_volume_spin = QDoubleSpinBox()
        self.preduodenum_volume_spin.setRange(0.0, 300.0)
        self.preduodenum_volume_spin.setValue(150.0)
        self.preduodenum_volume_spin.setSuffix(" mL")
        sim_form.addRow("Volume initial R2 (Préduodénum) :", self.preduodenum_volume_spin)
 
        layout.addWidget(sim_group)
 
        # Paramètres du repas
        meal_group = QGroupBox("Repas")
        meal_form = QFormLayout(meal_group)
 
        self.meal_flow_spin = QDoubleSpinBox()
        self.meal_flow_spin.setRange(0.0, 100.0)
        self.meal_flow_spin.setValue(meal.meal_flow)
        self.meal_flow_spin.setSuffix(" mL/min")
        meal_form.addRow("Débit d'entrée du repas :", self.meal_flow_spin)
 
        self.meal_period_spin = QDoubleSpinBox()
        self.meal_period_spin.setRange(0.0, 3600.0)
        self.meal_period_spin.setValue(meal.meal_entry_period)
        self.meal_period_spin.setSuffix(" s")
        meal_form.addRow("Période d'entrée du repas :", self.meal_period_spin)
 
        self.viscosity_spin = QDoubleSpinBox()
        self.viscosity_spin.setRange(0.0001, 1.0)
        self.viscosity_spin.setDecimals(4)
        self.viscosity_spin.setValue(meal.viscosity)
        self.viscosity_spin.setSuffix(" Pa·s")
        meal_form.addRow("Viscosité du repas :", self.viscosity_spin)
 
        layout.addWidget(meal_group)
 
        # Types de particules
        particles_group = QGroupBox("Types de particules")
        particles_layout = QVBoxLayout(particles_group)
 
        self.particle_table = ParticleTypeTable(particle_types=particle_types)
        particles_layout.addWidget(self.particle_table)
 
        row_buttons = QHBoxLayout()
        add_btn = QPushButton("+ Ajouter une ligne")
        add_btn.clicked.connect(self.particle_table.add_row)
        remove_btn = QPushButton("- Retirer la ligne sélectionnée")
        remove_btn.clicked.connect(self.particle_table.remove_selected_row)
        row_buttons.addWidget(add_btn)
        row_buttons.addWidget(remove_btn)
        particles_layout.addLayout(row_buttons)
 
        layout.addWidget(particles_group)
 
        # Actions 
        self.run_button = QPushButton("Lancer la simulation")
        self.run_button.setStyleSheet(
            "QPushButton { background-color: #3b82f6; color: white; padding: 8px; font-weight: bold; }"
        )
        self.run_button.clicked.connect(self.on_run_simulation)
        layout.addWidget(self.run_button)
 
        self.export_button = QPushButton("Exporter vers Excel (à venir)")
        self.export_button.setEnabled(False)
        self.export_button.setToolTip("Fonctionnalité prévue dans un increment ultérieur.")
        layout.addWidget(self.export_button)
 
        self.status_label = QLabel("Prêt.")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
 
        layout.addStretch()
        return panel
 
    # Panneau de résultats
    def _build_results_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
 
        self.summary_label = QLabel("Aucune simulation exécutée pour l'instant.")
        self.summary_label.setStyleSheet("font-size: 13px; padding: 6px;")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
 
        self.tabs = QTabWidget()

        # Affiche l'histogramme de E(t)
        self.e_t_canvas = FigureCanvas(plot_residence_time_distribution([], []))
        self.tabs.addTab(self.e_t_canvas, "Distribution E(t)")

        # Affiche l'histogramme de F(t)
        self.f_t_canvas = FigureCanvas(plot_cumulative_distribution([], []))
        self.tabs.addTab(self.f_t_canvas, "Fonction cumulée F(t)")
 
        layout.addWidget(self.tabs)
        return panel
 
    # Logique de simulation
    def on_run_simulation(self) -> None:

        simulation_init = simulation_initialization()
 
        # Système et repas de test 
        particle_types = simulation_init["particle_types"]
        system = simulation_init["system"]
        meal = simulation_init["meal"]
        simulation_param = simulation_init["simulation_param"]

        if not particle_types:
            QMessageBox.warning(self, "Repas vide", "Ajoutez au moins un type de particule avant de lancer la simulation.")
            return
 
        self.status_label.setText("Simulation en cours...")
        self.run_button.setEnabled(False)
        QApplication.processEvents()  # rafraîchit l'UI avant le calcul (bloquant pour le code)
 
        try:
            particles = run_population_simulation(system=system, meal=meal, dt_s=simulation_param.time_step, max_t_s=simulation_param.simulation_duration)

            self._last_particles = particles
            self._display_results(particles)
            self.status_label.setText("Simulation terminée.")
 
        except Exception as exc:  # affichage d'erreur plutôt qu'un crash
            QMessageBox.critical(self, "Erreur pendant la simulation", str(exc))
            self.status_label.setText("Erreur pendant la simulation (voir message).")
 
        finally:
            self.run_button.setEnabled(True)
 
    def _display_results(self, particles: list) -> None:
        summary = residence_time_summary(particles)
        taus = collect_residence_times(particles)
 
        # Résumé texte
        if summary["n_completed"] > 0:
            text = (
                f"<b>{summary['n_completed']} / {summary['n_total']}</b> particules ont terminé leur traversée "
                f"({summary['completion_rate'] * 100:.0f}%).<br>"
                f"Temps de résidence moyen (tau) : <b>{summary['mean_residence_time_s']:.1f} s</b> "
                f"Variance (σ²) : {summary['variance_s2']:.1f} s² | Écart-type : {summary['std_dev_s']:.1f} s"
            )
        else:
            text = "Aucune particule n'a terminé sa traversée dans la fenêtre de simulation choisie."
        self.summary_label.setText(text)
 
        # Distribution E(t)
        bin_centers, e_values = compute_E_t(taus, n_bins=20)
 
        fig_e = plot_residence_time_distribution(bin_centers, e_values)
        self._replace_canvas(self.tabs, 0, fig_e, "Distribution E(t)")
 
        # Fonction cumulée F(t) 
        t_values, f_values = compute_F_t(taus)
        fig_f = plot_cumulative_distribution(t_values, f_values)
        self._replace_canvas(self.tabs, 1, fig_f, "Fonction cumulée F(t)")
 
    @staticmethod
    def _replace_canvas(tabs: QTabWidget, index: int, figure, title: str) -> None:
        """Remplace le canvas matplotlib d'un onglet par une nouvelle figure."""
        new_canvas = FigureCanvas(figure)
        tabs.removeTab(index)
        tabs.insertTab(index, new_canvas, title)
        tabs.setCurrentIndex(index)

"""
    Fonction qui permet d'initialiser/importer les données de simulation 
    
    Renvoi un dictionnaire avec les différentes données de simulation/système
"""
def simulation_initialization():
    # Importation du tableau excel
    loader = ExcelLoader()
    config = loader.load_configuration("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx")
        
    # Système et repas de test 
    system = DigestionSystem(config, initial_stomach_volume_ml=400.0, initial_preduodenum_volume_ml=150.0)
    particle_types = loader._load_particles("C:\\Users\\lucas\\Documents\\Canada\\UdS\\Projet\\RTD_Modelisation\\resources\\Test_import.xlsx","Particules")
    meal =  config.meal_parameter
          
    # Simulation
    simulation_param = config.simulation_parameter

    return {
        "loader": loader,
        "config": config,
        "system": system,
        "particle_types": particle_types,
        "meal": meal,
        "simulation_param": simulation_param,
    }
 
def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
 
 
if __name__ == "__main__":
    main()
 