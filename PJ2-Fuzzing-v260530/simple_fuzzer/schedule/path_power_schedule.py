from typing import Dict, Sequence, Tuple

from schedule.power_schedule import PowerSchedule
from utils.seed import Seed


class PathPowerSchedule(PowerSchedule):

    def __init__(self) -> None:
        super().__init__()
        self.path_frequency: Dict[Tuple, int] = {}

    def update_path_frequency(self, path: Tuple) -> None:
        """Record one observation of a path (called by PathGreyBoxFuzzer)."""
        self.path_frequency[path] = self.path_frequency.get(path, 0) + 1

    def assign_energy(self, population: Sequence[Seed]) -> None:
        """Assign energy inversely proportional to path frequency.

        Seeds that exercise rarer paths get more energy.
        """
        for seed in population:
            path_key = getattr(seed, "path_key", None)
            if path_key is None:
                path_key = tuple(sorted(seed.coverage))
            freq = self.path_frequency.get(path_key, 1)
            seed.energy = 1.0 / max(freq, 1)
