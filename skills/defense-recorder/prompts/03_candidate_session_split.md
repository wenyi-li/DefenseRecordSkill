# 答辩人场次拆分

针对单个答辩人场次，将转写轮次拆分为陈述、问答和过渡片段。

## 片段定义

- `presentation`: 当前答辩人连续较长时间介绍研究背景、方法、实验、贡献和总结。
- `qa`: 评委与答辩人交替发言，包含提问、质疑、澄清、建议和回答。
- `transition`: 主持人的流程控制、致谢、时间提醒、下一位答辩人切换等内容。

## 规则

- 只在当前答辩人场次内部进行拆分。
- 除非边界证据充分，不要把转写轮次移动到相邻答辩人场次。
- 如果陈述和问答的边界不清楚，保留最合理的估计，并添加低置信度说明。

## 输出

```json
{
  "candidate_name": "张三",
  "segments": [
    {
      "type": "presentation",
      "start_time": "00:05:12",
      "end_time": "00:22:30",
      "summary": "..."
    },
    {
      "type": "qa",
      "start_time": "00:22:31",
      "end_time": "00:37:40",
      "summary": "..."
    },
    {
      "type": "transition",
      "start_time": "00:37:41",
      "end_time": "00:38:45",
      "summary": "..."
    }
  ],
  "low_confidence_notes": []
}
```
