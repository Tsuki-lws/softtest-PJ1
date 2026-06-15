# 任务 C 完成报告：路径频率调度

**负责人：** C  
**完成日期：** 2026 年 6 月 15 日

---

## 一、交付目标回顾

| 要求 | 状态 |
|------|------|
| 完成路径频率 scheduler | 已完成 |
| 完成对应 PathGreyBoxFuzzer | 已完成 |
| 能记录输入执行路径 | 已完成 |
| 能统计路径频率 | 已完成 |
| 低频路径 seed 获得更高优先级 | 已完成 |
| 为 E 同学提供验证数据和报告素材 | 已完成 |

---

## 二、核心实现说明

### 2.1 路径表示方式

原先最小可用版本使用 `coverage set` 作为路径标识，只能表示一次执行覆盖了哪些代码行，无法区分执行顺序和循环次数。

本任务将路径表示升级为 edge path：

- 从 `FunctionCoverageRunner.trace()` 获取一次执行的有序 trace。
- 在 trace 前后加入 `("<START>", 0)` 和 `("<END>", 0)` 哨兵节点。
- 将相邻节点转换为有向 edge，例如 `START -> line1 -> line2 -> END`。
- 统计每条 edge 在本次执行中出现的次数，次数上限为 `EDGE_COUNT_CAP = 8`，避免循环导致路径数量失控。
- 最终将 `(src, dst, capped_count)` 组成稳定可哈希的 `path_key`。

这样可以区分“覆盖行相同但执行顺序不同”的输入，也可以让循环执行次数对路径签名产生影响。

### 2.2 路径频率统计

`PathGreyBoxFuzzer.run()` 每次执行后会：

1. 从 runner 读取本次有序 trace。
2. 调用 `build_path_key(trace)` 生成 edge path key。
3. 将新路径加入 `unique_paths`，用于统计唯一路径数。
4. 调用 `PathPowerSchedule.update_path_frequency(path_key)` 更新路径出现次数。
5. 如果本次输入因为新覆盖被加入 population，则把 `path_key` 写入对应 `Seed`。

### 2.3 能量分配策略

`PathPowerSchedule.assign_energy()` 优先读取 `seed.path_key`，若遇到旧 seed 没有该字段，则回退到旧的 `tuple(sorted(seed.coverage))`。

能量公式为：

```python
seed.energy = 1.0 / max(freq, 1)
```

其中 `freq` 是该 seed 对应路径的历史出现次数。路径出现越少，energy 越高；`PowerSchedule.choose()` 会按归一化 energy 加权随机选择 seed，因此低频路径对应的 seed 更容易被继续变异。

---

## 三、改动文件

- `simple_fuzzer/runner/function_coverage_runner.py`
  - 新增 `_trace` 字段。
  - 新增 `trace()` 方法，返回一次执行的有序行级 trace。

- `simple_fuzzer/utils/seed.py`
  - 新增可选 `path_key` 字段。
  - 保持原有 `Seed(data, coverage)` 调用兼容。

- `simple_fuzzer/fuzzer/path_grey_box_fuzzer.py`
  - 新增 edge path 构造逻辑。
  - 维护 `unique_paths` 和 `last_path_time`。
  - 执行后更新 scheduler 的路径频率。
  - 新增 seed 时保存本次 `path_key`。

- `simple_fuzzer/schedule/path_power_schedule.py`
  - 维护 `path_frequency`。
  - 根据路径频率倒数分配 seed energy。
  - 兼容没有 `path_key` 的旧 seed。

---

## 四、验证结果

### 4.1 编译与逻辑验证

编译检查通过：

```bash
python3 -m compileall runner/function_coverage_runner.py utils/seed.py fuzzer/path_grey_box_fuzzer.py schedule/path_power_schedule.py
```

逻辑验证通过：

- 覆盖行集合相同但执行顺序不同的 trace，会生成不同的 edge path key。
- 包含循环的 trace，会将重复 edge 次数限制到 `EDGE_COUNT_CAP = 8`。

### 4.2 集成验证

验证环境：

- Python 3.14.5
- 每个 sample 运行 30 秒
- 输出目录：`simple_fuzzer/_result/`
- 覆盖统计不包含 coverage 工具自身的读取逻辑

| Sample | 运行时间 | 覆盖行数 | 唯一路径数 | 唯一 Crash 数 | 总执行次数 | 结果文件 | 是否通过 |
|--------|----------|----------|------------|---------------|------------|----------|----------|
| 1 | 30 s | 8 | 5 | 6 | 89340 | `_result/Sample-1.pkl` | 是 |
| 2 | 30 s | 13 | 5 | 4 | 619162 | `_result/Sample-2.pkl` | 是 |
| 3 | 30 s | 9 | 9 | 8 | 923290 | `_result/Sample-3.pkl` | 是 |
| 4 | 30 s | 654 | 11014 | 0 | 44859 | `_result/Sample-4.pkl` | 是 |

---

## 五、运行方式

基本运行方式与 A 同学整理的入口保持一致：

```bash
cd simple_fuzzer
python3 main.py --sample 1 --run-time 60 --quiet
python3 main.py --sample 2 --run-time 60 --quiet
python3 main.py --sample 3 --run-time 60 --quiet
python3 main.py --sample 4 --run-time 60 --quiet
```

如果需要统计 RoleC 的唯一路径数，可以在运行过程中读取 `PathGreyBoxFuzzer.unique_paths` 和 `PathPowerSchedule.path_frequency`。

---

## 六、给其他同学的接口说明

- **D 同学**：新增 scheduler 仍然只需要继承 `PowerSchedule` 并重写 `assign_energy()`。如果要复用 RoleC 的路径信息，可以读取 `Seed.path_key` 或 `PathPowerSchedule.path_frequency`。
- **E 同学**：报告中可以说明本任务将路径表示从 coverage set 升级为 edge path，低频路径通过更高 energy 提高后续变异概率。验证表中的覆盖行数、唯一路径数、crash 数和结果文件位置可直接用于实验结果部分。
- **A 同学**：本任务没有修改持久化机制，仍使用原有 `_result/` 和 `_result/persist-sample{N}/` 输出结构。

---

## 七、报告素材摘要

RoleC 实现了基于 edge path 的路径频率调度。相比只记录覆盖行集合，edge path 记录了相邻执行位置之间的跳转关系，并对重复 edge 次数进行 capped 统计，因此能够更细粒度地区分不同输入的执行行为。调度器维护每条路径的出现频率，并将 seed 的能量设置为路径频率的倒数，使低频路径对应的 seed 在加权随机选择中拥有更高概率，从而提高继续探索新路径的机会。
