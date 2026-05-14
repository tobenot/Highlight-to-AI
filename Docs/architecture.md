# Highlight-to-AI 架构设计稿

## 1. 架构目标

`Highlight-to-AI` 的架构目标是用尽量轻量的桌面后台程序，实现稳定、安全、可扩展的全局 AI 文本处理能力。

核心质量目标：

- **低延迟**：短文本处理路径尽量短，减少 UI 和中间层开销。
- **低侵入**：不接管具体应用，只通过热键、剪贴板、模拟输入协作。
- **可恢复**：失败时尽量恢复剪贴板和运行状态。
- **可配置**：API、模型、快捷键、提示词、语言等可配置。
- **可替换**：热键、剪贴板、通知、LLM 客户端等能力通过模块封装，便于后续替换实现。

## 2. 总体架构

```text
┌──────────────────────────────────────────────────────────┐
│                    Desktop Applications                   │
│       Mail / Browser / Editor / Word / Chat / Notes       │
└────────────────────────────┬─────────────────────────────┘
                             │ selected text
                             ▼
┌──────────────────────────────────────────────────────────┐
│                  Highlight-to-AI Runtime                  │
│                                                          │
│  ┌─────────────┐     ┌──────────────┐     ┌────────────┐ │
│  │ Hotkey      │───▶ │ Task         │───▶ │ Clipboard  │ │
│  │ Listener    │     │ Orchestrator │     │ Service    │ │
│  └─────────────┘     └──────┬───────┘     └────────────┘ │
│                             │                            │
│                             ▼                            │
│                      ┌──────────────┐                    │
│                      │ LLM Client   │                    │
│                      └──────┬───────┘                    │
│                             │                            │
│        ┌──────────────┬─────┴─────┬──────────────┐      │
│        ▼              ▼           ▼              ▼      │
│  Config Service  Prompt Service  Feedback    Logger     │
│                                Service                   │
└────────────────────────────┬─────────────────────────────┘
                             │ OpenAI-compatible HTTP API
                             ▼
┌──────────────────────────────────────────────────────────┐
│                    LLM Provider                           │
│        DeepSeek / OpenAI-compatible endpoint / Local      │
└──────────────────────────────────────────────────────────┘
```

## 3. 核心流程

### 3.1 正常处理流程

```text
用户选中文本
  ↓
按下全局快捷键
  ↓
Hotkey Listener 捕获事件
  ↓
Task Orchestrator 检查当前是否空闲
  ↓
Feedback Service 发出开始提示
  ↓
Clipboard Service 保存旧剪贴板
  ↓
Input Service 模拟 Ctrl+C
  ↓
Clipboard Service 等待并读取选中文本
  ↓
Prompt Service 组装 system prompt + user text
  ↓
LLM Client 调用 OpenAI 兼容 API
  ↓
校验/清洗模型输出
  ↓
Clipboard Service 写入结果文本
  ↓
Input Service 模拟 Ctrl+V 就地替换
  ↓
按配置恢复旧剪贴板
  ↓
Feedback Service 发出成功提示
  ↓
Task Orchestrator 回到空闲状态
```

### 3.2 失败处理流程

任一步骤失败时：

1. 停止后续危险动作，尤其是停止粘贴。
2. 尽量恢复旧剪贴板。
3. 记录错误日志。
4. 发出失败提示音或通知。
5. 释放任务锁，允许下一次触发。

典型失败场景：

- 未选中文本。
- 剪贴板复制超时。
- API Key 错误。
- API 请求超时。
- 模型返回空内容。
- 粘贴前剪贴板写入失败。

## 4. 模块设计

### 4.1 App Runtime

职责：

- 程序启动入口。
- 初始化配置、日志、热键、托盘。
- 管理生命周期。
- 捕获顶层异常。

建议接口：

```python
class AppRuntime:
    def start(self) -> None: ...
    def stop(self) -> None: ...
```

### 4.2 Config Service

职责：

- 加载 `config.toml`。
- 首次启动生成默认配置。
- 校验必填项。
- 提供运行时配置对象。
- 后续支持保存 GUI 修改。

配置对象建议拆分：

- `AppConfig`
- `HotkeyConfig`
- `ApiConfig`
- `PromptConfig`

关键策略：

- `api_key` 允许来自配置文件或环境变量。
- 日志中禁止打印完整 API Key。
- 配置错误时阻止启动核心功能，并提示用户修复。

### 4.3 Hotkey Listener

