from collections import Counter
import time
from typing import Any, List, Tuple

from fuzzer.fuzzer import Fuzzer
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
        self.total_paths = 0
        self.unique_paths: set = set()

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
        result, outcome = Fuzzer.run(self, runner)

        path_key = self.build_path_key(runner.trace())
        if path_key not in self.unique_paths:
            self.unique_paths.add(path_key)
            self.last_path_time = time.time()

        self.schedule.update_path_frequency(path_key)

        if len(self.covered_line) != len(runner.all_coverage):
            self.covered_line |= runner.all_coverage
            if outcome == Runner.PASS:
                self.population.append(Seed(self.inp, runner.coverage(), path_key=path_key))

        if outcome == Runner.FAIL:
            self.last_crash_time = time.time()
            self.crash_map[self.inp] = result

        self._maybe_persist()

        return result, outcome
