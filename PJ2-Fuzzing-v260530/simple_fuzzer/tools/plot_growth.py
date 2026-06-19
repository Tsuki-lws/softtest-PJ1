"""Plot coverage / path growth curves from CSVs produced by ``bench_growth.py``.

Outputs three PNG figures into ``docs/figures/``:

* ``sample4_coverage_growth.png`` - covered lines vs. time per schedule
* ``sample4_paths_growth.png``    - unique paths vs. time per schedule
* ``sample4_execs_growth.png``    - total executions vs. time per schedule

Run from the ``simple_fuzzer/`` directory::

    python tools/plot_growth.py --sample 4
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


SCHEDULE_ORDER = ["path", "size", "coverage", "rare", "hybrid"]
SCHEDULE_COLORS = {
    "path":     "#1f77b4",
    "size":     "#ff7f0e",
    "coverage": "#2ca02c",
    "rare":     "#d62728",
    "hybrid":   "#9467bd",
}


def load_csv(path: str):
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    t = [float(r["t_seconds"]) for r in rows]
    covered = [int(r["covered_lines"]) for r in rows]
    execs = [int(r["total_execs"]) for r in rows]
    paths = [int(r["unique_paths"]) for r in rows]
    return t, covered, execs, paths


def plot_metric(sample_id: int, in_dir: str, out_path: str,
                metric_index: int, ylabel: str, title: str,
                log_y: bool = False):
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=140)
    for sched in SCHEDULE_ORDER:
        csv_path = os.path.join(in_dir, f"sample{sample_id}-{sched}.csv")
        if not os.path.exists(csv_path):
            continue
        series = load_csv(csv_path)
        t = series[0]
        y = series[metric_index]
        ax.plot(t, y, label=sched, color=SCHEDULE_COLORS.get(sched), linewidth=1.6)

    ax.set_xlabel("time (s)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if log_y:
        ax.set_yscale("log")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", frameon=False, ncol=5, fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"  wrote {out_path}")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample", type=int, default=4)
    p.add_argument("--in-dir", default="_eval/growth")
    p.add_argument("--out-dir", default="../docs/figures")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    plot_metric(args.sample, args.in_dir,
                os.path.join(out_dir, f"sample{args.sample}_coverage_growth.png"),
                metric_index=1, ylabel="Covered Lines",
                title=f"Sample {args.sample}: Covered Lines over Time")
    plot_metric(args.sample, args.in_dir,
                os.path.join(out_dir, f"sample{args.sample}_paths_growth.png"),
                metric_index=3, ylabel="Unique Paths",
                title=f"Sample {args.sample}: Unique Paths over Time")
    plot_metric(args.sample, args.in_dir,
                os.path.join(out_dir, f"sample{args.sample}_execs_growth.png"),
                metric_index=2, ylabel="Total Executions",
                title=f"Sample {args.sample}: Total Executions over Time")


if __name__ == "__main__":
    main()
