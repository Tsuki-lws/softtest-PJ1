"""Extract concrete crash inputs and stack-trace fingerprints from a fuzzer
run, then print a human-readable summary.

Run from the ``simple_fuzzer/`` directory::

    python tools/extract_crashes.py --sample 1 --run-time 30 --schedule path
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fuzzer.path_grey_box_fuzzer import PathGreyBoxFuzzer  # noqa: E402
from runner.function_coverage_runner import FunctionCoverageRunner  # noqa: E402
from samples.samples import sample1, sample2, sample3, sample4  # noqa: E402
from utils.object_utils import load_object  # noqa: E402
from main import build_schedule  # noqa: E402

SAMPLES = {
    1: (sample1, "corpus/corpus_1"),
    2: (sample2, "corpus/corpus_2"),
    3: (sample3, "corpus/corpus_3"),
    4: (sample4, "corpus/corpus_4"),
}


def replay_one(target, inp: str) -> str:
    """Replay an input against the target and return a one-line exception summary."""
    try:
        target(inp)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return "(no exception)"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample", type=int, default=1, choices=(1, 2, 3, 4))
    p.add_argument("--run-time", type=int, default=30)
    p.add_argument("--schedule", default="path")
    p.add_argument("--max-per-fp", type=int, default=1,
                   help="how many example inputs to show per unique fingerprint")
    return p.parse_args()


def main():
    args = parse_args()
    func, corpus = SAMPLES[args.sample]
    runner = FunctionCoverageRunner(func)
    seeds = load_object(corpus)
    fuzzer = PathGreyBoxFuzzer(seeds=seeds, schedule=build_schedule(args.schedule),
                               is_print=False,
                               persist_dir=f"_eval/crashes-persist/sample{args.sample}-{args.schedule}")
    fuzzer.runs(runner, run_time=args.run_time)

    by_fp: dict[str, list[str]] = defaultdict(list)
    for inp, fp in fuzzer.crash_map.items():
        by_fp[fp].append(inp)

    print(f"Sample {args.sample} | schedule {args.schedule} | "
          f"run {args.run_time}s | unique crashes: {len(by_fp)} | "
          f"total crash inputs: {len(fuzzer.crash_map)}")
    print("=" * 78)

    for i, (fp, inputs) in enumerate(by_fp.items(), 1):
        print(f"\n[Crash {i}/{len(by_fp)}]  fingerprint = {fp}")
        for inp in inputs[: args.max_per_fp]:
            disp = inp if len(inp) <= 60 else inp[:57] + "..."
            disp = repr(disp)
            print(f"  input  : {disp}")
            print(f"  message: {replay_one(func, inp)}")


if __name__ == "__main__":
    main()
