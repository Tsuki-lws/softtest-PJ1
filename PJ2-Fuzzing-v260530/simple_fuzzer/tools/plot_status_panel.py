"""Plot a 2x2 status panel for a single (sample, schedule) run.

Visualizes the four key fields shown in PathGreyBoxFuzzer's live table
(Covered Lines, Total Execs, Total Paths, Uniq Crashes) as time series.

Run from the ``simple_fuzzer/`` directory::

    python tools/plot_status_panel.py --sample 4 --schedule size
"""

from __future__ import annotations

import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_csv(path: str):
    with open(path, "r", newline="") as f:
        rows = list(csv.DictReader(f))
    t = [float(r["t_seconds"]) for r in rows]
    covered = [int(r["covered_lines"]) for r in rows]
    execs = [int(r["total_execs"]) for r in rows]
    paths = [int(r["unique_paths"]) for r in rows]
    crashes = [int(r["uniq_crashes"]) for r in rows]
    return t, covered, execs, paths, crashes


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample", type=int, default=4)
    p.add_argument("--schedule", default="size")
    p.add_argument("--in-dir", default="_eval/growth")
    p.add_argument("--out-dir", default="../docs/figures")
    return p.parse_args()


def main():
    args = parse_args()
    csv_path = os.path.join(args.in_dir, f"sample{args.sample}-{args.schedule}.csv")
    t, covered, execs, paths, crashes = load_csv(csv_path)

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"sample{args.sample}_{args.schedule}_status_panel.png")

    fig, axes = plt.subplots(2, 2, figsize=(10, 6), dpi=140)
    fig.suptitle(f"Sample {args.sample} live status (schedule={args.schedule})",
                 fontsize=12)

    panels = [
        (axes[0, 0], covered, "Covered Lines",  "#1f77b4"),
        (axes[0, 1], execs,   "Total Execs",    "#ff7f0e"),
        (axes[1, 0], paths,   "Total Paths",    "#2ca02c"),
        (axes[1, 1], crashes, "Uniq Crashes",   "#d62728"),
    ]
    for ax, y, label, color in panels:
        ax.plot(t, y, color=color, linewidth=1.7)
        ax.fill_between(t, 0, y, color=color, alpha=0.12)
        ax.set_xlabel("time (s)")
        ax.set_ylabel(label)
        ax.set_title(label)
        ax.grid(True, alpha=0.3)
        if y:
            ax.annotate(f"final = {y[-1]}", xy=(t[-1], y[-1]),
                        xytext=(-8, -14), textcoords="offset points",
                        ha="right", va="top", fontsize=9,
                        bbox=dict(boxstyle="round,pad=0.25",
                                  fc="white", ec=color, alpha=0.9))

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path)
    plt.close(fig)
    print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
