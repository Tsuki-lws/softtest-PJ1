from collections import Counter
import time
from typing import Any, List, Optional, Tuple

from fuzzer.grey_box_fuzzer import GreyBoxFuzzer
from runner.function_coverage_runner import FunctionCoverageRunner
from runner.runner import Runner
from schedule.path_power_schedule import PathPowerSchedule
from utils.coverage import Location
from utils.seed import Seed

EDGE_COUNT_CAP = 8
START_NODE: Location = ("<START>", 0)
END_NODE: Location = ("<END>", 0)


class PathGreyBoxFuzzer(GreyBoxFuzzer):
    """Count how often edge-based execution paths are exercised."""

    def __init__(self, seeds: List[str], schedule: PathPowerSchedule, is_print: bool,
                 persist_dir: str = "_persist"):
        super().__init__(seeds, schedule, False, persist_dir=persist_dir)
        self.is_print = is_print
        self.schedule: PathPowerSchedule = schedule
        self.last_path_time = self.start_time
        self.unique_paths: set = set()
        self._last_path_key: Optional[Tuple] = None

        if is_print:
            print("""
┌───────────────────────┬───────────────────────┬───────────────────────┬───────────────────┬───────────────────┬────────────────┬───────────────────┐
│        Run Time       │     Last New Path     │    Last Uniq Crash    │    Total Execs    │    Total Paths    │  Uniq Crashes  │   Covered Lines   │
├───────────────────────┼───────────────────────┼───────────────────────┼───────────────────┼───────────────────┼────────────────┼───────────────────┤""")

    @staticmethod
    def build_path_key(trace: List[Location]) -> Tuple:
        """Build a stable edge-frequency signature from an ordered line trace."""
        nodes = [START_NODE] + trace + [END_NODE]
        edge_counts = Counter(zip(nodes, nodes[1:]))
        return tuple(sorted(
            (src, dst, min(count, EDGE_COUNT_CAP))
            for (src, dst), count in edge_counts.items()
        ))

    def _make_seed(self, runner: FunctionCoverageRunner) -> Seed:
        """Attach the current edge-path key to the new seed."""
        path_key = self.build_path_key(runner.trace())
        self._last_path_key = path_key
        return Seed(self.inp, runner.coverage(), path_key=path_key)

    def print_stats(self):
        if not self.is_print:
            return

        def format_seconds(seconds):
            hours = int(seconds) // 3600
            minutes = int(seconds % 3600) // 60
            remaining_seconds = int(seconds) % 60
            return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"

        template = """│{runtime}│{path_time}│{crash_time}│{total_exec}│{total_path}│{uniq_crash}│{covered_line}│
├───────────────────────┼───────────────────────┼───────────────────────┼───────────────────┼───────────────────┼────────────────┼───────────────────┤"""
        template = template.format(runtime=format_seconds(time.time() - self.start_time).center(23),
                                   path_time=format_seconds(self.last_path_time - self.start_time).center(23),
                                   crash_time=format_seconds(self.last_crash_time - self.start_time).center(23),
                                   total_exec=str(self.total_execs).center(19),
                                   total_path=str(len(self.unique_paths)).center(19),
                                   uniq_crash=str(len(set(self.crash_map.values()))).center(16),
                                   covered_line=str(len(self.covered_line)).center(19))
        print(template)

    def run(self, runner: FunctionCoverageRunner) -> Tuple[Any, str]:  # type: ignore
        """Inform scheduler about edge-path frequency."""
        self._last_path_key = None
        result, outcome = super().run(runner)  # GreyBoxFuzzer.run handles coverage/crash/persist

        # _make_seed was called by GreyBoxFuzzer.run only when new coverage was found (PASS).
        # For all other outcomes compute the path key directly from the trace.
        path_key = (self._last_path_key
                    if self._last_path_key is not None
                    else self.build_path_key(runner.trace()))

        if path_key not in self.unique_paths:
            self.unique_paths.add(path_key)
            self.last_path_time = time.time()

        self.schedule.update_path_frequency(path_key)

        return result, outcome
