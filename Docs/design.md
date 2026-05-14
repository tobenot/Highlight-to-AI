
---

# Highlight-to-AI - 极速内联文本处理引擎 (V2版)

## 1. 项目背景与目标
**痛点**：用户希望在任意文档编辑时，能利用现有的语音输入法快速写下 AI 指令，并立刻对选中文本进行处理，而不需要复制粘贴到网页版的 AI 对话框中。
**目标**：开发一款极轻量的 Python 后台工具，实现“**框选（包含指令的文本） -> 一键触发 -> 极速推理 -> 就地替换**”的丝滑体验。

## 2. 核心使用场景 (User Story)
**场景：在写邮件时快速润色**
1. 用户在邮件客户端里写了一段草稿：“老板，项目做完了，我要请假”。
2. 用户直接用电脑自带的语音输入法，在草稿前面补充指令：“*帮我把这句话润色得委婉专业一点：*老板，项目做完了，我要请假”。
3. 用户用鼠标**选中这一整句话**。
4. 用户按下全局快捷键（例如 `F3` ）。
5. 屏幕光标处出现极短的等待（约 1-2 秒），选中的文字瞬间被替换为：“王总您好，目前该项目已顺利推进完成。近期因个人事务，希望能申请几天休假，望您批准。”

## 3. 核心功能需求 (MVP 阶段)

### 3.1 全局快捷键监听
*   **一键触发**：监听特定的全局快捷键。一旦按下，立即执行文本获取流程。
*   **后台静默**：程序无主界面，开机后静默运行在系统后台。

### 3.2 极速上下文获取（剪贴板接管）
*   **自动复制**：触发快捷键后，程序模拟按下 `Ctrl + C`（Mac 为 `Cmd + C`）。
*   **文本提取**：通过剪贴板读取被选中的文本（该文本已包含用户的“自然语言指令”和“待处理内容”）。

### 3.3 大模型极速推理 (LLM Processing)
*   **系统级 Prompt 设定（核心灵魂）**：因为用户选中的文本既包含指令又包含内容，大模型需要足够聪明。必须在代码里写死一段强大的 System Prompt：
    *   *System Prompt 示例*：“你是一个极简的文本处理引擎。用户会给你一段文本，其中包含了【处理指令】和【待处理内容】。请你直接执行指令，并**只输出最终的处理结果**。不要输出任何解释，不要包含‘好的’、‘这是润色后的结果’等废话。”
*   **极速 API 调用**：将提取到的文本发送给大模型（使用 DeepSeek 的 API，速度极快且成本极低）。

### 3.4 就地无缝替换 (Inline Replacement)
*   **自动粘贴**：将大模型返回的纯文本结果写入系统剪贴板。
*   **模拟输出**：模拟按下 `Ctrl + V`（Mac 为 `Cmd + V`），将原本选中的“指令+草稿”直接覆盖替换为“最终结果”。
*   **剪贴板恢复（可选）**：替换完成后，将剪贴板恢复为用户触发快捷键之前的状态，做到无痕运行。

---

## 4. 技术栈与架构设计 (Python)

因为去掉了录音和语音识别模块，技术栈变得非常简单干净，**代码量可以控制在 50 行以内**：

*   **全局快捷键**：`keyboard` 库（Windows）或 `pynput` 库（Mac/Windows）。
*   **键鼠模拟**：`pyautogui` 库（发送 Ctrl+C 和 Ctrl+V）。
*   **剪贴板操作**：`pyperclip` 库。
*   **大模型调用**：`openai` 官方库（用于调用兼容 OpenAI 格式的极速大模型 API）。

## 5. 难点与体验优化 (非功能性需求)
1.  **极速响应**：为了达到“闪电”般的速度，必须选择 TTFT（首字响应时间）极短的模型 API。
2.  **系统级提示音（状态反馈）**：因为没有 UI，用户按下快捷键后不知道程序有没有在运行。
    *   *优化方案*：按下快捷键时，调用系统发出一声短促的“滴”声（表示开始处理）；处理完成并粘贴时，发出两声“滴滴”（表示完成）。可以使用 Python 的 `winsound` (Windows) 或简单的系统提示音。
