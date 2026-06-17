from typing import Dict, Sequence, Tuple

from schedule.path_power_schedule import PathPowerSchedule
from utils.coverage import Location
from utils.seed import Seed

SENTINEL_NODES = ("<START>", "<END>")


class RareLinePowerSchedule(PathPowerSchedule):
    """Rare-Line Based schedule (reference direction 3).

    Tracks how often each code line is executed across the whole run. A seed
    that touches lines that have rarely been triggered gets very high energy,
    pushing the fuzzer toward under-explored code.

    The global line-execution counts are harvested from the edge path key that
    ``PathGreyBoxFuzzer`` already passes to ``update_path_frequency`` (each edge
    is ``(src, dst, count)``), so no change to the fuzzer is needed.
    """

    def __init__(self) -> None:
        super().__init__()
        self.line_frequency: Dict[Location, int] = {}

    def update_path_frequency(self, path: Tuple) -> None:
        # `path` is a tuple of (src, dst, count) edges. Entering a node `count`
        # times means its line executed `count` times this run.
        for src, dst, count in path:
            if dst[0] not in SENTINEL_NODES:
                self.line_frequency[dst] = self.line_frequency.get(dst, 0) + count

    def assign_energy(self, population: Sequence[Seed]) -> None:
        for seed in population:
            score = 0.0
            for line in seed.coverage:
                score += 1.0 / self.line_frequency.get(line, 1)
            seed.energy = score if score > 0 else 1e-6
