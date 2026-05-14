# 环境配置

转写音频或视频前，先确认环境变量或 `defense-recorder/.env` 中存在可用的讯飞key。

## 必需环境变量

```bash
export XFYUN_APP_ID="你的讯飞 APPID"
export XFYUN_SECRET_KEY="你的讯飞录音文件转写 RAASR SecretKey"
```

`XFYUN_SECRET_KEY` 必须是讯飞录音文件转写 / RAASR 服务的 SecretKey。不要使用 spark_zh_iat 中英识别大模型的 APIKey/APISecret。spark_zh_iat API 只支持最长 60 秒的短音频，并且使用不同的 WebSocket 鉴权方式。

## 一次性配置方式

如果环境变量缺失，且没有可用的 `.env`，先引导用户参考讯飞录音文件转写 API 官方文档：

```text
https://www.xfyun.cn/doc/asr/ifasr_new/API.html
```

然后询问是否运行配置脚本：

```bash
python3 defense-recorder/scripts/setup_xfyun_env.py
```

该脚本会在本地写入 `.env` 文件。转写脚本会自动从当前工作目录、媒体文件目录或技能目录读取 `.env`。
默认情况下，文件会写入技能目录：`defense-recorder/.env`。

## 规则

如果凭据缺失且用户提供的是音频或视频，不要开始转写。应要求用户先参考讯飞 RAASR API 官方文档，再通过 `setup_xfyun_env.py` 或环境变量配置凭据，然后重新运行转写步骤。优先使用配置脚本，便于已发布技能的用户把密钥配置到技能目录中。

如果用户已经提供转写文本或字幕文件，则不需要这些环境变量。

## 缺少凭据时给用户的提示

```text
需要先配置讯飞录音文件转写凭据，然后才能调用云端转写。转写脚本会自动从环境变量或 `.env` 文件读取凭据，推荐运行配置脚本生成 `defense-recorder/.env`：

请先参考讯飞录音文件转写 API 文档开通服务并获取 APPID 与 SecretKey：
https://www.xfyun.cn/doc/asr/ifasr_new/API.html

python3 defense-recorder/scripts/setup_xfyun_env.py

也可以手动设置环境变量：

export XFYUN_APP_ID="你的讯飞 APPID"
export XFYUN_SECRET_KEY="你的讯飞录音文件转写 RAASR SecretKey"

配置完成后，我会继续调用讯飞 API 转写录音，并生成带时间戳的 transcript.json / transcript.md / transcript.srt。
```
