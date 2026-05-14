# 术语修正

修正专业术语、英文缩写、模型名称、数据集名称、硬件名称、学校或院系名称中的明确 ASR 错误。

## 术语来源

```yaml
global_terms:
  - 学校名称
  - 学院名称
  - 答辩委员会
  - 通用学术术语
candidate_terms:
  candidate_name:
    - 当前答辩人幻灯片、论文、摘要、题目或陈述中的术语
```

## 隔离规则

处理某一位答辩人的记录时，只能使用：

```text
global_terms + 当前答辩人术语
```

不要使用其他答辩人的术语来修正当前答辩人的内容。

## 修正规则

- 只修正明显的 ASR 错误。
- 只修正术语和专有名词。
- 不要改变原意。
- 不确定时不要替换，应记录不确定性。
- 保留修正日志。

## 输出

```yaml
corrected_qa_records:
term_corrections:
  - before:
    after:
    evidence:
uncertain_corrections:
  - term:
    note:
```
