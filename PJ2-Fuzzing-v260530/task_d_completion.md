# 任务 D 完成报告：新增调度器与覆盖率优化

**负责人：** D
**完成日期：** 2026 年 6 月 16 日

---

## 一、交付目标回顾

| 要求 | 状态 |
|------|------|
| 新增至少一种不同类型的 scheduler | 已完成（共新增 4 种） |
| 覆盖实验说明点名的三个参考方向 | 已完成（Size-Based / Coverage-Size Based / Rare-Line Based 各做一个独立策略） |
| scheduler 放入 `schedule` 包 | 已完成 |
| 与 B、C 一起调参 | 已完成（长度惩罚系数调参实验 + 五路对比） |
| 至少一个 scheduler 在 4 个 sample 上覆盖率达到 50%+ | 已完成（五种 scheduler 全部达标，实测 66.7%~90.0%） |
| 不破坏 A 的入口与持久化、C 的路径频率主线 | 已完成（向后兼容） |

---

## 二、新增的调度策略

C 同学的 `PathPowerSchedule` 只用「路径频率」一个信号决定 seed 能量。本任务按实验说明第三条点名的三个参考方向，**各实现一个独立、单一职责的调度策略**，再额外提供一个把它们融合起来的「混合调度」，共 4 个新策略，全部放入 `schedule` 包，并都继承自 C 的 `PathPowerSchedule`，因此天然兼容 `PathGreyBoxFuzzer`（仍会被调用 `update_path_frequency`），只重写 `assign_energy`。

| 策略 | 文件 | `--schedule` | 对应参考方向 | 能量公式 |
|------|------|-------------|--------------|----------|
| 长度优先 `SizePowerSchedule` | `schedule/size_power_schedule.py` | `size` | 基于输入长度 (Size-Based) | `energy = 1 / (len(data)+1) ** len_exp`，输入越短能量越高 |
| 覆盖范围优先 `CoveragePowerSchedule` | `schedule/coverage_power_schedule.py` | `coverage` | 基于覆盖范围 (Coverage-Size Based) | `energy = (len(coverage)+1) ** cov_exp`，单次覆盖行越多能量越高 |
| 罕见行优先 `RareLinePowerSchedule` | `schedule/rare_line_power_schedule.py` | `rare` | 基于罕见代码行 (Rare-Line Based) | 统计每行全局执行次数，`energy = Σ 1/line_freq(line)`，命中罕见行越多能量越高 |
| 混合调度 `HybridPowerSchedule` | `schedule/hybrid_power_schedule.py` | `hybrid` | 上述三者 + 路径稀有度的融合 | 见 2.2 |

其中 `RareLinePowerSchedule` 的「每行执行频率」直接从 C 已经传给 `update_path_frequency` 的 edge path key 里解析得到（每条 edge 是 `(src, dst, count)`，进入某节点 `count` 次即该行执行 `count` 次），因此**无需改动 C 的 fuzzer**。

`SizePowerSchedule` 与 `CoveragePowerSchedule` 不需要路径信息，把 `update_path_frequency` 重写为空操作，避免长跑时无谓累积路径字典占内存。

### 2.1 混合调度的设计动机

单一信号各有盲区：长度优先可能困在短而无效的输入，覆盖范围优先可能反复挑同一个大种子，罕见行优先可能忽视执行效率。混合调度把它们融合，取长补短。文件 `simple_fuzzer/schedule/hybrid_power_schedule.py`。

### 2.2 混合调度能量公式

对种群中的每个 seed：

```
energy = rarity * cov_size * length * rare_line
```

其中：

| 信号 | 含义 | 公式 | 权重参数 |
|------|------|------|----------|
| 路径稀有度 rarity | 走过的路径越少越优先（继承 C 的思想） | `1 / freq ** rarity_exp` | `rarity_exp`（默认 1.0） |
| 覆盖范围 cov_size | 单次执行覆盖行越多，携带的前置状态越多 | `(len(coverage)+1) ** cov_exp` | `cov_exp`（默认 1.0） |
| 长度惩罚 length | 输入越短，执行越快、越易命中核心逻辑 | `1 / (len(data)+1) ** len_exp` | `len_exp`（默认 0.5） |
| 罕见行加成 rare_line | seed 命中了种群中很少有人覆盖的代码行则加分 | `1 + rare_line_weight * Σ(1/line_freq)` | `rare_line_weight`（默认 1.0） |

四个权重全部通过构造函数暴露，方便针对不同 sample 调参；把某个指数置 0 即可退化为单一启发式（例如 `cov_exp=0, len_exp=0` 时行为等价于纯路径频率调度），方便做消融对比。

### 2.3 性能优化（关键）

罕见行加成与覆盖范围、长度项只在**种群发生变化**时才会改变，而路径稀有度每次执行都会变。因此：

- 把 `cov_size * length * rare_line` 缓存为每个 seed 的 `_base_factor`，**仅在种群增长或被裁剪时重算**；
- 路径稀有度项每次 `choose()` 都刷新（只是一次字典查询）。

