from typing import Dict, Sequence, Tuple

from schedule.path_power_schedule import PathPowerSchedule
from utils.seed import Seed


class HybridPowerSchedule(PathPowerSchedule):
    """A new scheduler that mixes several heuristics into one energy score.

    Unlike :class:`PathPowerSchedule`, which only looks at how often a path was
    exercised, this scheduler combines three complementary signals:

    1. Path rarity   - seeds exercising rarely seen paths are preferred
                       (inherited path-frequency idea, weighted by ``rarity_exp``).
    2. Coverage size - seeds that reach more code lines in a single execution
                       usually carry more program state (weighted by ``cov_exp``).
    3. Length penalty- shorter inputs run faster and tend to hit core logic
                       without noisy bytes (weighted by ``len_exp``).

    On top of that an optional rare-line bonus rewards seeds that touch lines
    only a few population members cover, pushing the fuzzer toward branches that
    are still under-explored.

    The weights are exposed through the constructor so the strategy can be tuned
    per sample, and so the same class can be reduced to a single heuristic for
    ablation (e.g. ``cov_exp=0, len_exp=0`` behaves like pure path frequency).

    Performance note: the coverage-size, length and rare-line terms only change
    when the population changes, so they are cached as a per-seed *base factor*
    and recomputed only when the population grows or is trimmed. The path-rarity
    term changes on every execution, so it is refreshed cheaply (one dict lookup
    per seed) on every call. This keeps ``choose()`` close to O(population) on
    the hot path, which matters for samples with large coverage sets (sample4).
    """

    def __init__(self,
                 rarity_exp: float = 1.0,
                 cov_exp: float = 1.0,
                 len_exp: float = 0.5,
                 rare_line_weight: float = 1.0) -> None:
        super().__init__()
        self.rarity_exp = rarity_exp
        self.cov_exp = cov_exp
        self.len_exp = len_exp
        self.rare_line_weight = rare_line_weight
        self._cached_pop_size = -1

    def _seed_path_key(self, seed: Seed) -> Tuple:
        path_key = getattr(seed, "path_key", None)
        if path_key is None:
            path_key = tuple(sorted(seed.coverage))
        return path_key

    def _recompute_base_factors(self, population: Sequence[Seed]) -> None:
        """Cache the population-dependent part of each seed's energy.

        ``base_factor = coverage_size * length_penalty * rare_line_bonus``
        """
        line_freq: Dict[object, int] = {}
        for seed in population:
            for line in seed.coverage:
                line_freq[line] = line_freq.get(line, 0) + 1

        for seed in population:
            cov_size = (len(seed.coverage) + 1) ** self.cov_exp
            length = 1.0 / ((len(seed.data) + 1) ** self.len_exp)

            rare_line_score = 0.0
            for line in seed.coverage:
                rare_line_score += 1.0 / line_freq.get(line, 1)
            rare_line = 1.0 + self.rare_line_weight * rare_line_score

            seed._base_factor = cov_size * length * rare_line

        self._cached_pop_size = len(population)

    def assign_energy(self, population: Sequence[Seed]) -> None:
        if not population:
            return

        if len(population) != self._cached_pop_size:
            self._recompute_base_factors(population)

        for seed in population:
            freq = self.path_frequency.get(self._seed_path_key(seed), 1)
            rarity = 1.0 / (max(freq, 1) ** self.rarity_exp)
            base = getattr(seed, "_base_factor", 1.0)
            seed.energy = rarity * base
            if seed.energy <= 0:
                seed.energy = 1e-6
