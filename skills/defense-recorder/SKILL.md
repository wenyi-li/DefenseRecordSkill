---
name: defense-recorder
description: "将完整学术答辩会录音、转写文本或字幕文件整理为按答辩人组织的结构化答辩记录，包含陈述概述、评委问答、术语修正和低置信度说明。适用于用户要求整理答辩录音、生成答辩记录、提取评委问答、使用答辩秘书技能、处理答辩录音、论文答辩音频或评委问答记录的场景。"
metadata:
  argument-hint: "[音频文件或转写文本]"
  version: "0.1.0"
  user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---

# 答辩秘书

使用本技能将完整学术答辩会整理为可供秘书审核的 Markdown 草稿。默认假设为：

```text
一份录音 = 一场包含多位答辩人的完整答辩会
```

除非用户明确说明，否则不要把整份录音当作单个答辩人的答辩。

## 核心规则

- 将会议切分为 `答辩会 -> 答辩人场次 -> 陈述片段 + 问答片段`。
- 默认生成 `defense_records.md`；如果不适合写文件，则直接用 Markdown 回复。
- 保持每位答辩人的内容相互隔离：不要混用相邻场次的问题、回答或术语。
- 不要编造答辩人姓名、论文题目、评委问题、回答、时间戳或结论。
- 如果无法识别姓名，使用 `未知答辩人 1`、`未知答辩人 2` 等。
- 如果无法识别论文题目，写 `论文题目：未识别`。
- 不要生成官方答辩决议、通过/不通过判断或主观评价。
- 对不确定内容，应放入低置信度说明，不要强行确定。
- 不要把某个全局 `SPEAKER_ID` 直接绑定为 `答辩人`；说话人角色必须在每位答辩人的场次内推断。
- 概括回答时删除口头填充词和寒暄，但保留含义、局限和承诺后续补充的内容。
- 不要评价答辩人回答是否充分、是否正面或是否完整；只客观记录问题、回答和时间范围。
- 不要把评委建议强行转成问答。如果评委只提出格式、写作、实验或修改建议，而答辩人只是确认收到，应记录在 `评委建议` 下，不要写成 `问/答`。

## 工作流程

1. 如果用户提供音频或视频，先按照 [`prompts/00_env_setup.md`](prompts/00_env_setup.md) 检查 `XFYUN_APP_ID` / `XFYUN_SECRET_KEY` 或 `defense-recorder/.env` 中是否有可用的讯飞凭据。如果凭据缺失，转写前停止，并要求用户参考讯飞 RAASR API 文档 <https://www.xfyun.cn/doc/asr/ifasr_new/API.html>，然后运行 `scripts/setup_xfyun_env.py` 或设置环境变量。
2. 使用 [`prompts/00_intake.md`](prompts/00_intake.md) 梳理输入材料。
3. 如果用户提供音频或视频，仅在可以执行命令且 `XFYUN_APP_ID` / `XFYUN_SECRET_KEY` 可用时，使用讯飞 API 封装脚本 [`scripts/transcribe_audio.py`](scripts/transcribe_audio.py) 转写。命令参数参考 [`references/transcription_tools.md`](references/transcription_tools.md)。使用 `--role-type 1` 请求角色分离；如果说话人分离不可用，则继续使用带时间戳的转写文本，并标注说话人不确定。
4. 按以下优先级使用辅助材料：

```text
答辩顺序表 / 官方名单
> 答辩人 PPT / 论文 / 摘要
> 答辩人陈述内容
> 评委问答内容
> 通用领域知识
```

5. 使用 [`prompts/02_meeting_segmentation.md`](prompts/02_meeting_segmentation.md) 将整场会议切分为答辩人场次。
6. 使用 [`prompts/03_candidate_session_split.md`](prompts/03_candidate_session_split.md) 将每位答辩人的场次拆分为陈述、问答和过渡片段。
7. 使用 [`prompts/04_qa_extraction.md`](prompts/04_qa_extraction.md) 按答辩人抽取问答记录。
8. 按照 [`prompts/05_term_correction.md`](prompts/05_term_correction.md)，仅使用 `global_terms + 当前答辩人术语` 修正明确的 ASR 术语错误。
9. 使用 [`prompts/06_final_minutes.md`](prompts/06_final_minutes.md) 和 [`templates/defense_minutes_template.md`](templates/defense_minutes_template.md) 生成最终 Markdown。
10. 用户后续提出修正时，使用 [`prompts/07_correction_handler.md`](prompts/07_correction_handler.md) 只更新受影响的部分。

## 音频转写工具

当输入为音频或视频文件时，先使用讯飞录音文件转写 API 封装脚本：

```bash
python3 scripts/setup_xfyun_env.py
```

默认会把凭据写入 `defense-recorder/.env`。

或使用：

```bash
export XFYUN_APP_ID="你的讯飞 APPID"
export XFYUN_SECRET_KEY="你的讯飞录音文件转写 RAASR SecretKey"
```

`XFYUN_SECRET_KEY` 必须是讯飞录音文件转写 / RAASR 服务的 SecretKey，而不是应用级 APISecret 或 APIKey。

```bash
python3 scripts/transcribe_audio.py AUDIO_OR_VIDEO_FILE \
  --output-dir transcript_output \
  --language cn \
  --role-type 1 \
  --role-num 0 \
  --pd edu
```

使用生成的 `transcript_output/transcript.json` 作为主要中间转写文件。脚本会将媒体文件上传到讯飞、轮询订单结果，并把讯飞输出规范化为 JSON/Markdown/SRT 转写文件。如果缺少凭据、额度不可用或命令无法运行，使用 [`prompts/01_audio_transcription.md`](prompts/01_audio_transcription.md) 中的兜底提示，并要求用户提供转写文本或字幕输入。

本技能的音频转写路径仅使用 API。如果 API 转写无法运行，要求用户提供有效的讯飞凭据/额度，或已有转写文本/字幕文件。

## 必需输出结构

每位答辩人的章节应包含：

- 答辩顺序和姓名
- 时间范围
- 论文题目，如可识别
- 置信度
- 陈述概述
- 评委问答记录
- 评委建议，用于记录不是实际问题的建议

每条问答记录必须使用：

```text
问：...
答：...
时间范围：hh:mm:ss - hh:mm:ss
```

仅建议记录应使用：

```text
建议：...
回应：好的/感谢老师提醒/已记录
时间范围：hh:mm:ss - hh:mm:ss
```

## 边界信号

优先使用明确流程语言：

- `下面请第一位同学进行汇报`
- `请张三同学开始答辩`
- `我的论文题目是...`
- `下面进入专家提问环节`
- `请各位老师提问`
- `张三同学答辩到此结束`
- `下面请下一位同学`

如果缺少这些信号，则根据“较长陈述 -> 评委问答 -> 下一段较长陈述”的模式推断边界。推断得到或存在歧义的边界应标记为低置信度。

## 低置信度说明

对音频不清、说话人不确定、答辩人身份不明确、场次边界模糊、问答配对有歧义、可能串到相邻答辩人、术语修正不确定或论文题目缺失等情况添加说明。

## 隐私与合规

答辩录音可能包含个人信息。只纳入与答辩记录相关的信息。不要暴露无关隐私细节，也不要推断材料中没有明确支持的身份、关系或结果。
