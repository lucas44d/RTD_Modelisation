from dataclasses import dataclass


@dataclass
class Reactor:
    """
    Représentation d'un sous-ensemble du système digestif.
    """

    name: str
    volume_ml: float = 60.0

    def get_volume(self) -> float:
        """Retourne le volume du réacteur en mL."""
        return self.volume_ml

    def set_volume(self, volume: float):
        """Modifie le volume du réacteur."""
        if volume <= 0:
            raise ValueError("Le volume doit être strictement positif.")

        self.volume_ml = volume

    def __str__(self):
        return f"{self.name} ({self.volume_ml} mL)"