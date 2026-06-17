"""RoleD experiment driver: compare power schedules and report line coverage.

For every sample we fuzz with each schedule for a fixed time budget and report:

* target-function line coverage % - covered executable lines of the sample
  function under test, divided by the function's total executable lines
  (obtained from ``code.co_lines()``). This is the metric used for the
  "50%+ coverage" goal of the four samples.
* total covered lines - absolute number of ``(func, line)`` locations reached,
  including stdlib code the sample delegates to (e.g. HTMLParser for sample4).
* unique crashes - number of distinct crash signatures found.

Usage::

    python eval_schedules.py --run-time 60
    python eval_schedules.py --run-time 30 --samples 1 2 3 4 --schedules path hybrid
"""

import argparse
import time

from fuzzer.path_grey_box_fuzzer import PathGreyBoxFuzzer
from runner.function_coverage_runner import FunctionCoverageRunner
from samples.samples import sample1, sample2, sample3, sample4
from utils.object_utils import load_object

try:
    from main import build_schedule, SCHEDULES
except ImportError:
    from __main__ import build_schedule, SCHEDULES

SAMPLES = {
    1: (sample1, "corpus/corpus_1"),
    2: (sample2, "corpus/corpus_2"),
    3: (sample3, "corpus/corpus_3"),
    4: (sample4, "corpus/corpus_4"),
}


def make_schedule(name: str):
    return build_schedule(name)


def target_executable_lines(func):
    """All executable line numbers of `func` (one entry per real line)."""
    lines = set()
    for _start, _end, lineno in func.__code__.co_lines():
        if lineno is not None:
            lines.add(lineno)
    return lines


def run_once(sample_id: int, schedule_name: str, run_time: int):
    func, corpus = SAMPLES[sample_id]
    runner = FunctionCoverageRunner(func)
    seeds = load_object(corpus)
    fuzzer = PathGreyBoxFuzzer(seeds=seeds, schedule=make_schedule(schedule_name),
                               is_print=False, persist_dir=f"_eval/persist-{sample_id}-{schedule_name}")
    fuzzer.runs(runner, run_time=run_time)

    total_lines = target_executable_lines(func)
    covered_in_func = {ln for (fn, ln) in fuzzer.covered_line if fn == func.__name__}
    pct = 100.0 * len(covered_in_func) / max(len(total_lines), 1)

    return {
        "covered_total": len(fuzzer.covered_line),
        "func_total": len(total_lines),
        "func_covered": len(covered_in_func),
        "func_pct": pct,
        "crashes": len(set(fuzzer.crash_map.values())),
        "execs": fuzzer.total_execs,
        "paths": len(fuzzer.unique_paths),
    }


def parse_args():
    p = argparse.ArgumentParser(description="Compare power schedules across samples.")
    p.add_argument("--run-time", type=int, default=60, help="Seconds per (sample, schedule).")
    p.add_argument("--samples", type=int, nargs="+", default=[1, 2, 3, 4])
    p.add_argument("--schedules", nargs="+", default=list(SCHEDULES))
    return p.parse_args()


def main():
    args = parse_args()
    header = (f"{'Sample':>6} | {'Schedule':>8} | {'FuncCov':>14} | {'Cov%':>6} | "
              f"{'TotalLines':>10} | {'Paths':>7} | {'Crashes':>7} | {'Execs':>9}")
    print(header)
    print("-" * len(header))

    rows = {}
    for sid in args.samples:
        for sched in args.schedules:
            r = run_once(sid, sched, args.run_time)
            rows[(sid, sched)] = r
            func_cov = f"{r['func_covered']}/{r['func_total']}"
            print(f"{sid:>6} | {sched:>8} | {func_cov:>14} | {r['func_pct']:>5.1f}% | "
                  f"{r['covered_total']:>10} | {r['paths']:>7} | {r['crashes']:>7} | {r['execs']:>9}")

    print("\nGoal check (>=50% target-function line coverage):")
    for sid in args.samples:
        best = max((rows[(sid, s)]["func_pct"] for s in args.schedules), default=0.0)
        status = "PASS" if best >= 50.0 else "FAIL"
        print(f"  sample {sid}: best {best:5.1f}%  -> {status}")


if __name__ == "__main__":
    main()
