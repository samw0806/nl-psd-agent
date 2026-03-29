# 自然语言 PSD Agent -- v4 Codex/Claude Code 落地实现讨论

> **版本**: v4
> **更新日期**: 2026-03-26
> **状态**: 讨论稿
> **主题**: 如何用 Codex / Claude Code 最快落地"自然语言操作 PSD"

---

## 一、核心问题：Agent 到底能做什么？

### 1.1 Codex CLI 的实际能力

Codex CLI 是一个本地运行的 AI Agent，它能做的事情：

| 能力 | 说明 |
|------|------|
| **读写文件** | 读取/创建/修改本地文件 |
| **执行 Shell 命令** | 运行任意命令行命令 |
| **调用 MCP Tools** | 通过 MCP 协议调用外部工具（这是关键扩展点） |
| **读取 Skills** | 根据 SKILL.md 获取任务专属知识和工作流 |
| **遵循 AGENTS.md** | 项目级指令，控制 Agent 行为 |
| **生成代码/脚本** | LLM 天然擅长根据上下文生成代码 |
| **自我纠错** | 执行失败后分析错误并重试 |

**Codex 不能直接做的事情：**
- 不能直接操作浏览器（除非通过 Playwright/Puppeteer MCP）
- 不能直接渲染图像（CLI 是纯文本界面）
- 不能直接解析/编辑 PSD 二进制文件（需要专业工具）

### 1.2 Claude Code 的实际能力

与 Codex 几乎相同，也支持：
- 读写文件、执行命令
- MCP Tools（通过 `.mcp.json` 配置）
- 项目指引（`CLAUDE.md`）
- 代码生成和自我纠错

### 1.3 关键洞察：MCP 是核心扩展点

Agent 本身是"大脑"，MCP Tools 是"手脚"。要让 Agent 操作 PSD，需要通过 MCP 给它提供合适的"手脚"。

---

## 二、开源生态调研：有什么可以直接用的？

### 2.1 Skills / Agent Skills 生态

