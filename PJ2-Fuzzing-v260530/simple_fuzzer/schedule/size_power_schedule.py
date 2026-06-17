from typing import Sequence, Tuple

from schedule.path_power_schedule import PathPowerSchedule
from utils.seed import Seed


class SizePowerSchedule(PathPowerSchedule):
    """Size-Based schedule (reference direction 1).

    Shorter inputs get more energy: they execute faster and tend to exercise
    core logic without noisy bytes getting in the way. Energy is inversely
    proportional to input length, controlled by ``len_exp``.
    """

    def __init__(self, len_exp: float = 1.0) -> None:
        super().__init__()
        self.len_exp = len_exp

    def update_path_frequency(self, path: Tuple) -> None:
        # This strategy does not use path frequency; skip tracking to save memory.
        pass

    def assign_energy(self, population: Sequence[Seed]) -> None:
        for seed in population:
            seed.energy = 1.0 / ((len(seed.data) + 1) ** self.len_exp)
