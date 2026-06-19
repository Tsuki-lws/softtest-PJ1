# 崩溃样例集合（path 调度，每样例 20 秒）

> 复现命令：`uv run --python 3.14 python tools/extract_crashes.py --sample <N> --run-time 20 --schedule path`

## Sample 1（数值/递归型）

| # | 输入 | 异常类型 | 异常信息 |
|---|------|----------|----------|
| 1 | `'-C1Á'` | `ValueError` | could not convert string to float |
| 2 | `'1'` | `RecursionError` | maximum recursion depth exceeded |
| 3 | `'-5'` | `IndexError` | string index out of range |
| 4 | `'00.1244'` | `IndexError` | string index out of range |
| 5 | `'0.123E6548'` | `OverflowError` | cannot convert float infinity to integer |
| 6 | `'000'` | `ZeroDivisionError` | division by zero |

总计 6 个唯一崩溃指纹，共 32,304 次崩溃输入。

## Sample 2（字符串格式化型）

| # | 输入摘要 | 异常类型 | 异常信息 |
|---|----------|----------|----------|
| 1 | `"l{Inn';MvdFT...."` | `ValueError` | expected ':' after conversion specifier |
| 2 | `"l.ksb?@*+=%V..."` | `TypeError` | not enough arguments for format string |
| 3 | `"l\x00\x00fnnvnj..."` | `IndexError` | list index out of range |
| 4 | `"-10.0'er\x00\x00..."` | `ValueError` | expected a nonnegative input, got -10.0 |

总计 4 个唯一崩溃指纹，共 21,194 次崩溃输入。

## Sample 3（前缀分支型）

| # | 输入 | 异常类型 | 异常信息 |
|---|------|----------|----------|
| 1 | `'F'` | `IndexError` | string index out of range |
| 2 | `'FDUFdd'` | `ValueError` | substring not found |
| 3 | `'FDULg'` | `AssertionError` | （断言失败） |
| 4 | `'FD'` | `IndexError` | string index out of range |
| 5 | `'FDUd'` | `IndexError` | string index out of range |
| 6 | `'FDUPL'` | `ZeroDivisionError` | division by zero |
| 7 | `'FDUKFLAABz'` | `RuntimeError` | （触发被测函数显式抛错） |
| 8 | `'FDUFL'` | `IndexError` | string index out of range |

总计 8 个唯一崩溃指纹，共 26,012 次崩溃输入。可看到 fuzzer 在路径调度引导下逐步发现 `F` → `FD` → `FDU` → `FDUFL...` 的多层前缀，触达样例代码深处的 `assert` 与 `raise RuntimeError`。

## Sample 4（HTMLParser）

20 秒内未触发崩溃；对应 `path` 调度下覆盖了 657 行 HTMLParser 内部代码与 25,805 条唯一执行路径。
