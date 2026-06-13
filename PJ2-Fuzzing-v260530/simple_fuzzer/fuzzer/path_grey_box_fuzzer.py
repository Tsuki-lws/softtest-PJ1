import time
from typing import List, Tuple, Any

from fuzzer.grey_box_fuzzer import GreyBoxFuzzer
from schedule.path_power_schedule import PathPowerSchedule
from runner.function_coverage_runner import FunctionCoverageRunner


class PathGreyBoxFuzzer(GreyBoxFuzzer):
    """Count how often individual paths are exercised."""

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
        """Inform scheduler about path frequency"""
        result, outcome = super().run(runner)

        # Track path: use the coverage set as the path identifier
        path_key = tuple(sorted(runner.coverage())) if runner.coverage() else ()
        if path_key and path_key not in self.unique_paths:
            self.unique_paths.add(path_key)
            self.last_path_time = time.time()
        # Update frequency in the schedule
        self.schedule.update_path_frequency(path_key)

        return result, outcome
