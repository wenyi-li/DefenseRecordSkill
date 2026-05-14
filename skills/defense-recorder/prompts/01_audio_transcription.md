# 音频转写

通过讯飞录音文件转写 API，把主要音频或视频转换为带时间戳和说话人轮次的文本。保留可能的问答内容；此阶段不要概括。

## API 工具

当命令执行能力和讯飞凭据都可用时，运行内置的讯飞 API 封装脚本：

必须先通过一次性配置脚本设置凭据：

```bash
python3 defense-recorder/scripts/setup_xfyun_env.py
```

默认会把凭据写入 `defense-recorder/.env`。

如果 `.env` 不存在，且环境变量中也没有凭据，配置前先引导用户参考讯飞录音文件转写 API 官方文档：

```text
https://www.xfyun.cn/doc/asr/ifasr_new/API.html
```

也可以使用环境变量：

```bash
export XFYUN_APP_ID="你的讯飞 APPID"
export XFYUN_SECRET_KEY="你的讯飞录音文件转写 RAASR SecretKey"
```

```bash
python3 scripts/transcribe_audio.py {{audio_or_video_file}} \
  --output-dir transcript_output \
  --language cn \
  --role-type 1 \
  --role-num 0 \
  --pd edu
```

使用 `transcript_output/transcript.json` 作为主要转写中间文件。脚本会调用讯飞录音文件转写，并请求角色分离。如果角色分离不可用，或说话人区分不清，继续处理，但在低置信度说明中标注说话人不确定。

如果讯飞 API 转写不可用，停止处理，并要求用户提供有效 API 凭据、可用额度，或已有的转写文本/字幕文件。

## 必需中间格式

```json
[
  {
    "start": "hh:mm:ss",
    "end": "hh:mm:ss",
    "speaker": "SPEAKER_XX",
    "text": "..."
  }
]
```

## 规则

- 保留时间戳。
- 如果存在说话人分离结果，应保留说话人信息。
- 将听不清的内容标记为 `[听不清]`。
- 尽量按转写原文保留中英混说、英文术语、缩写、数据集名称、模型名称和硬件名称。
- 转写阶段不要删除重复表达或口头填充词；清理工作在问答抽取阶段完成。
- 转写完成前不要推断答辩人场次。

## 转写不可用时的兜底提示

使用以下提示：

```text
当前环境无法通过讯飞 API 完成音频转写，或缺少讯飞 API 凭据/可用额度。请先参考讯飞录音文件转写 API 文档开通服务并获取 APPID 与 SecretKey：https://www.xfyun.cn/doc/asr/ifasr_new/API.html。也可以提供该录音的转写文本、字幕文件，或配置可用于讯飞录音文件转写的 XFYUN_APP_ID 与 XFYUN_SECRET_KEY 后再运行转写。收到转写文本后，我可以继续完成答辩人切分、问答抽取和记录生成。
```