这样 `choose()` 在热路径上接近 O(种群规模)，避免了对「种群 × 每个种子覆盖行」的双重循环。该优化对覆盖集巨大的 sample4（HTMLParser）至关重要：优化前 sample4 在 60 秒内只能执行约 1 万次，优化后吞吐量提升数倍。

---

## 三、改动文件

- **新增** `simple_fuzzer/schedule/size_power_schedule.py`：Size-Based 长度优先调度。
- **新增** `simple_fuzzer/schedule/coverage_power_schedule.py`：Coverage-Size Based 覆盖范围优先调度。
- **新增** `simple_fuzzer/schedule/rare_line_power_schedule.py`：Rare-Line Based 罕见行优先调度（全局行频率）。
- **新增** `simple_fuzzer/schedule/hybrid_power_schedule.py`：混合调度，含四信号能量公式与缓存优化。

- **修改** `simple_fuzzer/main.py`
  - 新增 `SCHEDULES` 注册表与 `build_schedule(name)` 工厂函数。
  - 新增命令行参数 `--schedule {path,size,coverage,rare,hybrid}`，**默认 `path` 保持 A/C 原有行为**。

- **新增** `simple_fuzzer/eval_schedules.py`
  - 调参/对比实验脚本：对每个 sample、每种 scheduler 跑固定时长，输出目标函数行覆盖率、总覆盖行数、唯一路径数、崩溃数、执行次数，并自动判定是否达到 50% 目标。

> 未改动 B 的 `mutator.py`、C 的 `path_power_schedule.py` / `path_grey_box_fuzzer.py` 以及 A 的持久化逻辑。

---

## 四、运行方式

```bash
cd simple_fuzzer

# 用本任务新增的某个调度策略跑单个 sample（size/coverage/rare/hybrid 任选）
python main.py --sample 4 --run-time 300 --schedule hybrid

# 仍可使用 C 的路径频率调度器（默认）
python main.py --sample 1 --run-time 60

# 一键对比全部 5 种调度策略在 4 个 sample 上的覆盖率
python eval_schedules.py --run-time 30

# 也可只对比指定策略
python eval_schedules.py --run-time 60 --schedules path hybrid
```

结果文件仍按 A 的约定输出到 `_result/Sample-{N}.pkl`。

---

## 五、覆盖率验证结果

### 5.1 覆盖率口径说明

「目标函数行覆盖率」= 直接被测样例函数（`sample1`~`sample4`）自身被覆盖的可执行行数 ÷ 该函数 `code.co_lines()` 给出的可执行行总数。这是衡量 50% 目标的主指标，因为它针对的是项目中我们控制的被测代码（SUT）。

各 sample 始终有 1 行无法被 `sys.settrace` 报告（`else:` / `def` 等结构行不产生 line 事件），因此满覆盖体现为约 89%~90%，这属于度量口径而非未覆盖逻辑。

### 5.2 五路调度策略实测对比（每个组合运行 30 秒，Python 3.12.7）

| Sample | Schedule | 目标函数行覆盖 | 覆盖率 | 总覆盖行数 | 唯一路径 | 唯一崩溃 | 执行次数 |
|--------|----------|----------------|--------|------------|----------|----------|----------|
| 1 | path | 8/9 | 88.9% | 8 | 5 | 6 | 46,077 |
| 1 | size | 8/9 | 88.9% | 8 | 5 | 6 | 46,512 |
| 1 | coverage | 8/9 | 88.9% | 8 | 5 | 6 | 50,205 |
| 1 | rare | 8/9 | 88.9% | 8 | 5 | 6 | 48,368 |
| 1 | hybrid | 8/9 | 88.9% | 8 | 5 | 6 | 45,938 |
| 2 | path | 8/9 | 88.9% | 13 | 5 | 4 | 241,325 |
| 2 | size | 8/9 | 88.9% | 13 | 5 | 4 | 206,069 |
| 2 | coverage | 8/9 | 88.9% | 13 | 5 | 4 | 265,130 |
| 2 | rare | 8/9 | 88.9% | 13 | 5 | 4 | 249,161 |
| 2 | hybrid | 8/9 | 88.9% | 13 | 5 | 4 | 242,669 |
| 3 | path | 9/10 | 90.0% | 9 | 9 | 8 | 425,331 |
| 3 | size | 9/10 | 90.0% | 9 | 9 | 8 | 594,939 |
| 3 | coverage | 9/10 | 90.0% | 9 | 9 | 8 | 394,732 |
| 3 | rare | 9/10 | 90.0% | 9 | 9 | 8 | 320,771 |
| 3 | hybrid | 9/10 | 90.0% | 9 | 9 | 8 | 349,716 |
| 4 | path | 2/3 | 66.7% | **612** | 7,804 | 1 | 22,020 |
| 4 | size | 2/3 | 66.7% | 240 | **16,038** | **2** | **42,654** |
| 4 | coverage | 2/3 | 66.7% | 216 | 1,465 | 0 | 3,088 |
| 4 | rare | 2/3 | 66.7% | 216 | 2,264 | 0 | 5,115 |
| 4 | hybrid | 2/3 | 66.7% | 218 | 3,495 | 0 | 6,670 |

