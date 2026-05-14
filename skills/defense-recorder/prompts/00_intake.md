# 输入梳理

识别主要答辩录音和所有辅助材料。不要重复询问用户已经提供的信息。如果缺少辅助材料，但主音频或转写文本足够继续处理，应继续推进。

## 支持的主要媒体

`.mp3`, `.m4a`, `.wav`, `.flac`, `.aac`, `.mp4`

无法直接进行音频转写时，也可以使用转写文本或字幕文件：`.txt`, `.md`, `.srt`, `.vtt`, `.json`。

## 辅助材料分类

- `candidate_list`: 答辩人名单
- `agenda`: 答辩顺序表
- `committee_list`: 评委名单
- `slides`: PPT 或幻灯片文件夹
- `papers`: 论文 PDF、学位论文、摘要
- `output_template`: 学院指定模板
- `custom_terms`: 用户提供的术语表

## 输出

```yaml
main_audio_file:
main_transcript_file:
supporting_files:
  candidate_list:
  agenda:
  slides:
  papers:
  committee_list:
  output_template:
  custom_terms:
missing_information:
processing_plan:
```
