# Highlight-to-AI

A lightning-fast desktop tool. Highlight any text with your instructions, press a hotkey, and let AI replace it in-place seamlessly.

一款极速的全局 AI 文本处理引擎：划词选中“指令 + 文本”，按下快捷键，自动调用 OpenAI 兼容大模型，并在当前文档中就地替换。

## 当前版本

`v0.1.0` MVP：Windows 优先，命令行后台运行。

已实现：

- 全局快捷键监听。
- 自动复制当前选中文本。
- 调用 OpenAI 兼容 API。
- 将结果粘贴回原位置。
- 默认恢复原剪贴板文本。
- 开始、成功、失败提示音。
- TOML 配置文件。
- 本地日志。

## 使用前准备

需要 Python `3.11+`。

安装依赖：

```powershell
pip install -e .
```

复制示例配置：

```powershell
copy config.example.toml config.toml
```

编辑 `config.toml`，填写你的 OpenAI 兼容服务：

```toml
[api]
base_url = "https://api.deepseek.com"
api_key = "你的 API Key"
model = "deepseek-chat"
```

也可以用环境变量保存 Key：

```powershell
$env:HIGHLIGHT_TO_AI_API_KEY="你的 API Key"
```

如果没有指定 `HIGHLIGHT_TO_AI_CONFIG`，程序默认读取：

```text
%APPDATA%\Highlight-to-AI\config.toml
```

首次启动时如果该文件不存在，会自动生成一份默认配置。

## 启动

### 一键启动（Windows）

直接双击项目根目录的 `start.bat` 即可。

如果你在 PowerShell 里执行后立即退出，请查看脚本输出的 `[ERROR]` 信息（已增强退出码与错误提示）。

脚本会自动：


- 检查 Python 是否可用。
- 检查并生成 `config.toml`（若缺失）。
- 安装依赖（`pip install -e .`）。
- 使用 `Start-Process` 后台启动（优先 `pythonw`）。
- 创建系统托盘图标，可在托盘菜单中打开配置或退出程序。


### 手动启动

```powershell
highlight-to-ai
```

或：

```powershell
python -m highlight_to_ai
```

启动后将驻留在系统托盘（无主界面）。默认快捷键：



```text
F3
```

## 使用方式

1. 在任意文本输入框或编辑器中写下“指令 + 内容”。
2. 选中整段文本。
3. 按下配置的全局快捷键。
4. 等待提示音，选中文本会被 AI 结果替换。

示例选中文本：

```text
帮我把这句话润色得委婉专业一点：老板，项目做完了，我要请假
```

替换结果示例：

```text
王总您好，目前项目已顺利完成。近期因个人事务，希望能申请几天休假，恳请您批准。
```

## 配置说明

```toml
[app]
language = "zh-CN"
restore_clipboard = true
beep = true
copy_timeout_seconds = 1.0
paste_delay_seconds = 0.15

[hotkey]
trigger = "<f3>"

[api]
base_url = "https://api.deepseek.com"
api_key = ""
model = "deepseek-chat"
timeout_seconds = 15
max_tokens = 2048
temperature = 0.3

[prompt]
system = "你是一个极简的文本处理引擎……"
```

快捷键格式使用 `pynput` 的 `GlobalHotKeys` 格式，例如：

- `<f3>`
- `<ctrl>+<alt>+h`
- `<ctrl>+<shift>+space`


## 隐私说明

- 程序不会默认保存选中文本或 AI 返回结果。
- 日志只记录字符数、耗时、错误信息，不记录原文。
- 选中文本会发送到你配置的 OpenAI 兼容 API 服务商。
- MVP 阶段剪贴板恢复以文本为主，不保证完整恢复图片、文件等非文本剪贴板内容。

## 日志位置

Windows 默认：

```text
%APPDATA%\Highlight-to-AI\logs\app.log
```

## 开发文档

- `Docs/design.md`
- `Docs/development-plan.md`
- `Docs/architecture.md`

## 后续计划

- 系统托盘入口。
- 设置界面。
- API 连通性测试按钮。
- Windows EXE 打包。
- Prompt 模板库。
- macOS 支持。
