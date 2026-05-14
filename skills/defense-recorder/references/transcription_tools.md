# 讯飞转写工具

当用户提供音频或视频文件时，使用 `scripts/transcribe_audio.py`。本技能的音频转写仅通过讯飞录音文件转写 API 完成。

如果讯飞 API 转写不可用，要求用户提供有效的讯飞录音文件转写凭据/额度，或已有的转写文本/字幕文件。

## 必需凭据

创建或启用讯飞录音文件转写应用。一次性配置可运行：

如果缺少 `.env`，先参考讯飞录音文件转写 API 官方文档，开通服务并获取正确的 `APPID` 和 `SecretKey`：

```text
https://www.xfyun.cn/doc/asr/ifasr_new/API.html
```

```bash
python3 defense-recorder/scripts/setup_xfyun_env.py
```

该命令会写入 `defense-recorder/.env`，`scripts/transcribe_audio.py` 会自动读取。

也可以设置环境变量：

```bash
export XFYUN_APP_ID="你的讯飞 APPID"
export XFYUN_SECRET_KEY="你的讯飞录音文件转写 RAASR SecretKey"
```

使用讯飞录音文件转写 / RAASR 服务的 `SecretKey`。不要使用 spark_zh_iat 中英识别大模型的 `APIKey` 或 `APISecret`；将这些密钥与 APPID 混用通常会导致 `signa verify fail`。

文档中 `wss://iat.xf-yun.com/v1` 对应的 spark_zh_iat API 是另一种 WebSocket 流式服务。它使用 `APIKey`/`APISecret` HMAC-SHA256 鉴权，并且只接受最长 60 秒的音频，因此不作为完整答辩会录音的默认处理路径。

不要把真实密钥放入发布的技能包中。每位用户安装技能后都应自行运行配置脚本，在本地创建自己的 `defense-recorder/.env`。

运行转写前，技能必须先检查凭据。如果凭据缺失，应暂停并要求用户运行配置脚本，不要尝试上传文件。

## 命令

```bash
python3 scripts/transcribe_audio.py path/to/defense.m4a \
  --output-dir transcript_output \
  --language cn \
  --role-type 1 \
  --role-num 0 \
  --pd edu
```

如需在不上传音频的情况下检查本地凭据解析：

```bash
python3 scripts/transcribe_audio.py path/to/defense.m4a --auth-check
```

输出文件：

- `transcript_output/transcript.json`
- `transcript_output/transcript.md`
- `transcript_output/transcript.srt`
- `transcript_output/raw_response.json`
- `transcript_output/raw_order_result.json`

## 说话人分离

脚本通过 `--role-type 1` 请求讯飞角色分离。这要求用户的讯飞账号/应用已启用角色分离能力。已知预期说话人数时使用 `--role-num N`；未知时使用 `0` 进行盲分离。

如果角色分离不可用或质量较低，继续使用时间戳处理，并在最终低置信度部分标注说话人不确定。

## 常用选项

- `--language cn`: 普通话/通用中文。
- `--language en`: 英语。
- `--language-type 1`: 中文录音的中英文自动模式。
- `--hotword "CUDA|Triton|医学图像分割"`: 提高领域术语识别效果。
- `--pd edu`: 教育领域；可选值还包括 `tech`、`medical`、`finance` 等。

## 限制与计费

根据讯飞录音文件转写官方文档，标准 API 支持最大 500 MB、最长 5 小时的音频/视频文件，已完成结果保留 72 小时，并通过异步方式返回结果。新用户可能有试用额度，但上传前必须在用户自己的讯飞控制台检查额度和计费情况。