3.  **防误操作**：如果在处理的这 1~2 秒内，用户鼠标点到了别的地方，`Ctrl+V` 可能会粘贴错位置。
    *   *优化方案*：在处理期间，可以通过系统通知（Toast）提示“AI处理中...”，提醒用户保持光标位置不变。

---

### 总结与下一步

这个 V2 版本的方案**极其优雅**。它把最麻烦的“语音识别”交给了你现有的输入法，把 Python 脚本变成了一个纯粹的“文本搬运工 + AI 放大器”。

这个项目非常适合作为 Python 新手或效率极客的实战项目。如果你觉得这个策划案完美契合你的想法，我们现在就可以直接写代码了！


整体需要可以配置，比如说Api key，比如说快捷键这些需要配置。我觉得他的名字还可以更直接一点，比如说就是一个。就是那种让ai处理你的文本的这种感觉，请你头脑风暴一下可以叫什么？

它可以是有界面的，可以是有界面的，没关系。

支持中英文。自定义API key。暂时只支持OpenAI格式的API URL和Key。

---

## 6. 调研文档（网络资料汇总）

> 说明：本调研优先采用官方文档与官方仓库信息。由于部分站点存在反爬/验证页，少量内容基于可访问到的官方仓库说明与公开 API 文档摘要整理。

### 6.1 调研目标
- **验证可行性**：全局快捷键触发 -> 复制选中内容 -> LLM 处理 -> 原位替换。
- **确认约束**：跨平台差异、权限要求、剪贴板稳定性、误粘贴风险。
- **明确接入**：仅支持 OpenAI 格式 API URL + Key 的最小实现路径。

### 6.2 关键能力与资料结论

#### A. 全局快捷键监听
- **结论**：方案可行，Windows 下可用第三方库（`keyboard` / `pynput`）或直接走 Win32 全局热键机制。
- **证据要点**：
  - `boppreh/keyboard` 官方仓库明确该库可做全局键盘事件监听和热键注册，但仓库也标注“当前无人维护（unmaintained）”。
  - `pynput` 官方文档提供 `HotKey` / `GlobalHotKeys` 思路（监听线程模型）。
  - Windows 原生有 `RegisterHotKey`（Win32 API）。
- **工程建议**：
  - MVP（Windows 优先）先用 `keyboard` 或 `pynput` 快速落地。
  - 若后续追求稳定性，Windows 端可考虑切换到 Win32 原生热键封装。

#### B. 复制/粘贴模拟与输入控制
- **结论**：`pyautogui.hotkey('ctrl', 'c'/'v')` 可满足 MVP。
- **风险**：焦点窗口变化会导致“复制或粘贴到错误位置”。
- **工程建议**：
  - 处理期间给状态提示（系统提示音或通知）。
  - 控制总耗时；必要时支持“取消本次粘贴”。

#### C. 剪贴板读写
- **结论**：`pyperclip` 提供 `copy/paste` 与 `waitForPaste/waitForNewPaste`，可用于稳定等待复制完成。
- **工程建议**：
  - 触发后先保存旧剪贴板 -> 发送 `Ctrl+C` -> `waitForNewPaste(timeout)` -> 调用模型 -> 写回并 `Ctrl+V` -> 恢复旧剪贴板（可配置）。
  - 为空选区、超时、非文本内容设置降级路径。

#### D. LLM 调用（OpenAI 格式）
- **结论**：`openai` Python 官方库支持 `api_key` 与 `base_url` 配置，符合“自定义 OpenAI 兼容端点”的目标。
- **证据要点**：
  - 官方仓库 README 展示 `OpenAI(api_key=..., base_url=...)` 初始化方式。
  - 可通过环境变量 `OPENAI_API_KEY` / `OPENAI_BASE_URL` 配置。
