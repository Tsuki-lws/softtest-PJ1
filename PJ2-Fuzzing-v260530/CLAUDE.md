# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A course-lab grey-box fuzzing framework (Python 3.14, stdlib-only). The fuzzer takes Python functions as targets and uses corpus seeds, input mutation, coverage feedback, and power schedules to find crashes.

## Running

All commands run from `simple_fuzzer/`:

```bash
# Recommended: use uv (no pyproject.toml — just the .python-version pinning 3.14)
uv run main.py --sample 4 --run-time 300

# Switch target sample (1–4), adjust duration
uv run main.py --sample 1 --run-time 60

# Suppress the live stats table
uv run main.py --sample 2 --run-time 120 --quiet
```

Results are serialized (pickle) to `_result/Sample-{N}.pkl`.

## Architecture

```
simple_fuzzer/
├── main.py              # CLI entry point: picks sample, loads corpus, runs fuzzer, persists Result
├── fuzzer/
│   ├── fuzzer.py                # Base class: fuzz → run → runs loop with time budget
│   ├── grey_box_fuzzer.py       # Adds seed population, mutation stacking, coverage tracking, crash map
│   └── path_grey_box_fuzzer.py  # Extends GreyBoxFuzzer with edge-frequency path tracking
├── runner/
│   ├── runner.py                     # Base runner (PASS/FAIL/UNRESOLVED outcome)
│   └── function_coverage_runner.py   # Wraps target function, uses sys.settrace to collect coverage
├── schedule/
│   ├── power_schedule.py            # Base schedule: uniform energy, weighted random choice, MAX_SEEDS cap
│   ├── path_power_schedule.py       # Path-frequency energy assignment (rarer path -> higher energy)
│   ├── size_power_schedule.py       # Size-based: shorter input -> higher energy
│   ├── coverage_power_schedule.py   # Coverage-size based: larger per-run coverage -> higher energy
│   ├── rare_line_power_schedule.py  # Rare-line based: hitting rarely-touched lines -> higher energy
│   └── hybrid_power_schedule.py     # Hybrid: rarity x coverage x length x rare-line bonus
├── samples/samples.py           # 4 target functions (numeric, string-format, branch-nesting, HTML)
├── corpus/                      # Pickle files containing List[str] seed inputs per sample
└── utils/
    ├── coverage.py       # Coverage context manager (sys.settrace); Location = (func_name, lineno)
    ├── seed.py           # Seed dataclass: data, coverage set, energy
    ├── mutator.py        # 9 mutation operators (insert/delete/bitflip/arithmetic/interesting/havoc/swap/dict-token)
    └── object_utils.py   # pickle dump/load/md5 helpers
```

Key data flow: `main.py` → `PathGreyBoxFuzzer.runs()` → per iteration: `schedule.choose(population)` → `mutator.mutate()` (stacked) → `FunctionCoverageRunner.run(input)` → coverage diff → update population/crash_map.

## Status

All four lab tasks are complete. Quick map:

- **Mutator** (`utils/mutator.py`): 9 operators (insert/delete/bitflip/arithmetic/interesting/2x havoc/block swap/dict token) with `latin-1` 1:1 byte mapping and a 3-retry guard against returning empty / identical outputs.
- **Path-frequency scheduling** (`schedule/path_power_schedule.py` + `fuzzer/path_grey_box_fuzzer.py`): edge-frequency path key (`Counter` over `(src, dst)` edges, capped at 8), `energy = 1 / freq`.
- **Extra schedulers**: `size`, `coverage`, `rare` (each maps to one reference direction from the spec) plus a `hybrid` strategy with cached base factors.
- **Persistence**: `GreyBoxFuzzer._maybe_persist` snapshots population / crash_map / covered_line every 30 s and evicts the lowest-energy seeds when the population exceeds 500.

Switch the schedule with `--schedule {path,size,coverage,rare,hybrid}` (default `path`). Use `eval_schedules.py` for the 5-way comparison and `tools/bench_growth.py` for 1 Hz time-series sampling.

## Conventions

- Coverage is tracked as `Set[Location]` where `Location = Tuple[str, int]` (function name, line number).
- Corpus files are pickle-serialized `List[str]`.
- Mutation functions are standalone functions registered in `Mutator.mutators` list; adding one means defining the function and appending it.
- New schedulers subclass `PowerSchedule` and override `assign_energy`.
- `object_utils.dump_object` / `load_object` handle persistence (creates directories automatically).