| 资源 | Stars | 说明 |
|------|-------|------|
| [openai/skills](https://github.com/openai/skills) | 15.4k | OpenAI 官方 Skills 目录，含 `$skill-installer` |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 12.9k | 1030+ 社区 Skills，覆盖 Claude Code / Codex / Cursor |
| [VoltAgent/awesome-codex-subagents](https://github.com/VoltAgent/awesome-codex-subagents) | 2k | 136+ Codex 子 Agent 配置 |

**但是：目前没有任何开源的 PSD 操作 / Photopea 相关 Skill。** 这是一个空白领域，我们需要自己构建。

### 2.2 可利用的 MCP Server

| MCP Server | 用途 | 与本项目的关系 |
|------------|------|--------------|
| **Playwright MCP** (`@playwright/mcp`) | 浏览器自动化：打开页面、执行 JS、截图 | **高度相关** -- 可以用来控制 Photopea |
| **Puppeteer MCP** (`puppeteer-mcp-server`) | 浏览器自动化，420 stars | 同上，Playwright 版更官方 |
| **Chrome DevTools MCP** | Chrome 调试协议 | 可以用来在 Chrome 中执行 JS |
| **Context7** | 开发文档搜索 | 可以查 Photopea/PS 脚本文档 |
| **Figma MCP** | 操作 Figma | 不直接相关，但架构可参考 |

### 2.3 Photopea 的实际能力边界

Photopea 脚本 API 兼容 Adobe Photoshop JavaScript Reference，能做的事情：

```
✅ 基础操作（MVP 必须）
- 修改文字图层内容、字体、大小、颜色
- 图层显隐、不透明度、混合模式
- 图层移动、缩放、旋转
- 获取图层树结构
- 导出为 PSD/PNG/JPG/WebP

✅ 中级操作（Phase 2）
- 创建/删除图层
- 复制/粘贴图层
- 图层蒙版操作
- 色彩调整（亮度/对比度/色相饱和度）
- 选区操作
- 历史记录回退（撤销）

✅ 高级操作（Phase 3）
- 滤镜应用
- 智能对象操作
- 批量处理
- 自定义 Action 脚本
- 图层样式（投影、描边等）

❌ 不支持 / 受限
- 不能跑在无头模式（必须有浏览器渲染）
- 不能直接被 Node.js 进程调用（必须通过 iframe + postMessage）
- 某些操作比 Photoshop 慢（纯 JS 实现 vs 原生 C++）
- 大文件（>500MB）可能内存不足
```

---

## 三、你的想法的可行性分析

### 3.1 你的想法

> 构建一个 Codex 项目，里面放上各种 skills，以及调用子 agent、rules 等，然后给它各种操作的 scripts，然后进到目录，输入 codex，然后输入 PSD 文件，就可以自然语言操作 PSD。

### 3.2 这个想法的核心优势

1. **零前端开发**：不需要先做 Web UI，直接在终端对话
2. **利用成熟的 Agent 基础设施**：Codex/Claude Code 已经处理了 NL 理解、工具调用、纠错
3. **快速迭代**：改 SKILL.md / AGENTS.md 就能调整 Agent 行为，不需要改代码
4. **Skills 生态可复用**：可以装其他社区 Skills 增强能力

### 3.3 需要解决的问题

#### 问题 1："眼睛"在哪里？-- 视觉反馈断裂

```
最大的问题：Codex 是 CLI 工具，它看不到图片。

用户视角:
  Terminal (输入指令) ←→ 浏览器 (看效果)
  需要两个窗口来回切换

Agent 视角:
  只能通过文本了解状态（图层树 JSON）
  完全看不到渲染后的效果
  不知道"红色"到底好不好看
```

**缓解方案：**
- Agent 操作后主动 sync_layer_tree，通过文本确认操作是否成功
- 用 Playwright MCP 截图，Agent 能看到截图（如果模型支持 vision）
- MVP 阶段接受这个限制：用户负责"看"，Agent 负责"做"

#### 问题 2：Photopea 必须跑在浏览器里

PSD 的渲染和编辑都发生在 Photopea iframe 中，而 Photopea 不能无头运行。

```
codex (CLI) --MCP--> ??? --postMessage--> Photopea (Browser)
                     ↑
               这里需要一个桥
```

Agent 不能直接 postMessage 给 iframe，必须有一个中间层。

**三种桥接方案（下文详细对比）：**
- 方案 A: 自定义 MCP Bridge Server（v2 设计）
- 方案 B: Playwright MCP（零自定义代码）
- 方案 C: 混合方案

#### 问题 3：启动流程复杂

即使用最简方案，用户也需要：
1. 启动某种服务（Bridge 或浏览器）
2. 在浏览器中打开 Photopea 页面
3. 加载 PSD 文件
4. 然后才能开始自然语言对话

**缓解方案：** 写一个启动脚本，一键完成 1-3 步

#### 问题 4：PSD 文件如何"输入"？

用户说"输入我的 PSD 文件"，具体怎么做？

| 方式 | 实现难度 | 体验 |
|------|---------|------|
| 在浏览器中拖拽上传 | 低 | 需要手动操作 |
| Agent 读取本地文件，通过 Bridge 发送到浏览器 | 中 | 体验更流畅 |
| 启动脚本自动加载指定文件 | 中 | 最好的体验 |
| Codex 支持的文件路径参数 | 低 | `codex "打开 ./design.psd"` |

推荐：Agent 通过 MCP Tool 自动加载文件到 Photopea。用户只需在对话中说"打开 design.psd"。

---

## 四、三种桥接方案详细对比

### 方案 A: 自定义 MCP Bridge Server（v2 设计）

```
codex --STDIO MCP--> Bridge Server --WebSocket--> Browser --postMessage--> Photopea
```

**实现：**
- Node.js 进程，100~200 行代码
- 一侧是 MCP Server（STDIO），暴露 `execute_script` 等 Tools
- 另一侧是 WebSocket Server，连接浏览器页面
- 浏览器页面负责 postMessage 转发和结果收集

**优势：**
- 干净可靠，脚本执行结果精确回传
- Agent 能拿到结构化数据（图层树 JSON、执行成功/失败）
- 架构清晰，后续扩展为 Web 产品容易

**劣势：**
- 需要自己写 Bridge Server 代码
- 需要三个进程同时运行（Bridge + Web Server + Codex）
- 浏览器页面也需要自己写（虽然很简单）

**开发量：** 1-2 天

### 方案 B: Playwright MCP（零自定义代码）

```
codex --MCP--> Playwright MCP --> Browser --> Photopea
```

**实现：**
- 直接用 `@playwright/mcp`（npm 包，开箱即用）
- 不写任何桥接代码
- Agent 通过 Playwright 的 `evaluate()` 工具在页面上执行 JS
- Agent 通过 `screenshot()` 获取视觉反馈

**工作流：**
1. Agent 调用 `navigate("file:///path/to/photopea-host.html")` 打开本地 HTML
2. Agent 调用 `evaluate("document.getElementById('pp').contentWindow.postMessage(script, '*')")` 执行脚本
3. Agent 调用 `evaluate("window.__lastResult")` 获取结果（需要在 host 页面设置消息监听）
4. Agent 调用 `screenshot()` 查看当前效果

**优势：**
- **零自定义代码**（除了一个简单的 HTML host 页面）
- 直接装 MCP 就能用
- Agent 能看到截图（视觉反馈！）
- 不需要 WebSocket 服务

**劣势：**
- 脚本执行和结果获取不如方案 A 可靠（异步 postMessage 的时序问题）
- 截图传回 Agent 有延迟和 token 消耗
- evaluate() 在跨域 iframe 场景可能有限制
- Agent 需要用更复杂的 JS 包装来处理异步结果

**开发量：** 半天（只需一个 HTML 文件 + Codex 配置）

### 方案 C: 混合方案（推荐 MVP）

```
codex --MCP--> MCP Bridge (STDIO+WS) --> Browser --> Photopea
codex --MCP--> Playwright MCP ---------> Browser (screenshot)
```

**实现：**
- 自定义 Bridge 负责可靠的脚本执行和结果回传
- Playwright MCP 提供截图能力（可选）

**优势：**
- Bridge 保证操作可靠性
- Playwright 提供视觉反馈（Agent 能看到效果）
- 各取所长

**劣势：**
- 复杂度略高
- 两个 MCP Server 同时运行

### 选择建议

```
如果追求"最快看到效果":  方案 B（Playwright MCP）
  → 半天搭建，体验粗糙但能验证概念

如果追求"可靠的 MVP":    方案 A（自定义 Bridge）
  → 1-2 天搭建，操作可靠，后续演进路径清晰

如果追求"最佳体验":      方案 C（混合）
  → Bridge 保可靠性，Playwright 加视觉反馈
```

---

## 五、推荐的项目结构

### 5.1 目录结构

```
nl-psd-agent/
├── AGENTS.md                     # Codex 项目级指令（核心！）
├── CLAUDE.md                     # Claude Code 项目指引
├── README.md                     # 项目说明
│
├── .codex/
│   └── config.toml               # Codex MCP Server 配置
├── .mcp.json                     # Claude Code MCP 配置
│
├── bridge/                       # MCP Bridge Server（方案 A/C）
│   ├── server.js                 # 主入口 (~150 行)
│   ├── package.json
│   └── scripts/                  # 预定义的 Photopea 脚本
│       ├── extract-layers.js     # 图层树提取
│       ├── get-doc-info.js       # 文档信息
│       └── examples/             # 常见操作示例脚本
│           ├── change-text.js
│           ├── change-color.js
│           ├── toggle-layer.js
│           ├── move-layer.js
│           └── export.js
│
├── host/                         # Photopea 宿主页面
│   ├── index.html                # 极简 HTML：Photopea iframe + WS 客户端
│   └── adapter.js                # postMessage 封装 + WS 客户端
│
├── .agents/                      # Codex Skills 目录
│   └── skills/
│       └── psd-editor/
│           └── SKILL.md          # PSD 编辑核心 Skill
│
├── scripts/                      # 辅助脚本
│   ├── start.sh                  # 一键启动（Bridge + Host + 打开浏览器）
│   └── start.ps1                 # Windows 版启动脚本
│
├── references/                   # Agent 参考资料
│   ├── photopea-api-reference.md # Photopea 脚本 API 速查
│   └── common-operations.md      # 常见操作的脚本模板
│
└── plans/                        # 架构设计文档
    ├── v1-architecture.md
    ├── v2-architecture.md
    ├── v3-frontend-design.md
    └── v4-codex-implementation-discussion.md  # 本文档
```

### 5.2 核心文件内容设计

#### AGENTS.md（Codex 项目指引 -- 最重要的文件）

这个文件决定了 Agent 的"人格"和"能力认知"：

```markdown
# NL-PSD Agent

你是一个 PSD/PSB 文件编辑助手。用户通过自然语言描述修改需求，
你负责生成并执行 Photopea JavaScript 脚本来完成操作。

## 架构

- Photopea 运行在用户浏览器的 iframe 中
- 你通过 MCP Tool `execute_script` 发送脚本到 Photopea 执行
- 你通过 MCP Tool `sync_layer_tree` 获取当前文档的图层结构
- 你不能直接看到画面，但可以通过图层树 JSON 了解文档状态

## 工作流程

1. 用户说"打开 xxx.psd" → 你调用 `load_file` 加载文件
2. 调用 `sync_layer_tree` 了解图层结构
3. 用户描述修改需求 → 你分析需求，定位目标图层
4. 生成 Photopea JavaScript 脚本
5. 调用 `execute_script` 执行脚本
6. 如果失败，分析错误，修正脚本，重试（最多 3 次）
7. 成功后，调用 `sync_layer_tree` 确认结果
8. 用自然语言向用户报告完成情况

## 脚本编写规则

- 引用图层时优先用 `getByName("图层名")`，其次用索引
- 操作文字图层时通过 `textItem` 属性
- 颜色使用 `new SolidColor()` 创建
- 需要返回数据时用 `app.echoToOE(JSON.stringify(data))`
- 每段脚本保持简洁，一次只做一个操作

## 常见操作脚本模板

[此处嵌入 references/common-operations.md 的内容]

## 注意事项

- 操作前一定要先 sync_layer_tree，不要凭猜测操作
- 图层名是中文的很常见，要原样使用
- 图层组（LayerSet）和普通图层（ArtLayer）的 API 不同
- 修改文字内容后字体可能变化，注意保持原字体
- 大的修改分多步执行，每步确认后再继续
```

#### SKILL.md（PSD 编辑 Skill）

```markdown
---
name: psd-editor
description: |
  自然语言编辑 PSD/PSB 文件。当用户想要打开、修改、导出 PSD 文件时使用。
  通过 MCP Bridge 连接浏览器中的 Photopea 编辑器执行操作。
---

## 前置条件

确保 MCP Bridge Server 已启动。如果用户说"开始"或"打开 PSD"，
先检查 Bridge 连接状态（调用 get_document_info，如果报错说明未连接）。

## 工作流

1. 调用 `sync_layer_tree` 获取文档结构
2. 分析用户的自然语言指令
3. 确定目标图层（通过名称匹配）
4. 生成 Photopea JavaScript 脚本
5. 调用 `execute_script` 执行
6. 处理结果（成功 → 报告 / 失败 → 修正重试）

## Photopea API 速查

### 访问图层
- `app.activeDocument.layers` -- 所有顶层图层
- `app.activeDocument.artLayers` -- 所有普通图层（不含组）
- `app.activeDocument.layerSets` -- 所有图层组
- `layer.layers` / `layer.artLayers` -- 组内的图层
- `layers.getByName("名称")` -- 按名称查找

### 文字操作
- `artLayer.textItem.contents = "新文字"` -- 修改内容
- `artLayer.textItem.size = new UnitValue(24, "px")` -- 字号
- `artLayer.textItem.color = solidColor` -- 颜色
- `artLayer.textItem.font` -- 字体名

### 颜色
var c = new SolidColor();
c.rgb.red = 255; c.rgb.green = 0; c.rgb.blue = 0;

### 图层属性
- `layer.visible = true/false`
- `layer.opacity = 80` (0-100)
- `layer.translate(deltaX, deltaY)`
- `layer.resize(scaleX, scaleY, AnchorPosition.MIDDLECENTER)`
- `layer.rotate(angle, AnchorPosition.MIDDLECENTER)`

### 文档操作
- `app.activeDocument.saveToOE("png")` -- 导出
- `app.activeDocument.resizeImage(width, height)`
- `app.activeDocument.resizeCanvas(width, height)`

### 数据回传
- `app.echoToOE(JSON.stringify(data))` -- 发送字符串到外部
- `app.activeDocument.saveToOE("png")` -- 发送图片到外部
```

### 5.3 MCP 配置

#### .codex/config.toml

```toml
[mcp_servers.psd_bridge]
command = "node"
args = ["./bridge/server.js"]
startup_timeout_sec = 15
tool_timeout_sec = 30

# 可选：加上 Playwright 用于截图
# [mcp_servers.playwright]
# command = "npx"
# args = ["-y", "@playwright/mcp"]
```

#### .mcp.json（Claude Code）

```json
{
  "mcpServers": {
    "psd_bridge": {
      "command": "node",
      "args": ["./bridge/server.js"]
    }
  }
}
```

---

## 六、实际使用体验预览

### 6.1 启动流程

```powershell
# 终端 1：启动服务
cd nl-psd-agent
.\scripts\start.ps1
# → 自动启动 Bridge Server (localhost:9900)
# → 自动打开浏览器，加载 Photopea Host 页面
# → 浏览器自动连接 WebSocket

# 终端 2：启动 Agent
cd nl-psd-agent
codex
```

### 6.2 对话示例

```
You: 打开 D:\designs\banner.psd

Agent: 正在加载文件... 
       ✓ 文件已加载。文档信息：
       - 名称: banner.psd
       - 尺寸: 1920 × 1080 px
       - 图层数: 15
       
       图层结构：
       ├── [组] Header
       │   ├── Logo (普通图层)
       │   ├── Title (文字: "Summer Sale")
       │   └── Subtitle (文字: "Up to 50% off")
       ├── [组] Body
       │   ├── Product Image (智能对象)
       │   └── Price (文字: "$99.99")
       └── Background (普通图层)
       
       请告诉我你想做什么修改。

You: 把 Title 改成"秋季特惠"，颜色改成金色

Agent: 正在执行修改...

       执行脚本 1/2: 修改文字内容
       var layer = app.activeDocument.layerSets.getByName("Header")
                      .artLayers.getByName("Title");
       layer.textItem.contents = "秋季特惠";
       ✓ 成功

       执行脚本 2/2: 修改文字颜色
       var layer = app.activeDocument.layerSets.getByName("Header")
                      .artLayers.getByName("Title");
       var color = new SolidColor();
       color.rgb.red = 255; color.rgb.green = 193; color.rgb.blue = 37;
       layer.textItem.color = color;
       ✓ 成功

       已将标题改为"秋季特惠"，颜色设为金色 (#FFC125)。
       请在浏览器中查看效果。

You: 把 Subtitle 隐藏掉

Agent: var layer = app.activeDocument.layerSets.getByName("Header")
              .artLayers.getByName("Subtitle");
       layer.visible = false;
       ✓ 已隐藏 Subtitle 图层。

You: 导出为 PNG

Agent: 正在导出...
       ✓ 已导出 banner.png（1920×1080, ~2.1MB）
       文件已保存到浏览器下载目录。
```

---

## 七、潜在问题与风险

### 7.1 脚本生成准确性

**问题：** LLM 生成的 Photopea 脚本可能有错误（语法错、图层名不对、API 用法不对）。

**缓解：**
- AGENTS.md / SKILL.md 中提供丰富的 few-shot 示例
- `references/` 目录放完整的 API 参考
- 错误自动重试机制（Bridge 返回错误信息，Agent 修正后重试）
- 渐进式增加操作复杂度（先只支持基础操作）

**量化预期：**
- 改文字/改颜色/显隐图层：成功率 > 90%
- 移动/缩放/旋转：成功率 > 80%
- 复杂操作（滤镜/蒙版/样式）：成功率 50-70%，需要更多 few-shot

### 7.2 图层名匹配

**问题：** 用户说"标题"，但图层名可能是 "Title"、"标题文字"、"Header-Text" 等各种名称。

**缓解：**
- Agent 先 sync_layer_tree 拿到完整图层树
- 在 AGENTS.md 中指导 Agent 用模糊匹配逻辑
- Agent 不确定时主动询问用户

### 7.3 Windows 兼容性

**问题：** Codex CLI 在 Windows 上是实验性支持。

**缓解：**
- Claude Code 在 Windows 上也可用（通过 WSL 或原生）
- Bridge Server 是纯 Node.js，跨平台无问题
- 启动脚本提供 .sh 和 .ps1 两个版本

### 7.4 Token 消耗

**问题：** 图层树 JSON 可能很大（复杂 PSD 几百个图层），占用大量 context window。

**缓解：**
- MVP 阶段传完整图层树（对中小 PSD 够用）
- 后续优化：只传顶层结构，需要深入时再展开特定组
- 后续优化：只传与当前操作相关的图层信息

---

## 八、推荐的实施路径

### Phase 0: 概念验证（半天 - 1 天）

**目标：** 验证 "Codex -> Photopea 脚本执行" 这条链路是否通畅

**做法：**
1. 创建一个极简的 HTML 页面，嵌入 Photopea iframe
2. 手动在浏览器 DevTools 里通过 postMessage 执行几个脚本
3. 验证图层树提取、文字修改、颜色修改等基础操作

**不需要 Agent，不需要 Bridge，纯手动验证 Photopea 脚本 API。**

### Phase 1: 最小可用 Agent（1-2 天）

**目标：** 跑通完整链路 -- 在 Codex 中输入自然语言，Photopea 中看到效果

**做法：**
1. 实现 MCP Bridge Server（~150 行 Node.js）
2. 实现 Host 页面（~100 行 HTML+JS）
3. 编写 AGENTS.md + SKILL.md
4. 配置 .codex/config.toml
5. 编写启动脚本
6. 端到端测试

**支持的操作范围：** 修改文字、改颜色、显隐图层、获取图层信息

### Phase 2: 增强 Agent 能力（1 周）

**做法：**
- 扩充 SKILL.md 中的脚本示例库
- 添加更多操作支持（移动/缩放/旋转/导出）
- 优化错误处理和重试逻辑
- 添加 Playwright MCP 截图能力（可选）
- 添加文件自动加载功能

### Phase 3: Web UI 整合

**做法：**
- 用 v3 的前端设计，构建 Chat UI + Photopea 的整合界面
- Chat 消息直接通过 Bridge 传递
- 这一步将"CLI 体验"升级为"Web 产品体验"

---

## 九、核心结论

### 你的想法完全可行

"构建 Codex 项目 + Skills + MCP Tools → 自然语言操作 PSD" 这个思路是正确的。
核心挑战不在 Agent 端（Codex/Claude Code 已经很强了），而在 **Bridge 层**
—— 如何可靠地把 Agent 的意图传递给 Photopea 并回收结果。

### 最快落地路径

```
Day 0: 手动验证 Photopea 脚本 API（半天）
Day 1: 实现 MCP Bridge + Host 页面（1 天）
Day 2: 编写 AGENTS.md + SKILL.md + 端到端测试（1 天）
       → 此时已经可以在 Codex 中用自然语言操作 PSD 了
```

### 最大的加速器

- **AGENTS.md 的质量** 决定了 Agent 的脚本生成准确性
- **few-shot 示例** 越丰富，Agent 越准确
- **MCP Bridge 的可靠性** 决定了操作是否能稳定执行

### 最大的风险

- Photopea 脚本 API 的某些操作可能不如预期（需要实测）
- LLM 对不常见操作的脚本生成可能不准（需要持续优化 prompt）
- Windows 上 Codex 的兼容性（备选 Claude Code）