- **工程建议**：
  - 配置项至少包含：`base_url`、`api_key`、`model`、`timeout`、`max_tokens`。
  - 输出策略采用“只返回结果文本”的系统提示词，降低冗余话术。

#### E. 状态反馈（提示音/通知）
- **结论**：Windows 下 `winsound`（Python 标准库）可快速实现开始/结束声音反馈。
- **补充**：桌面 Toast 在 Windows 桌面应用中可实现，但集成复杂度高于提示音。
- **工程建议**：
  - MVP 先上提示音；通知作为可选增强项。

#### F. 托盘与配置界面（你已提出“可以有界面”）
- **结论**：`pystray` 可提供系统托盘入口（设置、退出、状态）。
- **工程建议**：
  - 使用托盘 + 简易设置窗口（如 Tkinter）管理热键、API 配置。
  - 对外仅暴露必要配置，避免把复杂度推给用户。

### 6.3 选型对比（MVP 视角）

| 能力 | 候选方案 | 优点 | 风险/缺点 | 建议 |
|---|---|---|---|---|
| 全局热键 | `keyboard` | 上手快、API 直接 | 官方标注长期无人维护 | 作为快速原型可用 |
| 全局热键 | `pynput` | 跨平台更自然 | 监听线程与状态管理稍复杂 | 更适合中期演进 |
| 全局热键 | Win32 `RegisterHotKey` | 稳定、系统原生 | Windows 专用、开发成本高 | 稳定版可升级 |
| 输入模拟 | `pyautogui` | 简单、够用 | 焦点漂移会误操作 | MVP 推荐 |
| 剪贴板 | `pyperclip` | API 极简，等待函数实用 | 平台依赖细节需处理 | 推荐 |
| API 调用 | `openai` Python SDK | 支持 `base_url`，生态成熟 | 需处理超时/重试 | 推荐 |

### 6.4 风险清单与规避
- **误粘贴风险（最高）**：AI 返回前用户切焦点。
  - **规避**：提示音 + 处理中提醒 + 超时自动放弃粘贴。
- **热键冲突**：被系统/其它软件占用。
  - **规避**：支持自定义热键，并在设置页实时检测冲突。
- **模型输出不干净**：出现“好的，以下是...”等冗余。
  - **规避**：强化系统提示词；必要时做结果后处理（去前后话术）。
- **剪贴板污染**：覆盖用户原剪贴板。
  - **规避**：默认恢复原剪贴板，并允许关闭。

### 6.5 推荐落地方案（结论）
- **MVP 推荐栈（Windows 优先）**：
  - 热键：`pynput`（或先 `keyboard` 快速验证）
  - 模拟按键：`pyautogui`
  - 剪贴板：`pyperclip`
  - LLM：`openai` SDK + 自定义 `base_url`/`api_key`
  - 反馈：`winsound`
  - 托盘/设置：`pystray` + 简易 GUI
- **一句话结论**：该功能技术上完全可落地，MVP 的核心挑战不是“能不能做”，而是“如何在 1~2 秒内确保不误粘贴、可感知、可恢复”。

### 6.6 参考资料（可访问来源）
- OpenAI Python SDK 官方仓库：`https://github.com/openai/openai-python`
- keyboard 官方仓库（含维护状态说明）：`https://github.com/boppreh/keyboard`
- pynput 键盘文档：`https://pynput.readthedocs.io/en/latest/keyboard.html`
- pyperclip 文档与仓库：`https://pyperclip.readthedocs.io/`、`https://github.com/asweigart/pyperclip`
- Python `winsound` 标准库文档：`https://docs.python.org/3/library/winsound.html`
- Windows 全局热键 `RegisterHotKey`：`https://learn.microsoft.com/zh-cn/windows/win32/api/winuser/nf-winuser-registerhotkey`
- Windows 剪贴板 API `SetClipboardData`：`https://learn.microsoft.com/zh-cn/windows/win32/api/winuser/nf-winuser-setclipboarddata`
- Windows 桌面 Toast 快速入门：`https://learn.microsoft.com/en-us/windows/win32/shell/quickstart-sending-desktop-toast`
- pystray：`https://pypi.org/project/pystray/`、`https://github.com/moses-palmer/pystray`