职责：

- 注册全局快捷键。
- 捕获触发事件。
- 将事件交给 `TaskOrchestrator`。
- 程序退出时释放监听资源。

MVP 实现：

- 使用 `pynput.keyboard.GlobalHotKeys`。

后续可替换：

- Windows 原生 `RegisterHotKey`。
- macOS 辅助功能权限下的原生监听。

设计约束：

- 热键监听模块不直接处理剪贴板、不直接调用 LLM。
- 只负责事件入口，避免逻辑耦合。

### 4.4 Task Orchestrator

职责：

- 串联一次完整 AI 处理任务。
- 管理任务锁，避免并发触发。
- 统一异常处理。
- 协调反馈、剪贴板、输入、LLM。

关键状态：

```text
IDLE -> COPYING -> REQUESTING -> PASTING -> RESTORING -> IDLE
                 ↘ FAILED ───────────────────────────────↗
```

设计要点：

- 使用互斥锁或状态机，保证同一时间只有一个任务执行。
- API 请求放到后台线程，避免阻塞热键监听线程。
- 所有异常在任务边界收敛，避免后台线程静默死亡。

### 4.5 Clipboard Service

职责：

- 保存旧剪贴板文本。
- 等待复制结果。
- 读取当前剪贴板文本。
- 写入模型结果。
- 恢复旧剪贴板。

MVP 实现：

- 使用 `pyperclip.copy()` / `pyperclip.paste()`。
- 复制后轮询或使用 `waitForNewPaste(timeout)`。

关键问题：

- 如果原剪贴板是图片、文件等非文本内容，`pyperclip` 可能无法完整恢复。
- MVP 可优先支持文本剪贴板恢复；文档中说明限制。
- 后续可通过系统原生剪贴板 API 支持多格式恢复。

### 4.6 Input Service

职责：

- 模拟复制：`Ctrl+C`。
- 模拟粘贴：`Ctrl+V`。
- 根据平台选择快捷键。

MVP 实现：

- Windows 使用 `pyautogui.hotkey('ctrl', 'c')` 和 `pyautogui.hotkey('ctrl', 'v')`。

后续扩展：

- macOS 使用 `command+c` / `command+v`。
- 对部分应用兼容性差时，可切换为 `pynput.keyboard.Controller`。

设计约束：

- Input Service 不关心文本内容。
- 是否执行粘贴由 Task Orchestrator 决定。

### 4.7 LLM Client

职责：

- 初始化 OpenAI 兼容客户端。
- 发送 Chat Completion 请求。
- 处理超时、网络错误、鉴权错误。
- 返回纯文本结果。

MVP 实现：

- 使用 `openai.OpenAI(api_key=..., base_url=...)`。
- 调用 `client.chat.completions.create()`。

建议请求参数：

- `model`
- `messages`
- `temperature`
- `max_tokens`
- `timeout`

输出约束：

- 返回前做 `strip()`。
- 空结果视为失败。
- 不在 LLM Client 中硬编码业务 prompt，Prompt 由 Prompt Service 提供。

### 4.8 Prompt Service

职责：

- 提供默认系统提示词。
- 从配置加载自定义提示词。
- 组装 messages。

默认系统提示词建议：

```text
你是一个极简的文本处理引擎。用户会给你一段文本，其中包含处理指令和待处理内容。请直接执行指令，并只输出最终处理结果。不要输出解释，不要寒暄，不要包含“好的”“以下是”等前置话术。
```

后续增强：

- Prompt 模板库。
- 不同快捷键绑定不同 Prompt。
- 输出后处理规则。

### 4.9 Feedback Service

职责：

- 开始处理提示。
- 成功提示。
- 失败提示。
- 后续支持桌面通知和托盘状态。

MVP 实现：

- Windows 使用 `winsound.MessageBeep()` 或 `winsound.Beep()`。

建议反馈：

| 事件 | 反馈 |
|---|---|
| 开始 | 短促一声 |
| 成功 | 两声短提示 |
| 失败 | 低频或不同音调提示 |

### 4.10 Tray / Settings UI

Beta 阶段引入。

职责：

- 展示后台运行状态。
- 提供设置入口。
- 提供退出入口。
- 提供 API 测试。

建议结构：

- `TrayController`：托盘菜单、状态展示。
- `SettingsWindow`：配置编辑。
- `ConfigService.save()`：保存用户修改。

## 5. 推荐目录结构

