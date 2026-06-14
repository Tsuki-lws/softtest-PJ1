# 任务 B 完成说明：变异器模块

## 交付内容

完成 `simple_fuzzer/utils/mutator.py`，保持现有接口：

```python
Mutator().mutate(inp) -> str
```

实现了 9 种输入变异策略：

1. 随机字符插入
2. 随机字符删除
3. 连续 1、2、4 bit 翻转
4. 连续 1、2、4 字节算术加减
5. interesting values 边界值替换
6. havoc 随机片段插入
7. havoc 随机片段替换
8. 相邻字节块交换
9. 面向四个 sample 的字典 token 插入

## 稳定性处理

- 所有策略都支持空串和长度为 1 的短串。
- 删除和交换在输入过短时自动退化为插入操作。
- 字节与字符串使用 `latin-1` 一一映射，避免 UTF-8 解码丢弃变异字节。
- `Mutator.mutate()` 避免返回空串或完全未变化的输入。
- 对非字符串输入统一转换为字符串，返回值始终为 `str`。

## 验证

- `python -m compileall utils/mutator.py` 通过。
- 35,000 次组合随机变异压力测试通过。
- 每种变异器针对空串、短串、数值、格式化字符串和 HTML 输入的独立压力测试通过。
- 使用基础 `GreyBoxFuzzer` 对 4 个 sample 的短时集成运行通过。

完整 `main.py` 是否可运行仍取决于任务 C 的路径调度实现，任务 B 本身不依赖该实现。
