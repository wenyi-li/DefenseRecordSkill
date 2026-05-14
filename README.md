# Defense Recorder

Defense Recorder 是一个用于整理学术答辩记录的 Agent Skill。它可以将完整答辩会录音、视频、转写文本或字幕文件整理为按答辩人组织的结构化 Markdown 记录，包含陈述概述、评委问答、评委建议、术语修正和低置信度说明。

## 安装

```bash
npx skills add wenyi-li/DefenseRecordSkill --skill defense-recorder
```

## 快速使用

提供答辩录音或已有转写文本，然后要求 Agent 使用 `defense-recorder` 整理记录：

```text
@defense_meeting.m4a
使用 defense-recorder 整理这场答辩会的问答记录。
```

建议同时提供答辩顺序、答辩人名单、PPT、论文摘要或学院模板，以提高姓名、题目、术语和场次边界的准确性：

```text
@defense_meeting.m4a
@答辩顺序表.xlsx
@答辩人名单.pdf
@答辩PPT文件夹
使用 defense-recorder 整理这场答辩会的问答记录。
```


## 功能

- 调用讯飞录音文件转写 / RAASR API 转写音频或视频。
- 将整场答辩会切分为多个答辩人场次。
- 为每位答辩人整理陈述概述、评委问答和评委建议。
- 根据当前答辩人的材料修正明确的 ASR 术语错误。
- 对说话人不确定、场次边界模糊、问答配对不清等内容添加低置信度说明。

## 输入

主要输入可以是：

- 音频或视频：`.mp3`、`.m4a`、`.wav`、`.flac`、`.aac`、`.mp4`
- 已有转写或字幕：`.txt`、`.md`、`.srt`、`.vtt`、`.json`

可选辅助材料包括：

- 答辩人名单
- 答辩顺序表
- 评委名单
- PPT 或幻灯片文件夹
- 论文 PDF、摘要或学位论文
- 学院指定输出模板
- 用户提供的术语表

辅助材料使用优先级：

```text
答辩顺序表 / 官方名单
> 答辩人 PPT / 论文 / 摘要
> 答辩人陈述内容
> 评委问答内容
> 通用领域知识
```

## 输出

默认输出文件为：

```text
defense_records.md
```

长录音或多答辩人场景还会生成逐人中间文件，便于核查并避免长上下文压缩遗漏：

```text
qa_chunks/<序号>_<姓名>.md     # 当前答辩人的原始问答片段
qa_extracts/<序号>_<姓名>.md   # 当前答辩人的问答/建议抽取结果
```

每位答辩人的记录包含：

- 答辩顺序和姓名
- 时间范围
- 论文题目，如可识别
- 识别置信度
- 陈述概述
- 评委问答
- 评委建议
- 术语修正说明
- 低置信度片段

问答记录格式：

```text
问：...
答：...
```

仅建议记录格式：

```text
建议：...
回应：好的/感谢老师提醒/已记录
```

## 讯飞转写 Key

> 如果未手动配置，skill 会自动提示配置科大讯飞 Key，用于录音转文字。

完整答辩录音使用讯飞录音文件转写 / RAASR：

- 上传接口：`https://raasr.xfyun.cn/v2/api/upload`
- 凭据变量：`XFYUN_APP_ID` 和 `XFYUN_SECRET_KEY`
- `XFYUN_SECRET_KEY` 必须是 RAASR 服务页面的 `SecretKey`

不要把 spark_zh_iat 中英识别大模型的 `APIKey` 或 `APISecret` 填到 `XFYUN_SECRET_KEY`。spark_zh_iat 是 WebSocket 流式接口，主要面向最长 60 秒的短音频；答辩录音通常需要长文件转写、时间戳和可选角色分离。

请先参考讯飞官方文档开通服务并获取 APPID 与 SecretKey：

```text
https://www.xfyun.cn/doc/asr/ifasr_new/API.html
```

可在 [讯飞开放平台录音文件转写服务页面](https://www.xfyun.cn/services/lfasr) 领取免费额度。

配置凭据：

```bash
python3 scripts/setup_xfyun_env.py
```

也可以手动设置环境变量：

```bash
export XFYUN_APP_ID="你的讯飞 APPID"
export XFYUN_SECRET_KEY="你的讯飞录音文件转写 RAASR SecretKey"
```

转写脚本会自动从以下位置读取凭据：

- 环境变量 `XFYUN_APP_ID` / `XFYUN_SECRET_KEY`
- 当前工作目录的 `.env`
- 媒体文件所在目录的 `.env`
- skill 目录的 `.env`

## 工作原则

- 保持每位答辩人的内容相互隔离，不混用相邻场次的问题、回答或术语。
- 不编造答辩人姓名、论文题目、评委问题、回答、时间戳或结论。
- 无法识别姓名时，使用 `未知答辩人 1`、`未知答辩人 2` 等。
- 无法识别论文题目时，写 `论文题目：未识别`。
- 对不确定内容添加低置信度说明，不强行确定。
- 不把全局 `SPEAKER_ID` 直接绑定为答辩人；说话人角色必须在每位答辩人的场次内推断。
- 不生成官方答辩决议、通过/不通过判断或主观评价。

## 仓库结构

```text
skills/defense-recorder/
├── SKILL.md
├── agents/
├── examples/
├── knowledge/
├── prompts/
├── references/
├── scripts/
└── templates/
```

## 隐私与合规

答辩录音和辅助材料可能包含个人信息。
不要将真实讯飞密钥、私人答辩录音、学生材料或未授权的输出记录提交到公开仓库。