```text
Highlight-to-AI/
├─ README.md
├─ LICENSE
├─ pyproject.toml              # 或 requirements.txt
├─ config.example.toml
├─ .gitignore
├─ Docs/
│  ├─ design.md
│  ├─ development-plan.md
│  └─ architecture.md
├─ src/
│  └─ highlight_to_ai/
│     ├─ __init__.py
│     ├─ main.py               # 程序入口
│     ├─ app.py                # AppRuntime
│     ├─ config.py             # ConfigService 与配置模型
│     ├─ hotkey.py             # HotkeyListener
│     ├─ orchestrator.py       # TaskOrchestrator
│     ├─ clipboard.py          # ClipboardService
│     ├─ input_control.py      # InputService
│     ├─ llm.py                # LLMClient
│     ├─ prompt.py             # PromptService
│     ├─ feedback.py           # FeedbackService
│     ├─ logging_config.py     # 日志初始化
│     └─ ui/
│        ├─ tray.py            # Beta
│        └─ settings.py        # Beta
├─ tests/
│  ├─ test_config.py
│  ├─ test_prompt.py
│  └─ test_orchestrator.py
└─ scripts/
   └─ build.ps1                # 打包脚本
```

## 6. 数据与配置架构

### 6.1 配置文件位置

开发阶段：

```text
./config.toml
```

发布阶段建议：

```text
%APPDATA%/Highlight-to-AI/config.toml
```

原因：

- 避免安装目录无写权限。
- 符合 Windows 应用配置习惯。
- 方便升级保留用户配置。

### 6.2 日志文件位置

发布阶段建议：

```text
%APPDATA%/Highlight-to-AI/logs/app.log
```

日志原则：

- 记录任务开始、成功、失败原因、耗时。
- 不记录完整用户选中文本，避免隐私泄露。
- 不记录完整 API Key。
- Debug 模式可选择记录更多信息，但默认关闭。

## 7. 并发与状态设计

### 7.1 线程模型

建议 MVP 线程模型：

```text
Main Thread
  ├─ 初始化配置、日志、托盘
  └─ 启动 Hotkey Listener

Hotkey Listener Thread
  └─ 捕获快捷键后提交任务

Worker Thread
  └─ 执行复制、LLM 请求、粘贴、恢复
```

### 7.2 任务锁

每次触发前检查：

```text
if task_running:
    feedback.busy()
    return
```

作用：

- 避免用户连续按快捷键造成多个 API 请求。
- 避免多个任务争抢剪贴板。
- 避免粘贴结果错乱。

### 7.3 超时控制

建议默认超时：

| 操作 | 超时 |
|---|---|
| 等待复制完成 | 1 秒 |
| API 请求 | 15 秒 |
| 剪贴板写入确认 | 1 秒 |

API 超时后不粘贴，恢复剪贴板并提示失败。

## 8. 安全与隐私设计

### 8.1 API Key

MVP：

- 支持配置文件或环境变量读取。
- `.gitignore` 忽略 `config.toml`。
- 日志中只显示 Key 尾号或完全不显示。

后续：

- 使用系统密钥库 `keyring`。
- 设置界面中 Key 默认脱敏显示。

### 8.2 用户文本

用户选中文本可能包含敏感信息，因此：

- 默认不保存历史记录。
- 默认不在日志中记录原文和结果。
- 文档明确说明：文本会发送到用户配置的 API 服务商。
- 后续如支持历史记录，必须默认关闭，并提供清除入口。

### 8.3 剪贴板

- 默认恢复旧剪贴板。
- 失败时优先恢复。
- 文档说明 MVP 对非文本剪贴板恢复能力有限。

## 9. 错误处理策略

统一错误类型建议：

```python
class HighlightToAIError(Exception): ...
class EmptySelectionError(HighlightToAIError): ...
class ClipboardTimeoutError(HighlightToAIError): ...
class LLMRequestError(HighlightToAIError): ...
class EmptyLLMResultError(HighlightToAIError): ...
```

错误处理原则：

1. 模块内部抛出明确异常。
2. `TaskOrchestrator` 统一捕获。
3. 统一恢复剪贴板。
4. 统一反馈给用户。
5. 统一写入日志。

## 10. 平台适配设计

### 10.1 MVP：Windows

- 复制/粘贴：`Ctrl+C` / `Ctrl+V`。
- 提示音：`winsound`。
- 配置目录：`%APPDATA%`。
- 打包：PyInstaller。

