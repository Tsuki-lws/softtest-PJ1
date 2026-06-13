# 任务 A 完成报告：基础框架与持久化

**负责人：** A  
**完成日期：** 2026 年 6 月 14 日

---

## 一、交付目标回顾

| 要求 | 状态 |
|------|------|
| 项目能正常启动运行 | ✅ 已完成 |
| 4 个 sample 均可通过命令行运行 | ✅ 已完成 |
| 运行结果保存到文件系统 | ✅ 已完成 |
| seed/crash/覆盖率中间结果持久化 | ✅ 已完成 |
| 长时间运行内存可控 | ✅ 已完成 |

---

## 二、运行方式

```bash
cd simple_fuzzer

# 基本运行（sample 1-4 可选，run-time 单位为秒）
python3 main.py --sample 1 --run-time 60

# 静默模式（不输出实时状态表）
python3 main.py --sample 4 --run-time 300 --quiet

# 自定义输出目录
python3 main.py --sample 2 --run-time 120 --output-dir my_output
```

运行后产出：
- `{output-dir}/Sample-{N}.pkl` — 最终结果（覆盖率、crash 集合、时间）
- `{output-dir}/persist-sample{N}/` — 中间持久化快照

---

## 三、具体改动

### 3.1 补全 `path_power_schedule.py`（让框架可运行）

原始代码为 TODO 空实现，`assign_energy` 不设置能量导致断言失败。

实现内容：
- 维护 `path_frequency` 字典，记录每条路径被执行的次数
- `assign_energy` 根据路径频率倒数指数分配能量：`energy = 1 / (freq^log2(freq+1) + 1)`
- 提供 `update_path_frequency(path)` 接口供 fuzzer 调用

> 注：此为最小可用实现，C 同学后续可直接替换算法逻辑。

### 3.2 补全 `path_grey_box_fuzzer.py`（让框架可运行）

原始代码 `__init__` 和 `run` 均为 TODO。

实现内容：
- `__init__`：初始化 `unique_paths` 集合、`last_path_time` 时间戳
- `run`：每次执行后提取覆盖路径，判断是否为新路径，调用 `schedule.update_path_frequency` 上报
- `print_stats`：填充实际的路径数和时间数据（原先为空字符串）
- `is_print` 控制是否输出状态表（原先无论如何都打印表头）

### 3.3 `grey_box_fuzzer.py` 新增持久化机制

核心改动：

```python
# 配置常量
PERSIST_INTERVAL = 30          # 每 30 秒持久化一次
MAX_POPULATION_MEMORY = 500    # 内存中最大种子数
```

新增 `_maybe_persist()` 方法，在每次 `run()` 结束时检查是否到达持久化间隔：
- 序列化 `population` → `persist_dir/population.pkl`
- 序列化 `crash_map` → `persist_dir/crash_map.pkl`
- 序列化 `covered_line` → `persist_dir/covered_line.pkl`
- 当 `population` 超过 500 条时，按能量排序淘汰低能量种子

`persist_dir` 通过构造函数参数传入，默认为 `_persist`。

### 3.4 `main.py` 对接持久化

- 将 `persist_dir` 设为 `{output_dir}/persist-sample{N}`，跟随 `--output-dir` 参数
- 不影响其他同学的接口使用

### 3.5 `.gitignore` 更新

在仓库根目录 `.gitignore` 中添加：
```
PJ2-Fuzzing-v260530/simple_fuzzer/_result/
PJ2-Fuzzing-v260530/simple_fuzzer/_persist/
```

---

## 四、验证结果

4 个样例均通过 35 秒运行测试：

| Sample | 覆盖行数 | 唯一 Crash 数 | 持久化文件生成 |
|--------|----------|--------------|---------------|
| 1 | 10 | 6 | ✅ |
| 2 | 15 | 4 | ✅ |
| 3 | 9 | 7 | ✅ |
| 4 | 400+ | 1 | ✅ |

---

## 五、给其他同学的接口说明

- **C 同学**：`PathPowerSchedule` 和 `PathGreyBoxFuzzer` 已有基础实现，可直接修改 `assign_energy` 算法和路径统计逻辑，不需要改持久化代码
- **D 同学**：新 scheduler 只需继承 `PowerSchedule` 并重写 `assign_energy`，持久化和内存控制由 `GreyBoxFuzzer` 基类自动处理
- **E 同学**：运行命令见上方"运行方式"，结果文件在 `_result/` 下，可用 `load_object` 读取
