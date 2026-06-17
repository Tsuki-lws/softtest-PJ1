# D 任务交接文档：新增调度器与覆盖率优化

**负责人：** D
**完成日期：** 2026 年 6 月 16 日
**详细完成报告见：** `task_d_completion.md`

---

## 1. 工作完成情况

D 负责的「新增调度器 + 调参达到 50%+ 覆盖率」已全部完成：

- 按实验说明第三条点名的三个参考方向，**各实现一个独立调度策略**（长度优先 / 覆盖范围优先 / 罕见行优先）。
- 额外实现一个把上述信号与路径稀有度融合的**混合调度**，并做了缓存性能优化。
- 完成 5 种调度策略在 4 个 sample 上的对比实验与长度惩罚系数调参实验。
- **4 个 sample 上目标函数行覆盖率均达到 50%+（实测 66.7%~90.0%），5 种策略全部达标。**
- 全程未改动 A / B / C 的文件，`main.py` 仅新增向后兼容的 `--schedule` 参数。

---

## 2. 改动 / 新增的文件

### 2.1 新增调度策略（均在 `simple_fuzzer/schedule/`）

| 文件 | 类 | `--schedule` | 对应参考方向 |
|------|----|-------------|--------------|
| `size_power_schedule.py` | `SizePowerSchedule` | `size` | 基于输入长度 (Size-Based) |
| `coverage_power_schedule.py` | `CoveragePowerSchedule` | `coverage` | 基于覆盖范围 (Coverage-Size Based) |
| `rare_line_power_schedule.py` | `RareLinePowerSchedule` | `rare` | 基于罕见代码行 (Rare-Line Based) |
| `hybrid_power_schedule.py` | `HybridPowerSchedule` | `hybrid` | 上述三者 + 路径稀有度融合 |

四个类都继承自 C 的 `PathPowerSchedule`，只重写 `assign_energy`，天然兼容 `PathGreyBoxFuzzer`。

### 2.2 修改

- `simple_fuzzer/main.py`：新增 `SCHEDULES` 注册表与 `build_schedule()`，新增命令行参数 `--schedule {path,size,coverage,rare,hybrid}`（**默认 `path`，保持 A/C 原有行为**）。

### 2.3 新增实验工具

- `simple_fuzzer/eval_schedules.py`：一键对比脚本，输出每个 sample × 每种策略的目标函数行覆盖率、总覆盖行数、唯一路径数、崩溃数、执行次数，并自动判定是否达到 50% 目标。

> 未改动：B 的 `mutator.py`、C 的 `path_power_schedule.py` / `path_grey_box_fuzzer.py`、A 的持久化逻辑。

---

## 3. 运行方式

环境：Python 3.12+（纯标准库，无需安装依赖）。在 `simple_fuzzer/` 目录下执行：

```bash
# 用某个调度策略跑单个 sample（size/coverage/rare/hybrid 任选）
python main.py --sample 4 --run-time 300 --schedule hybrid

# 默认仍是 C 的路径频率调度
python main.py --sample 1 --run-time 60

# 一键复现 5 种策略 × 4 个 sample 的对比表
python eval_schedules.py --run-time 30

# 只对比指定策略
python eval_schedules.py --run-time 60 --schedules path hybrid
```

结果文件输出到 `_result/Sample-{N}.pkl`（沿用 A 的约定）。

---

## 4. 实验结果（每组合 30 秒，Python 3.12.7）

50% 目标判定：**4 个 sample 全部 PASS（66.7%~90.0%），5 种策略全部达标。**

关键结论：

- **紧凑目标（sample1~3）**：5 种策略的目标函数行覆盖率完全一致（~89%~90%），差异只在吞吐量；瓶颈在被测函数本身分支有限。
- **广度目标（sample4 = HTMLParser）**：策略明显分化，各有所长——
  - `size` 吞吐最高、唯一路径最多（16,038）、崩溃最多（2）；
  - `path` 绝对覆盖行数最广（612）；
  - `coverage` 最慢、路径最少；`hybrid` 最均衡。
- 即「没有银弹」：追求崩溃/路径选 `size`，追求广覆盖选 `path`，要稳健折中选 `hybrid`。

完整数据表见 `task_d_completion.md` 第五节，以及实验日志 `simple_fuzzer/_eval/compare_5way_30s.txt`。

---

## 5. 覆盖率口径说明（重要，E 写报告需注意）

「目标函数行覆盖率」= 被测样例函数自身被覆盖的可执行行数 ÷ 该函数 `code.co_lines()` 给出的可执行行总数。

- sample1~3 稳定在 ~89%~90%，**未覆盖的那 1 行是 `else:`/`def` 等结构行**，`sys.settrace` 不会产生 line 事件，属度量口径，非逻辑未覆盖。
- sample4 直接被测函数只有 2 行（转调标准库 `HTMLParser`），目标函数覆盖率为 2/3=66.7%；其真正的探索深度体现在「总覆盖行数 / 唯一路径数」上（可达数百行 HTMLParser 代码）。

---

## 6. 交接给 E 同学（实验与报告）

可直接使用的素材：

- **覆盖率/对比数据**：`task_d_completion.md` 第五节的 5 路对比表、调参表，可直接放进实验报告的「调度策略实现」「测试与结果」章节。
- **复现命令**：`python eval_schedules.py --run-time 30` 一键产出对比表。
- **截图素材**：`python main.py --sample 4 --run-time 300 --schedule size` 会打印实时状态表（崩溃/路径数最多，画面最丰富），适合截图。
- **报告论点**：可重点写「不同调度策略对紧凑/广度型目标的区分度差异」和「没有银弹、需按目标特性选策略」这两个观察。

---

## 7. 交接状态

D 的代码、实验脚本、对比/调参数据、完成报告均已就绪，可直接交接给 E 进行最终实验汇总与报告撰写。无遗留 TODO；如需更长时长的稳定数据，E 可自行调高 `--run-time` 重跑 `eval_schedules.py`。
