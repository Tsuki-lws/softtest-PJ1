from typing import Sequence, Tuple

from schedule.path_power_schedule import PathPowerSchedule
from utils.seed import Seed


class CoveragePowerSchedule(PathPowerSchedule):
    """Coverage-Size Based schedule (reference direction 2).

    Seeds that touch more code lines in a single execution usually carry more
    useful program state or reach deeper logic branches, so they get more
    energy. Energy grows with ``len(seed.coverage)``, controlled by ``cov_exp``.
    """

    def __init__(self, cov_exp: float = 1.0) -> None:
        super().__init__()
        self.cov_exp = cov_exp

    def update_path_frequency(self, path: Tuple) -> None:
        # This strategy does not use path frequency; skip tracking to save memory.
        pass

    def assign_energy(self, population: Sequence[Seed]) -> None:
        for seed in population:
            seed.energy = (len(seed.coverage) + 1) ** self.cov_exp