### 6.7 为什么会中断（本次调研过程说明）
- 某些文档站点存在 JS 验证或反爬策略，会导致抓取工具超时/中断。
- 为保证可交付，本版文档采用“**先落地可验证结论，再补充可访问官方链接**”策略，后续如你需要，我可以继续补齐每一项的更细参数级引用。


## 调研 2

**目标**：为轻量级 Python 后台工具（支持全局热键 → 选中文本含指令 → LLM 处理 → 就地替换）收集资料、验证方案、提供实现路径和备选。

### 1. 核心功能可行性总结
design.md 提出的“**选中文本（指令+内容） → Ctrl+C → LLM → Ctrl+V 替换**”方案高度可行，且代码量可控（核心逻辑 <100 行）。这本质上是“AI 增强的文本宏/剪贴板管道”工具，类似 Raycast/Alfred 的 Quick AI 或自定义热键工作流，但更通用（任意 App）。

**优势**：
- 利用系统输入法/剪贴板，无需内置语音/OCR。
- OpenAI 兼容 API（DeepSeek 等）速度快、成本低。
- 跨平台潜力高（Windows/Mac 优先，Linux 次之）。

**潜在挑战**：
- 热键冲突、焦点丢失（Ctrl+V 位置错）。
- 剪贴板竞争（其他 App 可能覆盖）。
- 权限（Mac 需要 Accessibility）。
- 延迟控制（目标 1-2s）。

### 2. 技术栈调研与推荐

#### 2.1 全局快捷键监听
- **推荐**：`pynput`（跨平台最佳，支持 HotKey/GlobalHotKeys）。
  - 示例：`keyboard.GlobalHotKeys` 或 `HotKey` 类监听 `<f3>` 等。
  - 优点：非阻塞、支持组合键、多热键。
- 备选：`keyboard` 库（Windows 强，Mac 较弱）；`pyautogui` 辅助。
- 注意：Mac 需要“辅助功能”权限；Windows 需管理员或正确注册热键。

#### 2.2 键鼠模拟与剪贴板
- **剪贴板**：`pyperclip`（跨平台，简单可靠）。
  - `pyperclip.copy(text)` / `paste()`。
- **模拟 Ctrl+C / Ctrl+V**：`pyautogui`（`hotkey('ctrl', 'c')` 等）。
  - 建议：复制后加短 `time.sleep(0.1-0.3)` 确保稳定；粘贴前确保焦点。
  - 问题：有些 App 对模拟输入敏感；备选 `pynput.keyboard.Controller`。
- **剪贴板恢复**：触发前保存旧内容，处理后恢复（可选，但推荐实现“无痕”）。

#### 2.3 LLM 调用（OpenAI 兼容）
- 使用 `openai` 官方 Python 库 + `base_url` 和 `api_key`。
  - DeepSeek 示例：
    ```python
    from openai import OpenAI
    client = OpenAI(api_key=your_key, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(model="deepseek-chat", messages=[...])
    ```
- 支持 Grok、Llama.cpp server、本地模型等任意 OpenAI 兼容端点。
- **System Prompt**：design.md 建议极简“只输出结果、无解释”非常正确。测试时可加温度（temperature=0.3-0.7）和 max_tokens 控制。
- **极速优化**：选 TTFT 低的模型（如 DeepSeek）；流式响应（stream=True）可进一步降低感知延迟。