**50% 目标判定：4 个 sample 全部 PASS（最低 66.7%，最高 90.0%），五种 scheduler 全部达标。**

结论：

- **紧凑型目标（sample1~3）**：5 种策略的目标函数行覆盖率完全一致，唯一崩溃数也相同；差异只在执行吞吐量（如 sample3 上 `size` 因偏好短输入吞吐最高）。说明对小目标而言，调度策略对最终覆盖几乎没有区分度，瓶颈在被测函数本身分支有限。
- **广度型目标（sample4 = HTMLParser）**：策略之间出现明显分化，各有所长：
  - `size`（长度优先）偏好短输入、执行最快，**唯一路径最多（16,038）、崩溃最多（2）**；
  - `path`（路径频率）追求路径多样性，**绝对覆盖行数最广（612）**；
  - `coverage`（覆盖范围优先）偏爱长的大覆盖种子，执行最慢、路径最少；
  - `hybrid`（混合）居中、较均衡。
- 由此可见：**没有一种策略在所有指标上通吃**——追求"崩溃/路径数"应选 `size`，追求"广覆盖"应选 `path`，`hybrid` 提供折中的稳健表现。这正是本任务做多策略对比的价值。

### 5.3 调参实验：长度惩罚系数对 sample4 的影响

sample4 是「广度型」目标，深入 HTMLParser 需要更长、更丰富的 HTML 输入，因此长度惩罚对它影响最大。固定其他参数，仅调 `len_exp`，sample4 各跑 30 秒：

| len_exp | 总覆盖行数 | 唯一路径 | 唯一崩溃 | 执行次数 |
|---------|------------|----------|----------|----------|
| 0.0（关闭长度惩罚） | 610 | 10,396 | 1 | 35,212 |
| 0.2 | 214 | 1,295 | 0 | 2,954 |
| 0.5（默认） | 220 | 6,065 | 0 | 12,889 |

**调参结论：** 长度惩罚对 sample1~3 这类紧凑函数基本无害（仍稳定在 ~90%），但会压低 sample4 的总覆盖广度。对于 HTMLParser 这类广度型目标，将 `len_exp` 调到 0（关闭长度惩罚）能让总覆盖行数、唯一路径和崩溃数全面提升。因此推荐：

- 默认配置 `HybridPowerSchedule()`（`len_exp=0.5`）即可让 4 个 sample 全部满足 50%+ 目标；
- 若以「广度优先」探索 sample4，使用 `HybridPowerSchedule(len_exp=0.0)` 效果最佳。

---

## 六、给其他同学的接口说明

- **C 同学**：本任务 4 个新策略全部继承自你的 `PathPowerSchedule`。`hybrid`/`rare` 复用了路径信息（`hybrid` 用 `path_frequency`，`rare` 从你的 edge path key 里解析行频率），`size`/`coverage` 不用路径信息；均未改动你的文件，可通过 `--schedule` 自由切换对比。
- **B 同学**：未改动 `mutator.py`，所有调度策略只在「选哪个 seed」层面工作，与变异策略解耦。
- **A 同学**：未改动持久化与结果落盘逻辑，`main.py` 仅新增一个向后兼容的 `--schedule` 参数（默认 `path`，行为不变）。
- **E 同学（报告）**：第五节的五路对比表、调参表可直接用于实验报告的「调度策略实现」与「测试与结果」部分。推荐运行 `python eval_schedules.py --run-time 30` 一键复现对比表；运行 `python main.py --sample 4 --run-time 300 --schedule size` 截取实时状态表作为截图素材（sample4 上 `size` 崩溃/路径最多，画面最丰富）。

---

## 七、报告素材摘要

RoleD 在 C 的路径频率调度之外，按实验说明点名的三个参考方向各实现一个独立策略——长度优先 `SizePowerSchedule`、覆盖范围优先 `CoveragePowerSchedule`、罕见行优先 `RareLinePowerSchedule`，并额外提供把它们与路径稀有度融合的混合调度 `HybridPowerSchedule`（含缓存优化，保证大覆盖集目标下吞吐稳定）。所有权重均可调，便于按目标特性调参与消融。五路对比实测：4 个 sample 上目标函数行覆盖率 66.7%~90.0%，五种策略全部满足 50%+ 要求。结论是紧凑目标（sample1~3）上各策略覆盖率无区分度，瓶颈在被测函数本身；广度目标（sample4 = HTMLParser）上策略明显分化——长度优先崩溃与路径最多、路径频率绝对覆盖最广、混合调度最均衡，印证了"没有银弹、需按目标特性选择调度策略"这一核心观察。
