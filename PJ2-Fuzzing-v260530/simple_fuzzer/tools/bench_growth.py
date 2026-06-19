"""Benchmark coverage / path growth over time for each schedule.

Runs the fuzzer for a fixed time on a chosen sample, samples
``len(covered_line)``, ``total_execs`` and ``len(unique_paths)`` once per
second from a separate thread, and writes one CSV per (sample, schedule)
combination into ``_eval/growth/``.

Run from the ``simple_fuzzer/`` directory::

    python tools/bench_growth.py --sample 4 --run-time 60 \
        --schedules path size coverage rare hybrid
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import threading
import time

# Make `simple_fuzzer/` importable regardless of CWD.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fuzzer.path_grey_box_fuzzer import PathGreyBoxFuzzer  # noqa: E402
from runner.function_coverage_runner import FunctionCoverageRunner  # noqa: E402
from samples.samples import sample1, sample2, sample3, sample4  # noqa: E402
from utils.object_utils import load_object  # noqa: E402
from main import build_schedule, SCHEDULES  # noqa: E402

SAMPLES = {
    1: (sample1, "corpus/corpus_1"),
    2: (sample2, "corpus/corpus_2"),
    3: (sample3, "corpus/corpus_3"),
    4: (sample4, "corpus/corpus_4"),
}


def run_with_sampling(sample_id: int, schedule_name: str, run_time: int,
                      out_dir: str, interval: float = 1.0):
    func, corpus = SAMPLES[sample_id]
    runner = FunctionCoverageRunner(func)
    seeds = load_object(corpus)
    persist_dir = os.path.join("_eval", "growth-persist", f"s{sample_id}-{schedule_name}")
    fuzzer = PathGreyBoxFuzzer(seeds=seeds, schedule=build_schedule(schedule_name),
                               is_print=False, persist_dir=persist_dir)

    samples = []
    stop = threading.Event()

    def sampler():
        start = fuzzer.start_time
        while not stop.is_set():
            t = time.time() - start
            samples.append((
                round(t, 3),
                len(fuzzer.covered_line),
                fuzzer.total_execs,
                len(fuzzer.unique_paths),
                len(set(fuzzer.crash_map.values())),
            ))
            stop.wait(interval)

    th = threading.Thread(target=sampler, daemon=True)
    th.start()
    fuzzer.runs(runner, run_time=run_time)
    stop.set()
    th.join(timeout=2)

    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"sample{sample_id}-{schedule_name}.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t_seconds", "covered_lines", "total_execs",
                         "unique_paths", "uniq_crashes"])
        writer.writerows(samples)

    final = samples[-1] if samples else (0, 0, 0, 0, 0)
    print(f"  sample {sample_id} | {schedule_name:>8} -> "
          f"covered={final[1]:>4} execs={final[2]:>7} "
          f"paths={final[3]:>6} crashes={final[4]} -> {csv_path}")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample", type=int, default=4, choices=(1, 2, 3, 4))
    p.add_argument("--run-time", type=int, default=60)
    p.add_argument("--schedules", nargs="+", default=list(SCHEDULES))
    p.add_argument("--out-dir", default="_eval/growth")
    p.add_argument("--interval", type=float, default=1.0)
    return p.parse_args()


def main():
    args = parse_args()
    print(f"Benchmark: sample={args.sample}  run-time={args.run_time}s  "
          f"schedules={args.schedules}")
    for sched in args.schedules:
        run_with_sampling(args.sample, sched, args.run_time,
                          args.out_dir, args.interval)


if __name__ == "__main__":
    main()