#### 2.4 系统反馈（声音 + 通知）
- **声音**：
  - Windows：`winsound.Beep()` 或 `MessageBeep`。
  - Mac：`osascript` 或 `afplay` 系统音效。
  - Linux：`print('\a')` 或 `pygame`/`playsound`。
  - 跨平台：`platform` 判断 + 简单函数。
- **Toast 通知**（“AI 处理中...”）：
  - Windows：`win10toast` 或 `windows-toasts`（富通知支持）。
  - 跨平台：`notify2`（Linux/Mac）或 PyQt/PySide 系统托盘通知。

#### 2.5 配置管理（API Key、热键等）
- **推荐格式**：TOML（Python 3.11+ `tomllib`，或 `tomli`）或 YAML（`PyYAML`）。
  - 易读、可注释、支持嵌套（`hotkey: "ctrl+alt+a"`、`api: {base_url, key, model}`）。
- 加载：启动时读 `config.toml`，支持热重载或 GUI 编辑。
- 安全：`.gitignore` config；或用 keyring/env 存敏感 Key。

#### 2.6 GUI / 系统托盘（可选，但推荐）
- **托盘图标**（后台运行 + 设置入口）：PyQt/PySide（`QSystemTrayIcon`）或 `pystray` + Tkinter。
- **配置界面**：Tkinter（内置，轻量）或 CustomTkinter（现代）；PyQt Designer 拖拽。
- 支持：中英文切换、热键自定义、API 测试按钮、Prompt 模板。

### 3. 类似工具与灵感
- **Raycast / Alfred**：Mac 主流，有“选中文本 + 热键 + AI 处理”功能（Pro 版）。你的工具可作为跨平台轻量替代。
- 其他：Cursor/Zed 等 IDE 内联 AI；Clipboard 增强脚本。
- 你的差异化：极简、无订阅、任意 App 通用、强 Prompt 控制。

### 4. 难点与优化建议
1. **防误操作**：处理时显示 Toast + 禁用热键；或用 `pyautogui.position()` 记录光标，验证后粘贴。
2. **性能**：异步调用 LLM（`threading` 或 `asyncio`）；缓存旧剪贴板。
3. **跨平台**：用 `platform.system()` 分支；测试 Win/Mac。
4. **错误处理**：API 失败时恢复剪贴板 + 通知；超时机制。
5. **体验**：Prompt 工程（多版本测试）；支持指令模板（如“润色:”、“翻译成英文:”）。
6. **打包**：PyInstaller 单文件 EXE/App；开机自启（平台差异）。

### 5. 名称头脑风暴（更直接、体现“AI 处理文本”）
**核心方向**：简短、易记、体现“内联/快捷/AI 文本魔法”。

- **极简直接**：TextAI、InlineAI、QuickAI、TextFlash、AI Paste、SmartReplace。
- **中文友好**：闪电文本、AI 瞬改、文本闪电、魔改助手、选即 AI。
- **酷/品牌感**：LightningText、PromptForge、AetherType（以太文本）、VelociText、NexusAI、Text Weaver、InstantAI、ClipMind。
- **推荐**（个人偏好）：
  1. **TextSpark**（文本火花，快速激发）。
  2. **InlineAI** 或 **AI Inline**（直接描述）。
  3. **PromptClip**（Prompt + 剪贴板）。
  4. **FlashEdit** / **LightningEdit**。
  5. **语魔** / **语闪**（中文）。

支持中英文：App 名用英文，界面/文档双语。

### 6. 下一步行动建议
- **MVP 顺序**：1. 热键 + 剪贴板读写 + 模拟键；2. OpenAI 客户端 + Prompt；3. 反馈（声/通知）；4. Config + 托盘；5. 错误处理 + 测试。
- 测试环境：邮件/笔记/浏览器等常见 App。
- 资源：pynput/pyautogui/pyperclip 官方文档；DeepSeek API 快速入门。
- 扩展：多模型切换、历史记录、自定义 Prompt 库。