### 10.2 后续：macOS

- 复制/粘贴：`Cmd+C` / `Cmd+V`。
- 权限：需要辅助功能权限。
- 配置目录：`~/Library/Application Support/Highlight-to-AI/`。
- 状态栏：菜单栏图标。

### 10.3 后续：Linux

- 复制/粘贴：`Ctrl+C` / `Ctrl+V`。
- 剪贴板依赖可能需要 `xclip` / `xsel` / Wayland 支持。
- 桌面环境差异较大，优先级低于 Windows/macOS。

## 11. 关键设计决策

### 11.1 为什么采用剪贴板方案

优点：

- 对任意应用通用。
- 无需接入每个应用的插件 API。
- 实现简单，MVP 速度快。

代价：

- 有焦点漂移和剪贴板污染风险。
- 对非标准输入控件兼容性不完全可控。

结论：

- MVP 采用剪贴板方案是最优路径。
- 后续通过提示、锁、超时、恢复策略降低风险。

### 11.2 为什么先支持 OpenAI 兼容 API

优点：

- 兼容 DeepSeek、OpenAI、本地 OpenAI-compatible Server 等。
- 用户自由选择服务商。
- SDK 成熟，接入成本低。

约束：

- 不在 MVP 中适配每个厂商的私有 API。
- 厂商差异通过 `base_url`、`model`、参数配置解决。

### 11.3 为什么 UI 后置

核心价值是“选中即处理”。如果核心链路不稳定，UI 再好也无法使用。因此：

1. 先完成命令行/后台核心闭环。
2. 再增加托盘和设置窗口。
3. 最后优化视觉体验与安装体验。

## 12. MVP 伪代码

```python
def on_hotkey_pressed():
    if orchestrator.is_running:
        feedback.busy()
        return
    orchestrator.run_async()


def process_once():
    old_clipboard = clipboard.get_text_safe()
    try:
        feedback.start()
        input_control.copy()
        selected_text = clipboard.wait_for_text_change(timeout=1.0)
        if not selected_text.strip():
            raise EmptySelectionError()

        messages = prompt.build_messages(selected_text)
        result = llm.complete(messages)
        if not result.strip():
            raise EmptyLLMResultError()

        clipboard.copy(result.strip())
        input_control.paste()
        feedback.success()
    except Exception as exc:
        logger.exception("process failed")
        feedback.failure()
    finally:
        if config.app.restore_clipboard:
            clipboard.copy(old_clipboard)
```

实际实现中需要注意：恢复剪贴板不能过早，否则可能影响目标应用读取粘贴内容。建议粘贴后延迟几十到几百毫秒再恢复。

## 13. 可测试性设计

为避免桌面自动化难以测试，建议将模块分层：

- `PromptService`、`ConfigService`、`LLMClient` 参数组装可做单元测试。
- `TaskOrchestrator` 使用 mock 的 Clipboard/Input/LLM/Feedback 做流程测试。
- 真正的 `pyautogui` 与 `pyperclip` 行为放到手工集成测试。

测试重点：

- 空选区不调用 LLM。
- LLM 失败不粘贴。
- 成功路径调用顺序正确。
- 任务锁能阻止重复执行。
- 剪贴板恢复在成功和失败路径都被执行。

## 14. 架构演进路线

### 阶段一：单进程模块化

- 所有模块在同一 Python 进程内。
- 重点保证核心链路跑通。

### 阶段二：托盘化后台应用

- 加入托盘和设置窗口。
- 核心处理逻辑保持不变。
- UI 只通过配置和命令调用核心服务。

### 阶段三：平台适配层

抽象平台相关能力：

```text
PlatformAdapter
  ├─ WindowsAdapter
  ├─ MacOSAdapter
  └─ LinuxAdapter
```

适配内容：

- 复制/粘贴快捷键。
- 配置目录。
- 通知。
- 提示音。
- 权限检查。

### 阶段四：高级能力

- Prompt 模板。
- 多模型。
- 历史记录。
- 流式响应。
- 原生热键实现。
- 多格式剪贴板恢复。

## 15. 总结

推荐采用“核心流程优先、模块边界清晰、平台能力可替换”的架构。MVP 不追求复杂 UI，而是优先验证最关键的四步：

```text
全局热键 → 复制选区 → LLM 处理 → 就地替换
```

只要这条链路稳定，后续托盘、设置界面、多模型、跨平台都可以在现有模块边界上自然扩展。
