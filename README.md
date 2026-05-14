# 答辩秘书 Skill

将完整学术答辩会录音、转写文本或字幕文件整理为按答辩人组织的结构化答辩记录，包含陈述概述、评委问答、术语修正和低置信度说明。

这是一个通用 Agent Skill，遵循 `SKILL.md` 格式，可通过 `npx skills add` 安装到 Claude Code、Cursor、Codex、OpenCode 等支持 Agent Skills 的工具中。

## 一键安装

发布到 GitHub 后，其他人可以用下面的命令安装：

```bash
npx skills add <你的用户名>/DefenseRecordSkill --skill defense-recorder
```

指定安装到某些工具：

```bash
npx skills add <你的用户名>/DefenseRecordSkill \
  --skill defense-recorder \
  -a claude-code \
  -a cursor \
  -a codex
```

全局安装并跳过交互确认：

```bash
npx skills add <你的用户名>/DefenseRecordSkill \
  --skill defense-recorder \
  -g \
  -a claude-code \
  -a cursor \
  -a codex \
  -y
```

也可以直接安装 skill 子目录：

```bash
npx skills add https://github.com/<你的用户名>/DefenseRecordSkill/tree/main/skills/defense-recorder
```

安装后重启对应 Agent 工具，或按该工具的说明重新加载 skills。

## 发布结构

仓库中用于发布的唯一 skill 源目录是：

```text
skills/defense-recorder/
```

不要上传本地测试和私密文件：

- `answers/`
- `test/`
- `.env`
- `.agents/`
- `.cursor/`

`.agents/` 和 `.cursor/` 可以作为本地开发/调试副本，但不作为发布源。发布前用下面命令确认待提交文件：

```bash
git status --short
git ls-files --others --exclude-standard
```

默认场景是：

```text
一份录音 = 一场包含多位答辩人的完整答辩会
```

除非用户明确说明，否则不要把整份录音当作单个答辩人的答辩。

## 功能

- 调用讯飞录音文件转写 / RAASR API 转写音频或视频。
- 将整场答辩会切分为多个答辩人场次。
- 为每位答辩人整理陈述概述、评委问答和评委建议。
- 只客观记录问题、回答和时间范围，不评价回答是否充分、是否正面或是否完整。
- 根据当前答辩人的材料修正明确的 ASR 术语错误。
- 对说话人不确定、边界模糊、问答配对不清等内容添加低置信度说明。

## 使用方式

```text
@defense_meeting.m4a
使用答辩秘书 skill，整理这场答辩会的问答记录。
```

也可以同时提供辅助材料：

```text
@defense_meeting.m4a
@答辩顺序表.xlsx
@答辩人名单.pdf
@答辩PPT文件夹
使用答辩秘书 skill，整理这场答辩会的问答记录。
```

## 讯飞转写凭据

完整答辩录音使用讯飞录音文件转写 / RAASR：

- 上传接口：`https://raasr.xfyun.cn/v2/api/upload`
- 凭据变量：`XFYUN_APP_ID` 和 `XFYUN_SECRET_KEY`
- `XFYUN_SECRET_KEY` 必须是 RAASR 服务页面的 `SecretKey`

不要把 spark_zh_iat 中英识别大模型的 `APIKey` 或 `APISecret` 填到 `XFYUN_SECRET_KEY`。spark_zh_iat 是 WebSocket 流式接口，主要面向最长 60 秒的短音频；答辩录音通常需要长文件转写、时间戳和可选角色分离。

如果还没有 `.env`，请先参考讯飞官方文档开通服务并获取 APPID 与 SecretKey：

```text
https://www.xfyun.cn/doc/asr/ifasr_new/API.html
```

推荐运行配置脚本生成 `defense-recorder/.env`：

```bash
python3 .agents/skills/defense-recorder/scripts/setup_xfyun_env.py
```

转写脚本会自动从以下位置读取凭据：

- 环境变量 `XFYUN_APP_ID` / `XFYUN_SECRET_KEY`
- 当前工作目录的 `.env`
- 媒体文件所在目录的 `.env`
- skill 目录的 `.env`

也可以手动设置环境变量：

```bash
export XFYUN_APP_ID="你的讯飞 APPID"
export XFYUN_SECRET_KEY="你的讯飞录音文件转写 RAASR SecretKey"
```

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

默认输出文件：

```text
defense_records.md
```

每位答辩人记录包含：

- 答辩顺序和姓名
- 时间范围
- 论文题目，如可识别
- 识别置信度
- 陈述概述
- 评委问答
- 评委建议
- 术语修正说明
- 低置信度片段

## 当前限制

- 当前 skill 内置了讯飞音频转写脚本，但没有内置 PPT、XLSX、PDF 的统一抽取脚本。
- Codex 可以在具体运行环境中尝试读取辅助材料，但稳定性取决于本机工具和 Python 库。
- 如果需要跨 Codex、Cursor、Claude Code 稳定使用，建议后续增加 `scripts/extract_supporting_materials.py`，将 PPT/XLSX/PDF/CSV/TXT 统一抽取为 `supporting_materials.json`。

## 注意事项

- 不生成官方答辩决议、通过/不通过判断或主观评价。
- 不确定内容应进入低置信度说明，不要强行确定。
- 不要把真实讯飞密钥提交到仓库。
